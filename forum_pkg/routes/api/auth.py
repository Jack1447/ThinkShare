from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, current_user
from forum_pkg import db
from forum_pkg.models import User, Notification

auth_bp = Blueprint('api_auth', __name__)


@auth_bp.route('/auth/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    nickname = (data.get('nickname') or '').strip()
    password = data.get('password', '')

    if not username or not nickname or not password:
        return jsonify({'message': '所有字段都必须填写'}), 400

    if len(password) < 6:
        return jsonify({'message': '密码至少需要6位'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': '该用户名已被注册'}), 409

    new_user = User(
        username=username,
        nickname=nickname,
        password_hash=generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': '注册成功'}), 201


@auth_bp.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password', '')

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': '用户名或密码错误'}), 401

    if user.is_banned:
        return jsonify({'message': '你的账号已被封禁'}), 403

    access_token = create_access_token(identity=str(user.id))
    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()

    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'avatar_url': user.avatar_url,
            'is_admin': user.is_admin,
            'unread_count': unread_count,
            'like_count': user.like_count,
            'following_count': user.following_count,
            'follower_count': user.follower_count,
        }
    }), 200


@auth_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def api_me():
    user = current_user
    if not user:
        return jsonify({'message': '用户不存在'}), 404

    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()

    return jsonify({
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'avatar_url': user.avatar_url,
        'is_admin': user.is_admin,
        'unread_count': unread_count,
        'like_count': user.like_count,
        'following_count': user.following_count,
        'follower_count': user.follower_count,
    }), 200
