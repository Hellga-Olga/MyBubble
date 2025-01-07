import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, 'my_bubble.env'))

# The configuration class for this application
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = os.environ.get('ADMINS')
    SECURITY_EMAIL_SENDER = ''
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    MAIL_DEBUG = 1
    LANGUAGES = ['en', 'ru']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    POSTS_PER_PAGE = 5
    NEW_POSTS_PER_PAGE = 2
    MAX_CONTENT_LENGTH = 5120 * 5120
    UPLOAD_EXTENSIONS = ['.JPG', '.jpg', '.jpeg', '.png', '.gif']
    IMAGE_EXTENSIONS = ['.JPG', '.jpg', '.jpeg', '.JPEG', '.png']
    UPLOAD_PATH = "app/static/uploads/posts"
    AVATAR_UPLOAD_PATH = "app/static/avatars"
    AVATAR_DELETE_PATH = "app/static/"
    DOWNLOAD_PATH = "static/uploads/posts"
    IMAGE_DOWNLOAD_PATH = "static/uploads/images"
    STATIC_PATH = "uploads/posts/"
    AVATAR_STATIC_PATH = "avatars/"
