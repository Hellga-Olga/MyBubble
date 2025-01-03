from flask import current_app
from flask_mail import Message
from threading import Thread
from app import mail

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # send_async_email function runs in a background thread;
    # when the process completes the thread will end and clean itself up
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()