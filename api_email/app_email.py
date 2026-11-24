from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from email_service import DisparadorEmail

# Cria a aplicação da API EMAIL e conecta no banco exclusivo de histórico (db_email.db)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db_email.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Molde da tabela que guarda o histórico de cada e-mail enviado
class LogEmail(db.Model):
    __tablename__ = "logs_envio"
    id = db.Column(db.Integer, primary_key=True)
    destinatario = db.Column(db.String(120), nullable=False)
    assunto = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(30), nullable=False)       # SUCESSO ou FALHA
    detalhe_erro = db.Column(db.Text, nullable=True)        # Motivo do erro, se falhar
    data_envio = db.Column(db.String(50), default=lambda: datetime.now().strftime("%d/%m/%Y %H:%M:%S"))


# Cria a tabela automaticamente no banco se ela ainda não existir
with app.app_context():
    db.create_all()

# Prepara o motor que envia os e-mails de verdade
disparador = DisparadorEmail()


# ROTA DE ENVIO: recebe a ordem da API CLIENTE, envia o e-mail e grava o resultado
@app.route("/disparar", methods=["POST"])
def disparar():
    # 1. Lê os dados enviados (para quem, assunto e mensagem)
    dados = request.get_json()
    destinatario = dados.get("destinatario")
    assunto = dados.get("assunto")
    corpo = dados.get("mensagem")

    # 2. Barra o pedido se estiver faltando alguma informação
    if not destinatario or not assunto or not corpo:
        return jsonify({"erro": "Payload incompleto"}), 400

    # 3. Tenta enviar o e-mail e anota se deu certo ou se deu erro
    try:
        disparador.enviar_mensagem(destinatario, assunto, corpo)
        status_final = "SUCESSO"
        erro_tecnico = None
        codigo_http = 200
    except Exception as e:
        status_final = "FALHA"
        erro_tecnico = str(e)
        codigo_http = 500

    # 4. Salva o comprovante do envio no banco db_email.db para auditoria
    log = LogEmail(
        destinatario=destinatario,
        assunto=assunto,
        status=status_final,
        detalhe_erro=erro_tecnico
    )
    db.session.add(log)
    db.session.commit()

    # 5. Responde para quem pediu dizendo se foi enviado ou se falhou
    return jsonify({
        "status": status_final,
        "destinatario": destinatario,
        "detalhe_erro": erro_tecnico
    }), codigo_http


# ROTA DE AUDITORIA: mostra todo o histórico de envios (do mais recente para o mais antigo)
@app.route("/logs", methods=["GET"])
def listar_logs():
    logs = LogEmail.query.order_by(LogEmail.id.desc()).all()
    return jsonify([
        {
            "id": l.id,
            "destinatario": l.destinatario,
            "assunto": l.assunto,
            "status": l.status,
            "detalhe_erro": l.detalhe_erro,
            "data_envio": l.data_envio
        }
        for l in logs
    ])


if __name__ == "__main__":
    print("⚙️ API EMAIL (Motor Cego) rodando na porta 5001...")
    app.run(port=5001, debug=True)