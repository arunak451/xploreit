import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")


def send_email(name: str, email: str, phone: str, course: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER
        msg["Subject"] = f"New Student Enquiry - {name}"

        body = f"""
        New Student Enquiry Received!
        
        Name   : {name}
        Email  : {email}
        Phone  : {phone}
        Course : {course}
        
        XploreiT Corp - AI Agent System
        """

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        server.quit()

        print(f"Email sent for: {name}")
        return True

    except Exception as e:
        print(f"Email error: {e}")
        return False


if __name__ == "__main__":
    send_email("Test Student", "test@gmail.com", "+919999999999", "Python")
    print("Email test done!")
