import os
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Carrega exatamente o arquivo .env que está na mesma pasta (api_email/.env)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class DisparadorEmail:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_SERVER", "smtp.ethereal.email")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("EMAIL_USER")
        self.smtp_pass = os.getenv("EMAIL_PASS")

    def enviar_mensagem(self, destinatario, assunto, corpo):
        if not self.smtp_user or not self.smtp_pass:
            raise Exception(f"Credenciais ausentes no arquivo: {env_path}")

        msg = MIMEMultipart()
        msg["From"] = self.smtp_user
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain"))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.smtp_user, destinatario, msg.as_string())
        return True