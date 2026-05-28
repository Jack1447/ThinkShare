from flask import render_template, request, redirect, url_for, flash, session
from forum_pkg import db
from forum_pkg.models import User, Post, Comment


def register_admin_routes(app):

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
