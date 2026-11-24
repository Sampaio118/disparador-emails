from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
import requests

# Cria a aplicação da API CLIENTE e conecta no banco de clientes (db_cliente.db)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db_cliente.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Endereço da outra API (o serviço que envia os e-mails na porta 5001)
URL_API_EMAIL = "http://127.0.0.1:5001/disparar"


# Molde da tabela que guarda os clientes cadastrados
class Cliente(db.Model):
    __tablename__ = "clientes"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(
        db.String(50), default=lambda: datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )


with app.app_context():
    pass


# TELA INICIAL: abre a página visual (index.html) no navegador
@app.route("/")
def front():
    return render_template("index.html")


# LISTAR (READ): busca todos os clientes no banco e manda para a tela
@app.route("/clientes", methods=["GET"])
def listar_clientes():
    clientes = Cliente.query.all()
    return jsonify([
        {
            "id": c.id,
            "nome": c.nome,
            "email": c.email,
            "ativo": c.ativo,
            "criado_em": c.criado_em,
        }
        for c in clientes
    ])


# CADASTRAR (CREATE): salva um cliente novo no banco
@app.route("/clientes", methods=["POST"])
def criar_cliente():
    dados = request.get_json()
    nome = dados.get("nome")
    email = dados.get("email")

    # Impede salvar vazio ou duplicado
    if not nome or not email:
        return jsonify({"erro": "Nome e e-mail são obrigatórios"}), 400

    if Cliente.query.filter_by(email=email).first():
        return jsonify({"erro": "Este e-mail já está cadastrado"}), 409

    novo = Cliente(nome=nome, email=email)
    db.session.add(novo)
    db.session.commit()
    return jsonify({"mensagem": "Cliente cadastrado com sucesso!", "id": novo.id}), 201


# ATUALIZAR (UPDATE): altera dados ou liga/desliga o status ativo do cliente
@app.route("/clientes/<int:id>", methods=["PUT"])
def atualizar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    dados = request.get_json()

    cliente.nome = dados.get("nome", cliente.nome)
    cliente.email = dados.get("email", cliente.email)
    if "ativo" in dados:
        cliente.ativo = bool(dados["ativo"])

    db.session.commit()
    return jsonify({"mensagem": "Cliente atualizado com sucesso!"})


# EXCLUIR (DELETE): apaga o cliente do banco pelo ID
@app.route("/clientes/<int:id>", methods=["DELETE"])
def deletar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return jsonify({"mensagem": "Cliente removido com sucesso!"})


# DISPARAR CAMPANHA: pega só os clientes ATIVOS e manda a ordem para a API EMAIL
@app.route("/notificar-clientes", methods=["POST"])
def notificar_clientes():
    dados = request.get_json()
    assunto = dados.get("assunto")
    mensagem = dados.get("mensagem")

    #  Filtra no banco apenas quem está ativo
    clientes = Cliente.query.filter_by(ativo=True).all()
    resultados = []

    #  Para cada cliente ativo, personaliza o "Olá Nome" e envia para a porta 5001
    for c in clientes:
        payload = {
            "destinatario": c.email,
            "assunto": assunto,
            "mensagem": f"Olá {c.nome}, {mensagem}",
        }
        try:
            resp = requests.post(URL_API_EMAIL, json=payload, timeout=15)
            resultados.append(resp.json())
        except Exception as e:
            # Se a API EMAIL estiver desligada, avisa sem travar o sistema
            resultados.append({
                "destinatario": c.email,
                "status": f"Erro de comunicação com API EMAIL: {e}",
            })

    return jsonify({"total_processado": len(resultados), "detalhes": resultados})


if __name__ == "__main__":
    print(" API CLIENTE + FRONT rodando na porta 5000...")
    app.run(port=5000, debug=True)