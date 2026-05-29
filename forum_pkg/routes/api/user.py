from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from forum_pkg import db, allowed_file, upload_to_cloudinary
from forum_pkg.models import (
    User, Post, Comment, Favorite, Follow, Friend,
    Message, Notification, PrivacySetting, get_privacy, add_notification
)

user_bp = Blueprint('api_user', __name__)


def post_card(p):
    return {
        'id': p.id,
        'title': p.title,
        'category': p.category,
        'views': p.views,
        'created_at': p.created_at.isoformat(),
        'author': {'id': p.author.id, 'nickname': p.author.nickname, 'avatar_url': p.author.avatar_url},
        'like_count': p.like_count,
        'comment_count': p.comment_count,
        'content_plain': p.content_plain,
    }


def user_brief(u):
    return {
        'id': u.id,
        'nickname': u.nickname,
        'avatar_url': u.avatar_url,
        'username': u.username,
        'created_at': u.created_at.isoformat(),
    }


# ==================== Profile ====================

@user_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def api_my_profile():
    user = current_user
    ps = get_privacy(user.id)

    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    favs = Favorite.query.filter_by(user_id=user.id).order_by(Favorite.id.desc()).all()
    favorited_posts = [db.session.get(Post, fav.post_id) for fav in favs if db.session.get(Post, fav.post_id)]

    short_contacts = set()
    for m in Message.query.filter_by(sender_id=user.id, chat_type='short').all():
        short_contacts.add(m.receiver)
    for m in Message.query.filter_by(receiver_id=user.id, chat_type='short').all():
        short_contacts.add(m.sender)
    short_contacts.discard(user)

    friends = Friend.query.filter(
        ((Friend.user_id == user.id) | (Friend.friend_id == user.id)),
        Friend.status == 'accepted'
    ).all()
    friend_users = []
    friend_ids = set()
    for f in friends:
        fu = f.friend if f.user_id == user.id else f.user
        friend_users.append(fu)
        friend_ids.add(fu.id)

    short_contacts = {c for c in short_contacts if c.id not in friend_ids}

    pending_requests = Friend.query.filter_by(friend_id=user.id, status='pending').all()
    my_sent_requests = Friend.query.filter_by(user_id=user.id, status='pending').all()

    following = []
    for f in Follow.query.filter_by(follower_id=user.id).all():
        fu = db.session.get(User, f.followed_id)
        if fu:
            following.append(fu)

    followers = []
    for f in Follow.query.filter_by(followed_id=user.id).all():
        fu = db.session.get(User, f.follower_id)
        if fu:
            followers.append(fu)

    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'avatar_url': user.avatar_url,
            'is_admin': user.is_admin,
            'like_count': user.like_count,
            'following_count': user.following_count,
            'follower_count': user.follower_count,
        },
        'privacy': {
            'show_posts': ps.show_posts,
            'show_favorites': ps.show_favorites,
            'show_following': ps.show_following,
            'allow_short_chat': ps.allow_short_chat,
            'allow_friend_request': ps.allow_friend_request,
        },
        'posts': [post_card(p) for p in posts],
        'favorited_posts': [post_card(p) for p in favorited_posts],
        'short_contacts': [user_brief(c) for c in short_contacts],
        'friend_users': [user_brief(f) for f in friend_users],
        'pending_requests': [{'id': r.id, 'user': user_brief(r.user)} for r in pending_requests],
        'my_sent_requests': [{'id': r.id, 'user': user_brief(r.friend)} for r in my_sent_requests],
        'following': [user_brief(f) for f in following],
        'followers': [user_brief(f) for f in followers],
    }), 200


@user_bp.route('/user/profile', methods=['PUT'])
@jwt_required()
def api_update_profile():
    user = current_user
    data = request.get_json(silent=True) or {}

    if 'nickname' in data:
        nickname = data['nickname'].strip()
        if nickname:
            user.nickname = nickname

    priv_keys = ['show_posts', 'show_favorites', 'show_following', 'allow_short_chat', 'allow_friend_request']
    if any(k in data for k in priv_keys):
        ps = get_privacy(user.id)
        for k in priv_keys:
            if k in data:
                setattr(ps, k, bool(data[k]))

    db.session.commit()

    return jsonify({'message': '更新成功', 'nickname': user.nickname}), 200


# ==================== Avatar Upload ====================

@user_bp.route('/user/avatar', methods=['POST'])
@jwt_required()
def api_upload_avatar():
    file = request.files.get('avatar')
    if not file or not file.filename or not allowed_file(file.filename):
        return jsonify({'message': '请选择有效的图片文件'}), 400
    try:
        url = upload_to_cloudinary(file)
        current_user.avatar = url
        db.session.commit()
        return jsonify({'avatar_url': url, 'message': '头像上传成功'}), 200
    except Exception as e:
        return jsonify({'message': f'头像上传失败: {str(e)}'}), 500


# ==================== Other User Profile ====================

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def api_user_profile(user_id):
    my_id = current_user.id
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({'message': '用户不存在'}), 404

    if my_id == user_id:
        return jsonify({'message': '请使用 /api/user/profile'}), 400

    ps = get_privacy(user_id)

    is_friend = Friend.query.filter(
        ((Friend.user_id == my_id) & (Friend.friend_id == user_id)) |
        ((Friend.user_id == user_id) & (Friend.friend_id == my_id)),
        Friend.status == 'accepted'
    ).first() is not None

    pending_req = Friend.query.filter(
        ((Friend.user_id == my_id) & (Friend.friend_id == user_id)) |
        ((Friend.user_id == user_id) & (Friend.friend_id == my_id)),
        Friend.status == 'pending'
    ).first()

    friend_status = 'friend' if is_friend else ('pending' if pending_req else 'none')

    posts = []
    if ps.show_posts:
        posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).limit(30).all()

    favorited_posts = []
    if ps.show_favorites:
        favs = Favorite.query.filter_by(user_id=user_id).order_by(Favorite.id.desc()).limit(30).all()
        favorited_posts = [db.session.get(Post, fav.post_id) for fav in favs if db.session.get(Post, fav.post_id)]

    is_following = Follow.query.filter_by(follower_id=my_id, followed_id=user_id).first() is not None

    following_users = []
    if ps.show_following:
        for f in Follow.query.filter_by(follower_id=user_id).all():
            fu = db.session.get(User, f.followed_id)
            if fu:
                following_users.append(fu)

    return jsonify({
        'user': {
            'id': target.id,
            'nickname': target.nickname,
            'avatar_url': target.avatar_url,
            'created_at': target.created_at.isoformat(),
            'like_count': target.like_count,
        },
        'is_following': is_following,
        'following_count': target.following_count,
        'follower_count': target.follower_count,
        'friend_status': friend_status,
        'privacy': {
            'show_posts': ps.show_posts,
            'show_favorites': ps.show_favorites,
            'show_following': ps.show_following,
            'allow_short_chat': ps.allow_short_chat,
            'allow_friend_request': ps.allow_friend_request,
        },
        'posts': [post_card(p) for p in posts],
        'favorited_posts': [post_card(p) for p in favorited_posts],
        'following': [user_brief(f) for f in following_users],
    }), 200


# ==================== Follow ====================

@user_bp.route('/users/<int:user_id>/follow', methods=['POST'])
@jwt_required()
def api_follow(user_id):
    if current_user.id == user_id:
        return jsonify({'message': '不能关注自己'}), 400
    existing = Follow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first()
    if not existing:
        db.session.add(Follow(follower_id=current_user.id, followed_id=user_id))
        db.session.commit()
        return jsonify({'following': True}), 200
    return jsonify({'following': True}), 200


@user_bp.route('/users/<int:user_id>/follow', methods=['DELETE'])
@jwt_required()
def api_unfollow(user_id):
    Follow.query.filter_by(follower_id=current_user.id, followed_id=user_id).delete()
    db.session.commit()
    return jsonify({'following': False}), 200


# ==================== Friends ====================

@user_bp.route('/friends/<int:friend_id>', methods=['POST'])
@jwt_required()
def api_add_friend(friend_id):
    my_id = current_user.id
    if my_id == friend_id:
        return jsonify({'message': '不能添加自己为好友'}), 400

    existing = Friend.query.filter(
        ((Friend.user_id == my_id) & (Friend.friend_id == friend_id)) |
        ((Friend.user_id == friend_id) & (Friend.friend_id == my_id))
    ).first()

    if existing:
        if existing.status == 'pending':
            return jsonify({'message': '已发送过好友请求'}), 409
        elif existing.status == 'accepted':
            return jsonify({'message': '你们已经是好友了'}), 409

    friend_req = Friend(user_id=my_id, friend_id=friend_id)
    db.session.add(friend_req)
    db.session.commit()

    from flask import url_for
    add_notification(friend_id, my_id, 'friend_request',
                     url_for('profile', tab='friends'),
                     f"{current_user.nickname} 请求添加你为好友")

    return jsonify({'message': '好友请求已发送'}), 201


@user_bp.route('/friends/requests/<int:req_id>', methods=['PUT'])
@jwt_required()
def api_handle_friend(req_id):
    data = request.get_json(silent=True) or {}
    action = data.get('action', '')

    friend_req = db.session.get(Friend, req_id)
    if not friend_req or friend_req.friend_id != current_user.id:
        return jsonify({'message': '无权操作'}), 403

    from flask import url_for
    if action == 'accept':
        friend_req.status = 'accepted'
        add_notification(friend_req.user_id, current_user.id, 'friend_accept',
                         url_for('profile', tab='friends'),
                         f"{current_user.nickname} 已同意你的好友请求")
        db.session.commit()
        return jsonify({'message': '已同意好友请求'}), 200
    elif action == 'reject':
        friend_req.status = 'rejected'
        add_notification(friend_req.user_id, current_user.id, 'friend_reject',
                         url_for('profile'),
                         f"{current_user.nickname} 拒绝了你的好友请求")
        db.session.commit()
        return jsonify({'message': '已拒绝好友请求'}), 200

    return jsonify({'message': '无效操作'}), 400


# ==================== Notifications ====================

@user_bp.route('/notifications', methods=['GET'])
@jwt_required()
def api_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.created_at.desc()).all()
    result = [{
        'id': n.id,
        'type': n.type,
        'content': n.content,
        'link': n.link,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat(),
        'from_user': user_brief(n.from_user) if n.from_user else None,
    } for n in notifs]
    return jsonify(result), 200


@user_bp.route('/notifications/read-all', methods=['POST'])
@jwt_required()
def api_notification_read_all():
    Notification.query.filter_by(user_id=current_user.id, is_read=False) \
        .update({'is_read': True})
    db.session.commit()
    return jsonify({'message': '已全部标为已读'}), 200


@user_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@jwt_required()
def api_notification_read(notif_id):
    n = db.session.get(Notification, notif_id)
    if n and n.user_id == current_user.id:
        n.is_read = True
        db.session.commit()
    return jsonify({'message': 'ok'}), 200
