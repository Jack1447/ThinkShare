from flask import Blueprint, request, jsonify, url_for
from flask_jwt_extended import jwt_required, current_user
from forum_pkg import db, upload_to_cloudinary
from forum_pkg.models import User, Message, Friend, add_notification

chat_bp = Blueprint('api_chat', __name__)


def _check_chat_limit(my_id, peer_id):
    existing = Message.query.filter(
        ((Message.sender_id == my_id) & (Message.receiver_id == peer_id)) |
        ((Message.sender_id == peer_id) & (Message.receiver_id == my_id)),
        Message.chat_type == 'short'
    ).count()
    if existing >= 10:
        return False, '短时聊天已达10条上限'

    peer_replied = Message.query.filter_by(
        sender_id=peer_id, receiver_id=my_id, chat_type='short'
    ).first() is not None

    my_sent = Message.query.filter_by(
        sender_id=my_id, receiver_id=peer_id, chat_type='short'
    ).count()

    if not peer_replied and my_sent >= 1:
        return False, '对方尚未回复，无法继续发送'

    return True, ''


@chat_bp.route('/chat/<int:peer_id>', methods=['GET'])
@jwt_required()
def api_chat(peer_id):
    my_id = current_user.id
    peer = db.session.get(User, peer_id)
    if not peer:
        return jsonify({'message': '用户不存在'}), 404

    is_friend = Friend.query.filter(
        ((Friend.user_id == my_id) & (Friend.friend_id == peer_id)) |
        ((Friend.user_id == peer_id) & (Friend.friend_id == my_id)),
        Friend.status == 'accepted'
    ).first() is not None

    chat_type = 'long' if is_friend else 'short'

    if is_friend:
        msgs = Message.query.filter(
            ((Message.sender_id == my_id) & (Message.receiver_id == peer_id)) |
            ((Message.sender_id == peer_id) & (Message.receiver_id == my_id))
        ).order_by(Message.created_at.asc()).all()
    else:
        msgs = Message.query.filter(
            ((Message.sender_id == my_id) & (Message.receiver_id == peer_id)) |
            ((Message.sender_id == peer_id) & (Message.receiver_id == my_id)),
            Message.chat_type == 'short'
        ).order_by(Message.created_at.asc()).all()

    total_count = len(msgs)

    return jsonify({
        'peer': {
            'id': peer.id,
            'nickname': peer.nickname,
            'avatar_url': peer.avatar_url,
        },
        'chat_type': chat_type,
        'total_count': total_count,
        'messages': [{
            'id': m.id,
            'sender_id': m.sender_id,
            'receiver_id': m.receiver_id,
            'content': m.content,
            'file_url': m.file_url,
            'file_name': m.file_name,
            'created_at': m.created_at.isoformat(),
        } for m in msgs],
    }), 200


@chat_bp.route('/chat/<int:peer_id>', methods=['POST'])
@jwt_required()
def api_send_message(peer_id):
    my_id = current_user.id
    peer = db.session.get(User, peer_id)
    if not peer:
        return jsonify({'message': '用户不存在'}), 404

    is_friend = Friend.query.filter(
        ((Friend.user_id == my_id) & (Friend.friend_id == peer_id)) |
        ((Friend.user_id == peer_id) & (Friend.friend_id == my_id)),
        Friend.status == 'accepted'
    ).first() is not None

    chat_type = 'long' if is_friend else 'short'

    content = (request.form.get('content') or (request.get_json(silent=True) or {}).get('content') or '').strip()
    file_url = ''
    file_name = ''

    if chat_type == 'long' and 'file' in request.files:
        f = request.files['file']
        if f and f.filename:
            file_url = upload_to_cloudinary(f)
            file_name = f.filename

    if not content and not file_url:
        return jsonify({'message': '消息不能为空'}), 400

    if chat_type == 'short':
        ok, err_msg = _check_chat_limit(my_id, peer_id)
        if not ok:
            return jsonify({'message': err_msg}), 400

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
                         f"{current_user.nickname} 给你发了一条短时消息")

    return jsonify({
        'id': msg.id,
        'sender_id': msg.sender_id,
        'content': msg.content,
        'file_url': msg.file_url,
        'file_name': msg.file_name,
        'created_at': msg.created_at.isoformat(),
    }), 201
