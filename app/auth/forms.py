from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
import sqlalchemy as sa
from app import db
from app.models import User
# _l wraps the text in a special object that triggers the translation to be performed later,
# when the string is used inside a request
from flask_babel import _, lazy_gettext as _l


class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired(_l('Enter your username'))]) #prevent invalid data from being accepted into the application
    password = PasswordField(_l('Password'), validators=[DataRequired(_l('Enter your password'))])
    remember_me = BooleanField(_l('Remember me'))
    submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired(_l('Enter your username'))])
    email = StringField(_l('Email'), validators=[DataRequired(_l('Enter your email address')), Email()]) # ensures that the user passes a string that matches the structure of email address
    password = PasswordField(_l('Password'), validators=[DataRequired(_l('Enter your password'))])
    password2 = PasswordField(_l('Repeat password'), validators=[DataRequired(_l('Repeat password')), EqualTo('password')])
    submit = SubmitField(_l('Sign Up'))

    # WTForms takes these methods as custom validators and invokes them in addition to the stock validators
    def validate_username(self, username): # ensures that a username is not already in the database
        user = db.session.scalar(sa.select(User).where(User.username==username.data))
        if user is not None:
            raise ValidationError(_('Please use a different username'))

    def validate_email(self, email): # ensures that an email is not already in the database
        user = db.session.scalar(sa.select(User).where(User.email==email.data))
        if user is not None:
            raise ValidationError(_('Please use a different email'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Enter Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Reset password'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Reset password'))