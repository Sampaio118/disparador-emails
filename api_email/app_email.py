from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from email_service import DisparadorEmail

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db_email.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class LogEmail(db.Model):
    __tablename__ = "logs_envio"
    id = db.Column(db.Integer, primary_key=True)
    destinatario = db.Column(db.String(120), nullable=False)
    assunto = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    detalhe_erro = db.Column(db.Text, nullable=True)
    data_envio = db.Column(db.String(50), default=lambda: datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

with app.app_context():
    db.create_all()

disparador = DisparadorEmail()

# Única porta de entrada da API EMAIL (Motor Cego)
@app.route("/disparar", methods=["POST"])
def disparar():
    dados = request.get_json()
    destinatario = dados.get("destinatario")
    assunto = dados.get("assunto")
    corpo = dados.get("mensagem")

    if not destinatario or not assunto or not corpo:
        return jsonify({"erro": "Payload incompleto"}), 400

    try:
        disparador.enviar_mensagem(destinatario, assunto, corpo)
        status_final = "SUCESSO"
        erro_tecnico = None
        codigo_http = 200
    except Exception as e:
        status_final = "FALHA"
        erro_tecnico = str(e)
        codigo_http = 500

    # Grava exclusivamente no DB EMAIL
    log = LogEmail(
        destinatario=destinatario,
        assunto=assunto,
        status=status_final,
        detalhe_erro=erro_tecnico
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "status": status_final,
        "destinatario": destinatario,
        "detalhe_erro": erro_tecnico
    }), codigo_http

# Rota de consulta de auditoria (READ no DB EMAIL)
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