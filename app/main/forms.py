from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Length
import sqlalchemy as sa
from app import db
from app.models import User
# _l wraps the text in a special object that triggers the translation to be performed later,
# when the string is used inside a request
from flask_babel import _, lazy_gettext as _l


class EmptyForm(FlaskForm):
    submit = SubmitField(_l('Submit'))


class EditProfileForm(FlaskForm):
    username = StringField(_('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_('About Me'), validators=[Length(min=0, max=140)])
    submit = SubmitField(_('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(User.username == username.data))
            if user is not None:
                raise ValidationError(_('Please use a different username'))

class PostForm(FlaskForm):
    post = TextAreaField(_l('Write something'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))

class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))