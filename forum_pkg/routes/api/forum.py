from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from forum_pkg import db, allowed_file, upload_to_cloudinary
from forum_pkg.models import (
    User, Post, Comment, Like, Favorite, Follow,
    Notification, add_notification
)
import markdown as md

forum_bp = Blueprint('api_forum', __name__)


def post_to_dict(p):
    return {
        'id': p.id,
        'user_id': p.user_id,
        'title': p.title,
        'content': p.content,
        'category': p.category,
        'views': p.views,
        'created_at': p.created_at.isoformat(),
        'author': {
            'id': p.author.id,
            'username': p.author.username,
            'nickname': p.author.nickname,
            'avatar_url': p.author.avatar_url,
        } if p.author else None,
        'comment_count': p.comment_count,
        'like_count': p.like_count,
        'favorite_count': p.favorite_count,
        'content_plain': p.content_plain,
    }


def comment_to_dict(c):
    return {
        'id': c.id,
        'post_id': c.post_id,
        'user_id': c.user_id,
        'parent_id': c.parent_id,
        'content': c.content,
        'created_at': c.created_at.isoformat(),
        'author': {
            'id': c.author.id,
            'nickname': c.author.nickname,
            'avatar_url': c.author.avatar_url,
        } if c.author else None,
        'replies': [comment_to_dict(r) for r in c.replies] if c.replies else [],
    }


def user_to_dict(u):
    return {
        'id': u.id,
        'username': u.username,
        'nickname': u.nickname,
        'avatar_url': u.avatar_url,
        'is_admin': u.is_admin,
        'is_banned': u.is_banned,
        'created_at': u.created_at.isoformat(),
        'like_count': u.like_count,
        'following_count': u.following_count,
        'follower_count': u.follower_count,
    }


# ==================== Forum Home ====================

@forum_bp.route('/forum', methods=['GET'])
@jwt_required()
def api_forum():
    category = request.args.get('category', 'all')
    page = int(request.args.get('page', 1))
    per_page = 20

    q = Post.query.order_by(Post.created_at.desc())
    if category != 'all':
        q = q.filter(Post.category == category)

    total = q.count()
    posts = q.offset((page - 1) * per_page).limit(per_page).all()

    all_posts = Post.query.all()
    hot_posts = sorted(all_posts,
                       key=lambda p: p.views + p.like_count * 2 + p.comment_count * 3,
                       reverse=True)[:5]

    today_start = datetime.combine(date.today(), datetime.min.time())
    stats = {
        'total_posts': Post.query.count(),
        'total_users': User.query.count(),
        'today_posts': Post.query.filter(Post.created_at >= today_start).count(),
    }

    return jsonify({
        'posts': [post_to_dict(p) for p in posts],
        'hot_posts': [post_to_dict(p) for p in hot_posts],
        'stats': stats,
        'total': total,
        'page': page,
        'per_page': per_page,
    }), 200


# ==================== Post CRUD ====================

@forum_bp.route('/posts', methods=['POST'])
@jwt_required()
def api_create_post():
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    category = data.get('category', '')

    if not title or not content or not category:
        return jsonify({'message': '所有字段都必须填写'}), 400

    post = Post(user_id=current_user.id, title=title, content=content, category=category)
    db.session.add(post)
    db.session.commit()

    followers = Follow.query.filter_by(followed_id=current_user.id).all()
    from flask import url_for
    for f in followers:
        add_notification(f.follower_id, current_user.id, 'follow_post',
                         url_for('post_detail', post_id=post.id),
                         f"{current_user.nickname} 发布了新帖子《{title}》")

    return jsonify(post_to_dict(post)), 201


@forum_bp.route('/posts/<int:post_id>', methods=['GET'])
@jwt_required()
def api_post_detail(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({'message': '帖子不存在'}), 404

    post.views += 1
    db.session.commit()

    user_liked = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first() is not None
    user_favorited = Favorite.query.filter_by(user_id=current_user.id, post_id=post_id).first() is not None

    content_html = md.markdown(post.content, extensions=['fenced_code', 'tables', 'nl2br'])

    root_comments = Comment.query.filter_by(post_id=post_id, parent_id=None) \
        .order_by(Comment.created_at.asc()).all()

    return jsonify({
        'post': post_to_dict(post),
        'content_html': content_html,
        'user_liked': user_liked,
        'user_favorited': user_favorited,
        'comments': [comment_to_dict(c) for c in root_comments],
    }), 200


@forum_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def api_delete_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({'message': '帖子不存在'}), 404
    if post.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'message': '只能删除自己的帖子'}), 403

    Comment.query.filter_by(post_id=post_id).delete()
    Like.query.filter_by(post_id=post_id).delete()
    Favorite.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()

    return jsonify({'message': '帖子已删除'}), 200


# ==================== Comments ====================

@forum_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def api_add_comment(post_id):
    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    parent_id = data.get('parent_id')

    if not content:
        return jsonify({'message': '评论内容不能为空'}), 400

    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({'message': '帖子不存在'}), 404

    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        content=content,
        parent_id=int(parent_id) if parent_id else None
    )
    db.session.add(comment)
    db.session.commit()

    from flask import url_for
    if parent_id:
        parent_comment = db.session.get(Comment, int(parent_id))
        if parent_comment and parent_comment.user_id != current_user.id:
            link = url_for('post_detail', post_id=post_id) + '#comment-' + str(parent_comment.id)
            add_notification(parent_comment.user_id, current_user.id, 'reply',
                             link, f"{current_user.nickname} 回复了你的评论")
    elif post.user_id != current_user.id:
        link = url_for('post_detail', post_id=post_id) + '#comments'
        add_notification(post.user_id, current_user.id, 'comment',
                         link, f"{current_user.nickname} 评论了你的帖子《{post.title}》")

    return jsonify(comment_to_dict(comment)), 201


@forum_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def api_delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return jsonify({'message': '评论不存在'}), 404
    if comment.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'message': '只能删除自己的评论'}), 403

    post_id = comment.post_id

    def delete_replies(parent_id):
        replies = Comment.query.filter_by(parent_id=parent_id).all()
        for reply in replies:
            delete_replies(reply.id)
            db.session.delete(reply)

    delete_replies(comment.id)
    db.session.delete(comment)
    db.session.commit()

    return jsonify({'message': '评论已删除'}), 200


# ==================== Likes & Favorites ====================

@forum_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
def api_toggle_like(post_id):
    existing = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post_id))
        liked = True
    db.session.commit()

    post = db.session.get(Post, post_id)
    return jsonify({'liked': liked, 'like_count': post.like_count if post else 0}), 200


@forum_bp.route('/posts/<int:post_id>/favorite', methods=['POST'])
@jwt_required()
def api_toggle_favorite(post_id):
    existing = Favorite.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing:
        db.session.delete(existing)
        favorited = False
    else:
        db.session.add(Favorite(user_id=current_user.id, post_id=post_id))
        favorited = True
    db.session.commit()

    post = db.session.get(Post, post_id)
    return jsonify({'favorited': favorited, 'favorite_count': post.favorite_count if post else 0}), 200


# ==================== Upload ====================

@forum_bp.route('/upload', methods=['POST'])
@jwt_required()
def api_upload():
    if 'image' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': '不支持的图片格式'}), 400
    try:
        url = upload_to_cloudinary(file)
        return jsonify({'url': url}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Search ====================

@forum_bp.route('/search', methods=['GET'])
@jwt_required()
def api_search():
    q = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'post')
    category = request.args.get('category', 'all')
    time_filter = request.args.get('time', 'all')

    result = {'posts': [], 'users': []}

    if search_type == 'user' and q:
        users = User.query.filter(User.nickname.contains(q), User.is_banned == False).all()
        result['users'] = [user_to_dict(u) for u in users]
    elif q:
        query = Post.query
        if category != 'all':
            query = query.filter(Post.category == category)
        now = datetime.utcnow()
        if time_filter == 'day':
            query = query.filter(Post.created_at >= now - timedelta(days=1))
        elif time_filter == 'half_month':
            query = query.filter(Post.created_at >= now - timedelta(days=15))
        elif time_filter == 'month':
            query = query.filter(Post.created_at >= now - timedelta(days=30))
        elif time_filter == 'half_year':
            query = query.filter(Post.created_at >= now - timedelta(days=180))

        posts = query.filter(
            (Post.title.contains(q)) | (Post.content.contains(q))
        ).order_by(Post.created_at.desc()).all()
        result['posts'] = [post_to_dict(p) for p in posts]

    return jsonify(result), 200
