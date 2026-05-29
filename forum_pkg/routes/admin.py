from flask import render_template, request, redirect, url_for, flash, session
from sqlalchemy.orm import joinedload
from forum_pkg import db
from forum_pkg.models import User, Post, Comment, Like, Favorite, Report, add_notification


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
            'pending_reports': Report.query.filter_by(status='pending').count(),
        }
        users = User.query.order_by(User.created_at.desc()).all()
        posts = Post.query.options(joinedload(Post.author)).order_by(Post.created_at.desc()).all()
        reports = Report.query.options(joinedload(Report.reporter)).order_by(Report.created_at.desc()).all()
        return render_template('admin.html', stats=stats, users=users, posts=posts, reports=reports)

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

    @app.route('/admin/delete_post/<int:post_id>')
    def admin_delete_post(post_id):
        if not session.get('is_admin'):
            flash('无权操作', 'error')
            return redirect(url_for('forum'))

        post = db.session.get(Post, post_id)
        if not post:
            flash('帖子不存在', 'error')
            return redirect(url_for('admin'))

        Comment.query.filter_by(post_id=post_id).delete()
        Like.query.filter_by(post_id=post_id).delete()
        Favorite.query.filter_by(post_id=post_id).delete()
        db.session.delete(post)
        db.session.commit()

        flash('帖子已删除', 'info')
        return redirect(url_for('admin'))

    @app.route('/admin/resolve_report/<int:report_id>')
    def admin_resolve_report(report_id):
        if not session.get('is_admin'):
            flash('无权操作', 'error')
            return redirect(url_for('forum'))

        report = db.session.get(Report, report_id)
        if not report:
            flash('举报不存在', 'error')
            return redirect(url_for('admin'))

        if report.target_type == 'post':
            post = db.session.get(Post, report.target_id)
            if post:
                Comment.query.filter_by(post_id=post.id).delete()
                Like.query.filter_by(post_id=post.id).delete()
                Favorite.query.filter_by(post_id=post.id).delete()
                db.session.delete(post)
                add_notification(post.user_id, session['user_id'], 'report_resolved',
                               url_for('forum'),
                               '你的帖子因违规被管理员删除')
        elif report.target_type == 'comment':
            comment = db.session.get(Comment, report.target_id)
            if comment:
                post_id = comment.post_id
                def delete_replies(parent_id):
                    replies = Comment.query.filter_by(parent_id=parent_id).all()
                    for reply in replies:
                        delete_replies(reply.id)
                        db.session.delete(reply)
                delete_replies(comment.id)
                add_notification(comment.user_id, session['user_id'], 'report_resolved',
                               url_for('post_detail', post_id=post_id),
                               '你的评论因违规被管理员删除')
                db.session.delete(comment)

        report.status = 'resolved'
        db.session.commit()

        add_notification(report.reporter_id, session['user_id'], 'report_resolved',
                       url_for('forum'),
                       '你举报的内容经审核已被删除，感谢你的监督')
        flash('举报已处理，相关内容已删除', 'success')
        return redirect(url_for('admin'))

    @app.route('/admin/dismiss_report/<int:report_id>')
    def admin_dismiss_report(report_id):
        if not session.get('is_admin'):
            flash('无权操作', 'error')
            return redirect(url_for('forum'))

        report = db.session.get(Report, report_id)
        if not report:
            flash('举报不存在', 'error')
            return redirect(url_for('admin'))

        report.status = 'dismissed'
        db.session.commit()

        add_notification(report.reporter_id, session['user_id'], 'report_dismissed',
                       url_for('forum'),
                       '你举报的内容经审核未发现问题')
        flash('举报已忽略', 'info')
        return redirect(url_for('admin'))
