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
    POSTS_PER_PAGE = 10
    NEW_POSTS_PER_PAGE = 2
    IMAGES_PER_PAGE = 10
    VIDEOS_PER_PAGE = 2
    VIDEOS_PER_VID_PAGE = 12
    MAX_CONTENT_LENGTH = 5120 * 5120
    UPLOAD_EXTENSIONS = ['.JPG', '.jpg', '.jpeg', '.png', '.gif', '.mp4']
    IMAGE_EXTENSIONS = ['.JPG', '.jpg', '.jpeg', '.JPEG', '.png']
    AUDIO_EXTENSIONS = ['.mp3', '.MP3', '.WAV', '.FLAC']
    UPLOAD_PATH = "app/static/uploads/posts"
    IMAGE_UPLOAD_PATH = "app/static/uploads/images"
    AUDIO_UPLOAD_PATH = "app/static/uploads/audios"
    VIDEO_UPLOAD_PATH = "app/static/uploads/videos"
    AVATAR_UPLOAD_PATH = "app/static/avatars"
    DOWNLOAD_PATH = "static/uploads/posts"
    IMAGE_DOWNLOAD_PATH = "static/uploads/images"
    VIDEO_DOWNLOAD_PATH = "static/uploads/videos"
    AUDIO_DOWNLOAD_PATH = "static/uploads/audios"
    STATIC_PATH = "uploads/posts"
