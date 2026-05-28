from datetime import datetime, date, timedelta
from flask import render_template, request, redirect, url_for, flash, session
import markdown as md
from forum_pkg import db, allowed_file, upload_to_cloudinary
from forum_pkg.models import (
    User, Post, Comment, Like, Favorite, Follow, Notification,
    add_notification
)


def register_forum_routes(app):

    @app.route('/upload_image', methods=['POST'])
    def upload_image():
        if 'user_id' not in session:
            return {'error': '请先登录'}, 401
        if 'image' not in request.files:
            return {'error': '没有文件'}, 400
        file = request.files['image']
        if file.filename == '' or not allowed_file(file.filename):
            return {'error': '不支持的图片格式'}, 400
        url = upload_to_cloudinary(file)
        return {'url': url}, 200

    @app.route('/forum')
    def forum():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        category = request.args.get('category', 'all')

        if category == 'all':
            posts = Post.query.order_by(Post.created_at.desc()).all()
        else:
            posts = Post.query.filter_by(category=category).order_by(Post.created_at.desc()).all()

        all_posts = Post.query.all()
        hot_posts = sorted(all_posts, key=lambda p: p.views + p.like_count * 2 + p.comment_count * 3, reverse=True)[:5]

        today_start = datetime.combine(date.today(), datetime.min.time())
        stats = {
            'total_posts': Post.query.count(),
            'total_users': User.query.count(),
            'today_posts': Post.query.filter(Post.created_at >= today_start).count(),
        }

        return render_template('forum.html',
                               posts=posts,
                               hot_posts=hot_posts,
                               stats=stats,
                               current_category=category)

    @app.route('/create_post', methods=['GET', 'POST'])
    def create_post():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            category = request.form.get('category', '')

            if not title or not content or not category:
                flash('所有字段都必须填写', 'error')
                return render_template('create_post.html')

            post = Post(
                user_id=session['user_id'],
                title=title,
                content=content,
                category=category
            )
            db.session.add(post)
            db.session.commit()

            followers = Follow.query.filter_by(followed_id=session['user_id']).all()
            for f in followers:
                add_notification(f.follower_id, session['user_id'], 'follow_post',
                               url_for('post_detail', post_id=post.id),
                               f"{session.get('nickname','')} 发布了新帖子《{title}》")

            flash('帖子发布成功！', 'success')
            return redirect(url_for('forum'))

        return render_template('create_post.html')

    @app.route('/post/<int:post_id>')
    def post_detail(post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        post = db.session.get(Post, post_id)
        if not post:
            return redirect(url_for('forum'))

        post.views += 1
        db.session.commit()

        user_liked = Like.query.filter_by(user_id=session['user_id'], post_id=post_id).first() is not None
        user_favorited = Favorite.query.filter_by(user_id=session['user_id'], post_id=post_id).first() is not None

        post_content_html = md.markdown(post.content, extensions=['fenced_code', 'tables', 'nl2br'])

        root_comments = Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(Comment.created_at.asc()).all()

        return render_template('post_detail.html',
                               post=post,
                               post_content_html=post_content_html,
                               root_comments=root_comments,
                               user_liked=user_liked,
                               user_favorited=user_favorited)

    @app.route('/post/<int:post_id>/comment', methods=['POST'])
    def add_comment(post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        content = request.form.get('content', '').strip()
        parent_id = request.form.get('parent_id', '')

        if content:
            comment = Comment(
                post_id=post_id,
                user_id=session['user_id'],
                content=content,
                parent_id=int(parent_id) if parent_id else None
            )
            db.session.add(comment)
            db.session.commit()

            post = db.session.get(Post, post_id)
            if parent_id:
                parent_comment = db.session.get(Comment, int(parent_id))
                if parent_comment and parent_comment.user_id != session['user_id']:
                    link = url_for('post_detail', post_id=post_id) + '#comment-' + str(parent_comment.id)
                    add_notification(parent_comment.user_id, session['user_id'], 'reply',
                                   link,
                                   f"{session.get('nickname','')} 回复了你的评论")
            elif post and post.user_id != session['user_id']:
                link = url_for('post_detail', post_id=post_id) + '#comments'
                add_notification(post.user_id, session['user_id'], 'comment',
                               link,
                               f"{session.get('nickname','')} 评论了你的帖子《{post.title}》")

            flash('评论成功', 'success')

        return redirect(url_for('post_detail', post_id=post_id))

    @app.route('/post/<int:post_id>/like')
    def toggle_like(post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        existing = Like.query.filter_by(user_id=session['user_id'], post_id=post_id).first()
        if existing:
            db.session.delete(existing)
        else:
            like = Like(user_id=session['user_id'], post_id=post_id)
            db.session.add(like)
        db.session.commit()

        return redirect(url_for('post_detail', post_id=post_id))

    @app.route('/post/<int:post_id>/favorite')
    def toggle_favorite(post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        existing = Favorite.query.filter_by(user_id=session['user_id'], post_id=post_id).first()
        if existing:
            db.session.delete(existing)
        else:
            fav = Favorite(user_id=session['user_id'], post_id=post_id)
            db.session.add(fav)
        db.session.commit()

        return redirect(url_for('post_detail', post_id=post_id))

    @app.route('/post/<int:post_id>/delete')
    def delete_post(post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        post = db.session.get(Post, post_id)
        if not post:
            return redirect(url_for('forum'))
        if post.user_id != session['user_id'] and not session.get('is_admin'):
            flash('只能删除自己的帖子', 'error')
            return redirect(url_for('post_detail', post_id=post_id))

        Comment.query.filter_by(post_id=post_id).delete()
        Like.query.filter_by(post_id=post_id).delete()
        Favorite.query.filter_by(post_id=post_id).delete()
        db.session.delete(post)
        db.session.commit()

        flash('帖子已删除', 'info')
        return redirect(url_for('forum'))

    @app.route('/comment/<int:comment_id>/delete')
    def delete_comment(comment_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        comment = db.session.get(Comment, comment_id)
        if not comment:
            return redirect(url_for('forum'))
        if comment.user_id != session['user_id'] and not session.get('is_admin'):
            flash('只能删除自己的评论', 'error')
            return redirect(url_for('post_detail', post_id=comment.post_id))

        post_id = comment.post_id

        def delete_replies(parent_id):
            replies = Comment.query.filter_by(parent_id=parent_id).all()
            for reply in replies:
                delete_replies(reply.id)
                db.session.delete(reply)

        delete_replies(comment.id)
        db.session.delete(comment)
        db.session.commit()

        flash('评论已删除', 'info')
        return redirect(url_for('post_detail', post_id=post_id))

    @app.route('/search')
    def search():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        q = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'post')
        category = request.args.get('category', 'all')
        time_filter = request.args.get('time', 'all')

        posts = []
        users = []
        current_time = datetime.utcnow()

        if search_type == 'user' and q:
            users = User.query.filter(
                User.nickname.contains(q),
                User.is_banned == False
            ).all()

        elif q:
            query = Post.query

            if category != 'all':
                query = query.filter(Post.category == category)

            if time_filter == 'day':
                cutoff = current_time - timedelta(days=1)
                query = query.filter(Post.created_at >= cutoff)
            elif time_filter == 'half_month':
                cutoff = current_time - timedelta(days=15)
                query = query.filter(Post.created_at >= cutoff)
            elif time_filter == 'month':
                cutoff = current_time - timedelta(days=30)
                query = query.filter(Post.created_at >= cutoff)
            elif time_filter == 'half_year':
                cutoff = current_time - timedelta(days=180)
                query = query.filter(Post.created_at >= cutoff)

            posts = query.filter(
                (Post.title.contains(q)) | (Post.content.contains(q))
            ).order_by(Post.created_at.desc()).all()

        return render_template('search.html',
                               query=q,
                               search_type=search_type,
                               current_category=category,
                               current_time=time_filter,
                               posts=posts,
                               users=users)
