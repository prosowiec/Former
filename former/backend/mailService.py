from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
import asyncio
from fastapi.templating import Jinja2Templates

from ..config import (
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_FROM,
    MAIL_FROM_NAME,
    MAIL_SERVER,
    MAIL_PORT,
    EMAIL_VERIFY_URL,
    PASSWORD_RESET_URL,
    FRONTEND_URL,
)

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_PORT=MAIL_PORT,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fast_mail = FastMail(conf)
templates = Jinja2Templates(directory="former/backend/templates")

def send_email_sync(recipient_email: str, subject: str, html: str = None) -> bool:
    """
    Synchronous wrapper for send_email.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(send_email(recipient_email, subject, html))



async def send_email(recipient_email: str, subject: str, html: str) -> bool:
    try:
        message = MessageSchema(
            subject=subject,
            recipients=[recipient_email],
            body=html,
            subtype=MessageType.html,
        )

        await fast_mail.send_message(message)
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_email_verification(user_email: str, verify_link: str) -> bool:
    template = templates.get_template("verification_mail.html")
    
    html_content = template.render(
        verify_link=verify_link,
    )
    
    subject = "Email Verification - Former App"
    
    email_sent = send_email_sync(user_email, subject, html_content)
    
    return email_sent

def send_password_reset_email(user_email: str, reset_link: str) -> bool:
    template = templates.get_template("reset_password_mail.html")
    
    html_content = template.render(
        reset_link=reset_link,
    )
    
    subject = "Password Reset - Former App"
    
    email_sent = send_email_sync(user_email, subject, html_content)
    
    return email_sent