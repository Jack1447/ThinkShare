from flask import render_template, request, redirect, url_for, flash, session
from flask_socketio import emit, join_room
from forum_pkg import db, upload_to_cloudinary, socketio
from forum_pkg.models import User, Message, Friend, add_notification


def _room_name(uid1, uid2):
    return f"chat_{min(uid1, uid2)}_{max(uid1, uid2)}"


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


@socketio.on('join')
def on_join(data):
    if 'user_id' not in session:
        return
    peer_id = int(data.get('peer_id', 0))
    if peer_id:
        join_room(_room_name(session['user_id'], peer_id))


@socketio.on('send_message')
def on_send_message(data):
    if 'user_id' not in session:
        return

    my_id = session['user_id']
    peer_id = int(data.get('peer_id', 0))
    content = (data.get('content', '') or '').strip()
    chat_type = data.get('chat_type', 'short')

    if not content:
        return

    if chat_type == 'short':
        ok, err_msg = _check_chat_limit(my_id, peer_id)
        if not ok:
            emit('error', {'message': err_msg})
            return

    msg = Message(
        sender_id=my_id,
        receiver_id=peer_id,
        content=content,
        chat_type=chat_type
    )
    db.session.add(msg)
    db.session.commit()

    sender = db.session.get(User, my_id)
    payload = {
        'id': msg.id,
        'sender_id': my_id,
        'sender_nickname': sender.nickname if sender else '',
        'content': content,
        'file_url': '',
        'file_name': '',
        'created_at': msg.created_at.strftime('%H:%M'),
        'chat_type': chat_type,
    }

    room = _room_name(my_id, peer_id)
    emit('new_message', payload, room=room)

    if chat_type == 'short':
        add_notification(peer_id, my_id, 'short_chat',
                       url_for('chat', peer_id=my_id),
                       f"{session.get('nickname','')} 给你发了一条短时消息")


def register_chat_routes(app):

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
                file_url = upload_to_cloudinary(uploaded_file)
                file_name = uploaded_file.filename

            if not content and not file_url:
                flash('消息不能为空', 'error')
                return redirect(url_for('chat', peer_id=peer_id))

            if chat_type == 'short':
                ok, err_msg = _check_chat_limit(my_id, peer_id)
                if not ok:
                    flash(err_msg, 'error')
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
