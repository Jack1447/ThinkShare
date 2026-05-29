from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from forum_pkg.routes.api.auth import auth_bp
from forum_pkg.routes.api.forum import forum_bp
from forum_pkg.routes.api.user import user_bp
from forum_pkg.routes.api.chat import chat_bp
from forum_pkg.routes.api.admin import admin_bp

api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(forum_bp)
api_bp.register_blueprint(user_bp)
api_bp.register_blueprint(chat_bp)
api_bp.register_blueprint(admin_bp)
