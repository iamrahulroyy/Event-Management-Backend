import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from extra.variables import FROM_EMAIL, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT

def send_email_single(to_email: str, token: str):
    """
    Sends an RSVP invitation email using SMTP.
    """
    with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as server:
        server.starttls()
        server.login(FROM_EMAIL, SMTP_PASSWORD)
        
        msg = MIMEMultipart()
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = "Event Invitation - RSVP"
        
        body = f"""
        You have been invited to an event!
        
        Please click one of the following links to respond:
        Accept: http://localhost:8000/rsvp/respond/{token}/accept
        Decline: http://localhost:8000/rsvp/respond/{token}/decline
        
        Thank you!
        """
        
        msg.attach(MIMEText(body, "plain"))
        server.send_message(msg)