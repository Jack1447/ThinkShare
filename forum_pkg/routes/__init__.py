from forum_pkg.routes.auth import register_auth_routes
from forum_pkg.routes.forum import register_forum_routes
from forum_pkg.routes.chat import register_chat_routes
from forum_pkg.routes.user import register_user_routes
from forum_pkg.routes.admin import register_admin_routes
from forum_pkg.routes.api import api_bp


def register_all_routes(app):
    app.register_blueprint(api_bp)
    register_auth_routes(app)
    register_forum_routes(app)
    register_chat_routes(app)
    register_user_routes(app)
    register_admin_routes(app)
