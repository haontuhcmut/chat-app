from asgiref.sync import async_to_sync
from celery import Celery

from backend.app.utility.mail_config import create_message, mail

c_app = Celery()
c_app.config_from_object('backend.app.config')

@c_app.task()
def send_email(recipient: list[str], subject: str, body: str):
    message = create_message(recipient, subject, body)
    async_to_sync(mail.send_message)(message)
    print("Email sent")

