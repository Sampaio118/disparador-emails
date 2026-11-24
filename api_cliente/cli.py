import argparse
import time
from pathlib import Path
import requests
from app_cliente import app, db, Cliente, URL_API_EMAIL

# Descobre os caminhos exatos dos dois bancos de dados na pasta do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
DB_CLIENTE_PATH = BASE_DIR / "api_cliente" / "instance" / "db_cliente.db"
DB_EMAIL_PATH = BASE_DIR / "api_email" / "instance" / "db_email.db"


# Mostra no final do comando --help se os dois bancos de dados existem
def montar_epilogo():
    status_cliente = "encontrado" if DB_CLIENTE_PATH.exists() else "não encontrado"
    status_email = "encontrado" if DB_EMAIL_PATH.exists() else "não encontrado"
    return f"""
Bancos de dados:
  DB CLIENTE : {DB_CLIENTE_PATH} ({status_cliente})
  DB EMAIL   : {DB_EMAIL_PATH} ({status_email})
"""


def main():
    #  Configura todas as opções que o usuário pode digitar no terminal
    parser = argparse.ArgumentParser(
        description="CLI da API CLIENTE - Orquestrador de Comunicação",
        epilog=montar_epilogo(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--disparar", action="store_true", help="Busca clientes ativos no DB CLIENTE e envia ordem de disparo para a API EMAIL.")
    parser.add_argument("--listar", action="store_true", help="Lista todos os clientes cadastrados no DB CLIENTE.")
    parser.add_argument("--cadastrar", nargs=2, metavar=("NOME", "EMAIL"), help="Cadastra um novo cliente no DB CLIENTE.")
    parser.add_argument("--assunto", type=str, default="Comunicado Oficial", help="Define o assunto do e-mail.")
    parser.add_argument("--mensagem", type=str, default="Temos novidades exclusivas para você.", help="Define o corpo da mensagem.")
    parser.add_argument("--lote", type=int, default=2, help="Tamanho do lote de requisições para a API EMAIL (padrão: 2).")

    args = parser.parse_args()

    # Se nenhuma ação foi escolhida, mostra a ajuda na tela
    if not (args.disparar or args.listar or args.cadastrar):
        parser.print_help()
        return

    with app.app_context():
        # OPÇÃO A: listar todos os clientes do banco
        if args.listar:
            clientes = Cliente.query.all()
            print(f"📋 Total de clientes no DB CLIENTE: {len(clientes)}")
            for c in clientes:
                status = "ATIVO" if c.ativo else "INATIVO"
                print(f"   [{c.id}] {c.nome} | {c.email} | {status} | {c.criado_em}")
            return

        # OPÇÃO B: cadastrar um novo cliente pelo terminal
        if args.cadastrar:
            nome, email = args.cadastrar
            if Cliente.query.filter_by(email=email).first():
                print(f"⚠️ O e-mail {email} já está cadastrado!")
                return
            novo = Cliente(nome=nome, email=email)
            db.session.add(novo)
            db.session.commit()
            print(f"✅ Cliente '{nome}' ({email}) cadastrado no DB CLIENTE!")
            return

        # OPÇÃO C: disparar e-mails em grupinhos (lotes) para os clientes ativos
        clientes = Cliente.query.filter_by(ativo=True).all()
        total = len(clientes)
        print(f"📋 [API CLIENTE] {total} clientes ativos encontrados no DB CLIENTE.")

        # Divide a lista total em pequenos lotes (ex.: de 2 em 2)
        for i in range(0, total, args.lote):
            lote_atual = clientes[i : i + args.lote]
            print(f"\n🚀 Enviando Lote #{(i // args.lote) + 1} para a API EMAIL (Porta 5001)...")

            for cliente in lote_atual:
                payload = {
                    "destinatario": cliente.email,
                    "assunto": args.assunto,
                    "mensagem": f"Olá {cliente.nome}, {args.mensagem}"
                }
                try:
                    resp = requests.post(URL_API_EMAIL, json=payload, timeout=15)
                    print(f"   -> {cliente.email}: {resp.json().get('status')}")
                except requests.exceptions.ConnectionError:
                    print("   ❌ ERRO: A API EMAIL (porta 5001) está desligada!")
                    return

            # Dá uma pausa de 3 segundos entre um lote e outro para não sobrecarregar
            if i + args.lote < total:
                print("⏳ Aguardando 3 segundos antes do próximo lote...")
                time.sleep(3)

        print("\n✅ Processo finalizado! Verifique o db_email.db para auditoria.")


if __name__ == "__main__":
    main()