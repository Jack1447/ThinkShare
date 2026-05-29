from forum_pkg.routes.api import api_bp


def register_all_routes(app):
    app.register_blueprint(api_bp)
