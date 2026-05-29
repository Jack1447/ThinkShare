from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import re
from forum_pkg import db, allowed_file, upload_to_cloudinary
from forum_pkg.models import User, Notification


def register_auth_routes(app):

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

            if len(username) < 3 or len(username) > 20:
                flash('用户名长度需在 3-20 个字符之间', 'error')
                return render_template('register.html')

            if not re.match(r'^[\u4e00-\u9fffa-zA-Z0-9_]+$', username):
                flash('用户名只能包含中文、字母、数字和下划线', 'error')
                return render_template('register.html')

            if len(nickname) > 20:
                flash('昵称不能超过 20 个字符', 'error')
                return render_template('register.html')

            if len(password) > 128:
                flash('密码不能超过 128 位', 'error')
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

            avatar_url = ''
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and file.filename and allowed_file(file.filename):
                    try:
                        avatar_url = upload_to_cloudinary(file)
                    except Exception:
                        pass

            new_user = User(
                username=username,
                nickname=nickname,
                avatar=avatar_url,
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
