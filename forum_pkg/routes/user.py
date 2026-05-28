from flask import render_template, request, redirect, url_for, flash, session
from forum_pkg import db, allowed_file, upload_to_cloudinary
from forum_pkg.models import (
    User, Post, Favorite, Message, Friend, Follow, Notification,
    get_privacy
)


def register_user_routes(app):

    @app.route('/user/<int:user_id>')
    def user_profile(user_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        my_id = session['user_id']
        target = db.session.get(User, user_id)
        if not target:
            flash('用户不存在', 'error')
            return redirect(url_for('forum'))

        if my_id == user_id:
            return redirect(url_for('profile'))

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
            posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()

        favorited_posts = []
        if ps.show_favorites:
            favs = Favorite.query.filter_by(user_id=user_id).order_by(Favorite.id.desc()).all()
            favorited_posts = [db.session.get(Post, fav.post_id) for fav in favs if db.session.get(Post, fav.post_id)]

        is_following = Follow.query.filter_by(follower_id=my_id, followed_id=user_id).first() is not None

        following_users = []
        if ps.show_following:
            flist = Follow.query.filter_by(follower_id=user_id).all()
            for f in flist:
                fu = db.session.get(User, f.followed_id)
                if fu:
                    following_users.append(fu)

        return render_template('user_profile.html',
                               target=target,
                               target_posts=posts,
                               favorited_posts=favorited_posts,
                               following_users=following_users,
                               privacy=ps,
                               friend_status=friend_status,
                               is_friend=is_friend,
                               is_following=is_following)

    @app.route('/follow/<int:user_id>')
    def follow_user(user_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session['user_id'] == user_id:
            flash('不能关注自己', 'error')
            return redirect(request.referrer or url_for('forum'))
        existing = Follow.query.filter_by(follower_id=session['user_id'], followed_id=user_id).first()
        if not existing:
            db.session.add(Follow(follower_id=session['user_id'], followed_id=user_id))
            db.session.commit()
        return redirect(request.referrer or url_for('forum'))

    @app.route('/unfollow/<int:user_id>')
    def unfollow_user(user_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        Follow.query.filter_by(follower_id=session['user_id'], followed_id=user_id).delete()
        db.session.commit()
        return redirect(request.referrer or url_for('forum'))

    @app.route('/notifications')
    def notification_list():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        notifs = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).all()
        return render_template('notifications.html', notifications=notifs)

    @app.route('/notifications/read_all')
    def notification_read_all():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        Notification.query.filter_by(user_id=session['user_id'], is_read=False).update({'is_read': True})
        db.session.commit()
        session['unread_count'] = 0
        return redirect(url_for('notification_list'))

    @app.route('/notification/<int:notif_id>/read')
    def notification_read(notif_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        n = db.session.get(Notification, notif_id)
        if n and n.user_id == session['user_id']:
            n.is_read = True
            db.session.commit()
            session['unread_count'] = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
            return redirect(n.link or url_for('notification_list'))
        return redirect(url_for('notification_list'))

    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('login'))

        if request.method == 'POST':
            form_type = request.form.get('form_type', '')

            if form_type == 'avatar':
                file = request.files.get('avatar')
                if file and file.filename and allowed_file(file.filename):
                    try:
                        avatar_url = upload_to_cloudinary(file)
                        user.avatar = avatar_url
                        session['avatar_url'] = avatar_url
                        db.session.commit()
                        flash('头像更新成功', 'success')
                    except Exception as e:
                        flash(f'头像上传失败: {str(e)}', 'error')
                else:
                    flash('请选择有效的图片文件', 'error')
                return redirect(url_for('profile'))

            new_nickname = request.form.get('nickname', '').strip()
            if new_nickname and new_nickname != user.nickname:
                user.nickname = new_nickname
                session['nickname'] = new_nickname
                db.session.commit()
                flash('昵称更新成功', 'success')
                return redirect(url_for('profile'))

            if 'show_posts' in request.form:
                ps = get_privacy(user.id)
                ps.show_posts = request.form.get('show_posts') == '1'
                ps.show_favorites = request.form.get('show_favorites') == '1'
                ps.show_following = request.form.get('show_following') == '1'
                ps.allow_short_chat = request.form.get('allow_short_chat') == '1'
                ps.allow_friend_request = request.form.get('allow_friend_request') == '1'
                db.session.commit()
                flash('隐私设置已更新', 'success')

            return redirect(url_for('profile'))

        my_posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
        my_favorites = Favorite.query.filter_by(user_id=user.id).order_by(Favorite.id.desc()).all()
        favorited_posts = [db.session.get(Post, fav.post_id) for fav in my_favorites if db.session.get(Post, fav.post_id)]

        ps = get_privacy(user.id)

        short_contacts = set()
        sent_msgs = Message.query.filter_by(sender_id=user.id, chat_type='short').all()
        for m in sent_msgs:
            short_contacts.add(m.receiver)
        received_msgs = Message.query.filter_by(receiver_id=user.id, chat_type='short').all()
        for m in received_msgs:
            short_contacts.add(m.sender)
        short_contacts.discard(user)

        friends = Friend.query.filter(
            ((Friend.user_id == user.id) | (Friend.friend_id == user.id)),
            Friend.status == 'accepted'
        ).all()

        friend_ids = set()
        friend_users = []
        for f in friends:
            f_user = f.friend if f.user_id == user.id else f.user
            friend_users.append(f_user)
            friend_ids.add(f_user.id)

        short_contacts = {c for c in short_contacts if c.id not in friend_ids}

        my_sent_requests = Friend.query.filter_by(user_id=user.id, status='pending').all()
        pending_requests = Friend.query.filter_by(friend_id=user.id, status='pending').all()

        following_users = []
        follows = Follow.query.filter_by(follower_id=user.id).all()
        for f in follows:
            fu = db.session.get(User, f.followed_id)
            if fu:
                following_users.append(fu)

        follower_users = []
        flws = Follow.query.filter_by(followed_id=user.id).all()
        for f in flws:
            fu = db.session.get(User, f.follower_id)
            if fu:
                follower_users.append(fu)

        return render_template('profile.html',
                               user=user,
                               my_posts=my_posts,
                               favorited_posts=favorited_posts,
                               privacy=ps,
                               short_contacts=short_contacts,
                               friend_users=friend_users,
                               pending_requests=pending_requests,
                               my_sent_requests=my_sent_requests,
                               following_users=following_users,
                               follower_users=follower_users)
