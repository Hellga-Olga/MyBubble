import os
import logging
from flask import Flask, request, current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from logging.handlers import SMTPHandler, RotatingFileHandler

def get_locale():
    # Flask object provides a high-level interface to work with the Accept-Language header containing browser's preferences
    # which in turn specifies the client language and locale preferences as a weighted list
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])

# global scope
db = SQLAlchemy() # creates an instance of the extension that is not attached to the application
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login' # the function/endpoint name for the login view
login.login_message = _l('Please log in to access this page.')
mail = Mail()
moment = Moment()
babel = Babel()

# factory function
def create_app(config_class=Config):
    app = Flask(__name__)  # an instance of class Flask
    app.config.from_object(config_class)
    db.init_app(app) # binds the SQLAlchemy instance to the application
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp) # connects the errors blueprint to the application

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.cli import bp as cli_bp
    app.register_blueprint(cli_bp)

    db.create_all()

    with app.app_context():
        boards = ["Casual", "Movies", "Music", "Video Games", "Books"]
        for board in boards:
            if not Board.query.filter_by(name=board).first():
                db.session.add(Board(name=board))
        db.session.commit()
    # creates a SMTPHandler instance, sets its level so that it only reports errors and not warnings,
    # informational or debugging messages, and attaches it to the app.logger object from Flask
    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='MyBubble Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
            os.mkdir('logs')
        # limits the size of the log file to 10KB, and keeps the last ten log files as backup
        file_handler = RotatingFileHandler('logs/mybubble.log', maxBytes=10240,
                                       backupCount=10)
        #  includes the timestamp, the logging level, the message and the source file
        #  and line number from where the log entry originated
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('MyBubble startup') # server writes a line to the logs each time it starts

    return app

from app import models # reference to the app package
from app.models import Board