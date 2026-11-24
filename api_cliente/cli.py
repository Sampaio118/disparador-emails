import argparse
import time
from pathlib import Path
import requests
from app_cliente import app, db, Cliente, URL_API_EMAIL

# Descobre os caminhos exatos dos dois bancos de dados na pasta do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
DB_CLIENTE_PATH = BASE_DIR / "api_cliente" / "instance" / "db_cliente.db"
DB_EMAIL_PATH = BASE_DIR / "api_email" / "instance" / "db_email.db"


# Monta o bloco extra que aparece no final da tela de ajuda (-h / --help)
def montar_epilogo():
    status_cliente = "encontrado" if DB_CLIENTE_PATH.exists() else "não encontrado"
    status_email = "encontrado" if DB_EMAIL_PATH.exists() else "não encontrado"
    return f"""
Bancos de dados:
  DB CLIENTE : {DB_CLIENTE_PATH} ({status_cliente})
  DB EMAIL   : {DB_EMAIL_PATH} ({status_email})
"""


def main():
    # =========================================================================
    # TELA DE AJUDA (-h / --help): o argparse cria automaticamente o -h e o
    # --help aqui e junta tudo o que está em description, help=... e epilog.
    # =========================================================================
    parser = argparse.ArgumentParser(
        description="CLI da API CLIENTE - Orquestrador de Comunicação",  # Título da tela -h / --help
        epilog=montar_epilogo(),                                         # Rodapé da tela -h / --help (status dos bancos)
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Cada linha abaixo define um comando do terminal e o texto que aparece no -h / --help:
    parser.add_argument("--disparar", action="store_true", help="[-h/--help] Busca clientes ativos no DB CLIENTE e envia ordem de disparo para a API EMAIL.")
    parser.add_argument("--listar", action="store_true", help="[-h/--help] Lista todos os clientes cadastrados no DB CLIENTE.")
    parser.add_argument("--cadastrar", nargs=2, metavar=("NOME", "EMAIL"), help="[-h/--help] Cadastra um novo cliente no DB CLIENTE.")
    parser.add_argument("--assunto", type=str, default="Comunicado Oficial", help="[-h/--help] Define o assunto do e-mail.")
    parser.add_argument("--mensagem", type=str, default="Temos novidades exclusivas para você.", help="[-h/--help] Define o corpo da mensagem.")
    parser.add_argument("--lote", type=int, default=2, help="[-h/--help] Tamanho do lote de requisições para a API EMAIL (padrão: 2).")

    args = parser.parse_args()  # Lê o que foi digitado e responde sozinho se o usuário pediu -h ou --help

    # Se o usuário rodar 'python cli.py' sem passar nenhuma opção, exibe a mesma tela de ajuda (-h / --help)
    if not (args.disparar or args.listar or args.cadastrar):
        parser.print_help()  # Exibe a tela de ajuda na tela
        return

    with app.app_context():
        # OPÇÃO 1 (--listar): busca e mostra todos os clientes salvos no banco
        if args.listar:
            clientes = Cliente.query.all()
            print(f" Total de clientes no DB CLIENTE: {len(clientes)}")
            for c in clientes:
                status = "ATIVO" if c.ativo else "INATIVO"
                print(f"   [{c.id}] {c.nome} | {c.email} | {status} | {c.criado_em}")
            return

        # OPÇÃO 2 (--cadastrar NOME EMAIL): cadastra um novo cliente evitando e-mail repetido
        if args.cadastrar:
            nome, email = args.cadastrar
            if Cliente.query.filter_by(email=email).first():
                print(f" O e-mail {email} já está cadastrado!")
                return
            novo = Cliente(nome=nome, email=email)
            db.session.add(novo)
            db.session.commit()
            print(f"Cliente '{nome}' ({email}) cadastrado no DB CLIENTE!")
            return

        # OPÇÃO 3 (--disparar): envia e-mails em lotes apenas para quem está ATIVO
        clientes = Cliente.query.filter_by(ativo=True).all()
        total = len(clientes)
        print(f" [API CLIENTE] {total} clientes ativos encontrados no DB CLIENTE.")

        # Divide os clientes ativos em grupos do tamanho definido em --lote (padrão 2)
        for i in range(0, total, args.lote):
            lote_atual = clientes[i : i + args.lote]
            print(f"\n Enviando Lote #{(i // args.lote) + 1} para a API EMAIL (Porta 5001)...")

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
                    print("    ERRO: A API EMAIL (porta 5001) está desligada!")
                    return

            # Pausa de 3 segundos entre os lotes para não sobrecarregar o envio
            if i + args.lote < total:
                print(" Aguardando 3 segundos antes do próximo lote...")
                time.sleep(3)

        print("\n Processo finalizado! Verifique o db_email.db para auditoria.")


if __name__ == "__main__":
    main()