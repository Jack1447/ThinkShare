import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

db = SQLAlchemy()

def create_app():
    package_dir = os.path.abspath(os.path.dirname(__file__))
    project_dir = os.path.dirname(package_dir)

    app = Flask(__name__,
                template_folder=os.path.join(project_dir, 'templates'),
                static_folder=os.path.join(project_dir, 'static'))
    app.secret_key = os.environ.get('SECRET_KEY', 'campus_forum_secret_key_2024')

    database_url = os.environ.get('DATABASE_URL', '')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(project_dir, 'campus.db')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(project_dir, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response

    from forum_pkg import routes
    routes.register_routes(app)

    with app.app_context():
        db.create_all()

    return app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
