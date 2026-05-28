import os
import logging
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy import inspect, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

db = SQLAlchemy()
socketio = SocketIO()

cloudinary.config(
    cloudinary_url=os.environ.get('CLOUDINARY_URL', '')
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_to_cloudinary(file):
    result = cloudinary.uploader.upload(file)
    return result['secure_url']


def setup_logging(app):
    if not app.debug:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    package_dir = os.path.abspath(os.path.dirname(__file__))
    project_dir = os.path.dirname(package_dir)

    app = Flask(__name__,
                template_folder=os.path.join(project_dir, 'templates'),
                static_folder=os.path.join(project_dir, 'static'))

    from forum_pkg.config import config_map
    app.config.from_object(config_map[config_name])
    if hasattr(config_map[config_name], 'init_app'):
        config_map[config_name].init_app(app)

    app.config['UPLOAD_FOLDER'] = os.path.join(project_dir, 'static', 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    setup_logging(app)
    db.init_app(app)
    socketio.init_app(app)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('500.html'), 500

    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response

    from forum_pkg.routes import register_all_routes
    register_all_routes(app)

    with app.app_context():
        db.create_all()

        inspector = inspect(db.engine)
        existing_cols = [c['name'] for c in inspector.get_columns('messages')]
        if 'file_url' not in existing_cols:
            db.session.execute(text("ALTER TABLE messages ADD COLUMN file_url VARCHAR(200) DEFAULT ''"))
        if 'file_name' not in existing_cols:
            db.session.execute(text("ALTER TABLE messages ADD COLUMN file_name VARCHAR(200) DEFAULT ''"))
        db.session.commit()

    return app
