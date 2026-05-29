import re
import os
from datetime import datetime
from flask import url_for
import markdown as md
from forum_pkg import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    nickname = db.Column(db.String(80), nullable=False, index=True)
    avatar = db.Column(db.String(200), default='default.png')
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    likes = db.relationship('Like', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

    @property
    def avatar_url(self):
        if self.avatar and self.avatar.startswith('http'):
            return self.avatar
        if self.avatar and self.avatar != 'default.png':
            if os.environ.get('DATABASE_URL'):
                return url_for('static', filename='img/default_avatar.svg')
            return url_for('static', filename=f'uploads/{self.avatar}')
        return url_for('static', filename='img/default_avatar.svg')

    @property
    def like_count(self):
        return Like.query.join(Post).filter(Post.user_id == self.id).count()

    @property
    def favorite_count(self):
        return Favorite.query.join(Post).filter(Post.user_id == self.id).count()

    @property
    def following_count(self):
        return Follow.query.filter_by(follower_id=self.id).count()

    @property
    def follower_count(self):
        return Follow.query.filter_by(followed_id=self.id).count()

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    views = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    comments = db.relationship('Comment', backref='post', lazy=True)
    likes = db.relationship('Like', backref='post', lazy=True)
    favorites = db.relationship('Favorite', backref='post', lazy=True)

    @property
    def comment_count(self):
        return Comment.query.filter_by(post_id=self.id).count()

    @property
    def like_count(self):
        return Like.query.filter_by(post_id=self.id).count()

    @property
    def favorite_count(self):
        return Favorite.query.filter_by(post_id=self.id).count()

    @property
    def content_plain(self):
        html = md.markdown(self.content, extensions=['fenced_code', 'nl2br'])
        clean = re.sub(r'<[^>]+>', '', html)
        return clean[:200] + ('...' if len(clean) > 200 else '')

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)

class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, default='')
    file_url = db.Column(db.String(200), default='')
    file_name = db.Column(db.String(200), default='')
    chat_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

class Friend(db.Model):
    __tablename__ = 'friends'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref='friend_requests_sent')
    friend = db.relationship('User', foreign_keys=[friend_id], backref='friend_requests_received')

class PrivacySetting(db.Model):
    __tablename__ = 'privacy_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    show_posts = db.Column(db.Boolean, default=True)
    show_favorites = db.Column(db.Boolean, default=True)
    show_following = db.Column(db.Boolean, default=True)
    allow_short_chat = db.Column(db.Boolean, default=True)
    allow_friend_request = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref='privacy')

class Follow(db.Model):
    __tablename__ = 'follows'
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    follower = db.relationship('User', foreign_keys=[follower_id], backref='following_rels')
    followed = db.relationship('User', foreign_keys=[followed_id], backref='follower_rels')

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    type = db.Column(db.String(30), nullable=False)
    link = db.Column(db.String(200), default='')
    content = db.Column(db.String(200), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    from_user = db.relationship('User', foreign_keys=[from_user_id])

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_type = db.Column(db.String(10), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(15), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reports_filed')

def get_privacy(user_id):
    ps = PrivacySetting.query.filter_by(user_id=user_id).first()
    if not ps:
        ps = PrivacySetting(user_id=user_id)
        db.session.add(ps)
        db.session.commit()
    return ps

def add_notification(to_user_id, from_user_id, ntype, link, content):
    if to_user_id == from_user_id:
        return
    n = Notification(user_id=to_user_id, from_user_id=from_user_id, type=ntype, link=link, content=content)
    db.session.add(n)
    db.session.commit()
