import os
import uuid
from datetime import datetime, date, timedelta
from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import markdown as md
from forum_pkg import db, allowed_file
from forum_pkg.models import (
    User, Post, Comment, Like, Favorite, Message,
    Friend, PrivacySetting, Follow, Notification,
    get_privacy, add_notification
)

def register_routes(app):

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('forum'))
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            nickname = request.form.get('nickname', '').strip()
            password = request.form.get('password', '')
            password_confirm = request.form.get('password_confirm', '')

            if not username or not nickname or not password:
                flash('所有字段都必须填写', 'error')
                return render_template('register.html')

            if password != password_confirm:
                flash('两次密码输入不一致', 'error')
                return render_template('register.html')

            if len(password) < 6:
                flash('密码至少需要6位', 'error')
                return render_template('register.html')

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('该用户名已被注册', 'error')
                return render_template('register.html')

            avatar_filename = 'default.png'
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and file.filename and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    avatar_filename = f"avatar_{uuid.uuid4().hex[:8]}.{ext}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename))

            new_user = User(
                username=username,
                nickname=nickname,
                avatar=avatar_filename,
                password_hash=generate_password_hash(password)
            )
            db.session.add(new_user)
            db.session.commit()

            flash('注册成功！请登录', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password_hash, password):
                if user.is_banned:
                    flash('你的账号已被封禁', 'error')
                    return render_template('login.html')

                session['user_id'] = user.id
                session['username'] = user.username
                session['nickname'] = user.nickname
                session['avatar_url'] = user.avatar_url
                session['is_admin'] = user.is_admin
                session['unread_count'] = Notification.query.filter_by(user_id=user.id, is_read=False).count()
                flash('登录成功！', 'success')
                return redirect(url_for('forum'))
            else:
                flash('用户名或密码错误', 'error')

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('已退出登录', 'info')
        return redirect(url_for('login'))

    @app.route('/upload_image', methods=['POST'])
    def upload_image():
        if 'user_id' not in session:
            return {'error': '请先登录'}, 401
        if 'image' not in request.files:
            return {'error': '没有文件'}, 400
        file = request.files['image']
        if file.filename == '' or not allowed_file(file.filename):
            return {'error': '不支持的图片格式'}, 400
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        url = url_for('static', filename=f'uploads/{filename}')
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

    @app.route('/chat/<int:peer_id>', methods=['GET', 'POST'])
    def chat(peer_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        my_id = session['user_id']
        peer = db.session.get(User, peer_id)
        if not peer:
            return redirect(url_for('forum'))

        is_friend = Friend.query.filter(
            ((Friend.user_id == my_id) & (Friend.friend_id == peer_id)) |
            ((Friend.user_id == peer_id) & (Friend.friend_id == my_id)),
            Friend.status == 'accepted'
        ).first() is not None

        chat_type = 'long' if is_friend else 'short'

        if request.method == 'POST':
            content = request.form.get('content', '').strip()
            uploaded_file = request.files.get('file')

            file_url = ''
            file_name = ''
            if chat_type == 'long' and uploaded_file and uploaded_file.filename:
                if allowed_file(uploaded_file.filename):
                    ext = uploaded_file.filename.rsplit('.', 1)[1].lower()
                    fname = f"chat_{uuid.uuid4().hex[:8]}.{ext}"
                    uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                    file_url = url_for('static', filename=f'uploads/{fname}')
                    file_name = uploaded_file.filename
                else:
                    flash('不支持的文件格式', 'error')
                    return redirect(url_for('chat', peer_id=peer_id))

            if not content and not file_url:
                flash('消息不能为空', 'error')
                return redirect(url_for('chat', peer_id=peer_id))

            if chat_type == 'short':
                existing_short = Message.query.filter(
                    ((Message.sender_id == my_id) & (Message.receiver_id == peer_id)) |
                    ((Message.sender_id == peer_id) & (Message.receiver_id == my_id)),
                    Message.chat_type == 'short'
                ).count()

                if existing_short >= 10:
                    flash('短时聊天已达10条上限', 'error')
                    return redirect(url_for('chat', peer_id=peer_id))

                peer_replied = Message.query.filter_by(
                    sender_id=peer_id, receiver_id=my_id, chat_type='short'
                ).first() is not None

                my_sent = Message.query.filter_by(
                    sender_id=my_id, receiver_id=peer_id, chat_type='short'
                ).count()

                if not peer_replied and my_sent >= 1:
                    flash('对方尚未回复，无法继续发送', 'error')
                    return redirect(url_for('chat', peer_id=peer_id))

            msg = Message(
                sender_id=my_id,
                receiver_id=peer_id,
                content=content,
                file_url=file_url,
                file_name=file_name,
                chat_type=chat_type
            )
            db.session.add(msg)
            db.session.commit()

            if chat_type == 'short':
                add_notification(peer_id, my_id, 'short_chat',
                               url_for('chat', peer_id=my_id),
                               f"{session.get('nickname','')} 给你发了一条短时消息")

            return redirect(url_for('chat', peer_id=peer_id))

        if is_friend:
            messages = Message.query.filter(
                ((Message.sender_id == my_id) & (Message.receiver_id == peer_id)) |
                ((Message.sender_id == peer_id) & (Message.receiver_id == my_id))
            ).order_by(Message.created_at.asc()).all()
        else:
            messages = Message.query.filter(
                ((Message.sender_id == my_id) & (Message.receiver_id == peer_id)) |
                ((Message.sender_id == peer_id) & (Message.receiver_id == my_id)),
                Message.chat_type == 'short'
            ).order_by(Message.created_at.asc()).all()

        total_count = Message.query.filter(
            ((Message.sender_id == my_id) & (Message.receiver_id == peer_id)) |
            ((Message.sender_id == peer_id) & (Message.receiver_id == my_id)),
            Message.chat_type == 'short'
        ).count() if chat_type == 'short' else None

        return render_template('chat.html',
                               peer=peer,
                               messages=messages,
                               chat_type=chat_type,
                               total_count=total_count)

    @app.route('/add_friend/<int:friend_id>')
    def add_friend(friend_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        my_id = session['user_id']
        if my_id == friend_id:
            flash('不能添加自己为好友', 'error')
            return redirect(url_for('profile'))

        existing = Friend.query.filter(
            ((Friend.user_id == my_id) & (Friend.friend_id == friend_id)) |
            ((Friend.user_id == friend_id) & (Friend.friend_id == my_id))
        ).first()

        if existing:
            if existing.status == 'pending':
                flash('已发送过好友请求', 'info')
            elif existing.status == 'accepted':
                flash('你们已经是好友了', 'info')
            return redirect(url_for('profile'))

        friend_req = Friend(user_id=my_id, friend_id=friend_id)
        db.session.add(friend_req)
        db.session.commit()

        add_notification(friend_id, my_id, 'friend_request',
                       url_for('profile', tab='friends'),
                       f"{session.get('nickname','')} 请求添加你为好友")

        flash('好友请求已发送', 'success')
        return redirect(url_for('profile'))

    @app.route('/handle_friend/<int:req_id>/<action>')
    def handle_friend(req_id, action):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        friend_req = db.session.get(Friend, req_id)
        if not friend_req or friend_req.friend_id != session['user_id']:
            flash('无权操作', 'error')
            return redirect(url_for('profile'))

        if action == 'accept':
            friend_req.status = 'accepted'
            add_notification(friend_req.user_id, session['user_id'], 'friend_accept',
                           url_for('profile', tab='friends'),
                           f"{session.get('nickname','')} 已同意你的好友请求")
            flash('已同意好友请求', 'success')
        elif action == 'reject':
            friend_req.status = 'rejected'
            add_notification(friend_req.user_id, session['user_id'], 'friend_reject',
                           url_for('profile'),
                           f"{session.get('nickname','')} 拒绝了你的好友请求")
            flash('已拒绝好友请求', 'info')

        db.session.commit()
        return redirect(url_for('profile'))

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
                if fu: following_users.append(fu)

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
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and file.filename and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    avatar_filename = f"avatar_{uuid.uuid4().hex[:8]}.{ext}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename))
                    user.avatar = avatar_filename
                    session['avatar_url'] = user.avatar_url
                    db.session.commit()
                    flash('头像更新成功', 'success')

            new_nickname = request.form.get('nickname', '').strip()
            if new_nickname and new_nickname != user.nickname:
                user.nickname = new_nickname
                session['nickname'] = new_nickname
                db.session.commit()
                flash('昵称更新成功', 'success')

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
            if fu: following_users.append(fu)

        follower_users = []
        flws = Follow.query.filter_by(followed_id=user.id).all()
        for f in flws:
            fu = db.session.get(User, f.follower_id)
            if fu: follower_users.append(fu)

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

    @app.route('/admin')
    def admin():
        if not session.get('is_admin'):
            flash('无权访问管理后台', 'error')
            return redirect(url_for('forum'))

        stats = {
            'total_posts': Post.query.count(),
            'total_users': User.query.count(),
            'total_comments': Comment.query.count(),
            'banned_users': User.query.filter_by(is_banned=True).count(),
        }
        users = User.query.order_by(User.created_at.desc()).all()
        return render_template('admin.html', stats=stats, users=users)

    @app.route('/admin/ban/<int:user_id>')
    def admin_ban(user_id):
        if not session.get('is_admin'):
            flash('无权操作', 'error')
            return redirect(url_for('forum'))

        user = db.session.get(User, user_id)
        if not user:
            flash('用户不存在', 'error')
            return redirect(url_for('admin'))
        if user.is_admin:
            flash('不能封禁管理员', 'error')
            return redirect(url_for('admin'))

        user.is_banned = True
        db.session.commit()
        flash(f'用户 {user.nickname} 已被封禁', 'success')
        return redirect(url_for('admin'))

    @app.route('/admin/unban/<int:user_id>')
    def admin_unban(user_id):
        if not session.get('is_admin'):
            flash('无权操作', 'error')
            return redirect(url_for('forum'))

        user = db.session.get(User, user_id)
        if not user:
            flash('用户不存在', 'error')
            return redirect(url_for('admin'))

        user.is_banned = False
        db.session.commit()
        flash(f'用户 {user.nickname} 已解封', 'success')
        return redirect(url_for('admin'))
