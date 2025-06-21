# services/email_service.py - Email Service Stub
import smtplib
from email.mime.text import MIMEText

class EmailService:
    def send_confirmation(self, smtp_user, smtp_password, to_email, subject, body):
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = to_email

            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, [to_email], msg.as_string())
            print(f"[DEBUG] Email sent from {smtp_user} to {to_email}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send email: {e}")
            return False
