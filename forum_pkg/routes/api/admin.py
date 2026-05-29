from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, current_user
from forum_pkg import db
from forum_pkg.models import User, Post, Comment

admin_bp = Blueprint('api_admin', __name__)


@admin_bp.before_request
@jwt_required()
def check_admin():
    if not current_user.is_admin:
        return jsonify({'message': '无权访问管理后台'}), 403


@admin_bp.route('/admin', methods=['GET'])
def api_admin():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({
        'stats': {
            'total_users': User.query.count(),
            'total_posts': Post.query.count(),
            'total_comments': Comment.query.count(),
            'banned_users': User.query.filter_by(is_banned=True).count(),
        },
        'users': [{
            'id': u.id,
            'username': u.username,
            'nickname': u.nickname,
            'avatar_url': u.avatar_url,
            'is_admin': u.is_admin,
            'is_banned': u.is_banned,
            'created_at': u.created_at.isoformat(),
        } for u in users],
    }), 200


@admin_bp.route('/admin/ban/<int:user_id>', methods=['POST'])
def api_ban(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    if user.is_admin:
        return jsonify({'message': '不能封禁管理员'}), 400

    user.is_banned = True
    db.session.commit()
    return jsonify({'message': f'用户 {user.nickname} 已被封禁'}), 200


@admin_bp.route('/admin/unban/<int:user_id>', methods=['POST'])
def api_unban(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404

    user.is_banned = False
    db.session.commit()
    return jsonify({'message': f'用户 {user.nickname} 已解封'}), 200
