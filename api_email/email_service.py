import os
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Carrega o arquivo .env da mesma pasta (onde ficam o usuário e a senha secretos)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


class DisparadorEmail:
    def __init__(self):
        # Pega o endereço do servidor, a porta, o e-mail e a senha lá do .env
        self.smtp_host = os.getenv("SMTP_SERVER", "smtp.ethereal.email")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("EMAIL_USER")
        self.smtp_pass = os.getenv("EMAIL_PASS")

    def enviar_mensagem(self, destinatario, assunto, corpo):
        # Confere se o usuário e a senha realmente foram carregados
        if not self.smtp_user or not self.smtp_pass:
            raise Exception(f"Credenciais ausentes no arquivo: {env_path}")

        #  Monta o envelope do e-mail (De, Para, Assunto e Texto)
        msg = MIMEMultipart()
        msg["From"] = self.smtp_user
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain"))

        #  Conecta no servidor de e-mail, faz login e envia a mensagem
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()  # Ativa conexão criptografada (segura)
            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.smtp_user, destinatario, msg.as_string())
        return True