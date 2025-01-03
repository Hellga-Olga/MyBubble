import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db, cli #The Flask application instance is called app, and is a member of the app package, imports the app variable that is a member of the app package
from app.models import User, Post, Message, Notification

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Post': Post,
            'Message': Message, 'Notification': Notification}