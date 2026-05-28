import os

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'campus_forum_secret_key_2024')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'campus.db')


class ProductionConfig(Config):
    DEBUG = False

    @staticmethod
    def init_app(app):
        database_url = os.environ.get('DATABASE_URL', '')
        if database_url:
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        else:
            app.config['SQLALCHEMY_DATABASE_URI'] = \
                'sqlite:///' + os.path.join(basedir, 'campus.db')


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
