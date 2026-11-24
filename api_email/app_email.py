import argparse
from pathlib import Path
import requests

# Endereço base da API EMAIL rodando na porta 5001
BASE_URL_EMAIL = "http://127.0.0.1:5001"

# Caminho do banco de auditoria onde ficam os logs de envio
DB_EMAIL_PATH = Path(__file__).resolve().parent / "instance" / "db_email.db"


# Monta o bloco extra que aparece no final da tela de ajuda (-h / --help)
def montar_epilogo():
    status_db = "encontrado" if DB_EMAIL_PATH.exists() else "não encontrado"
    return f"""
Banco de auditoria:
  DB EMAIL : {DB_EMAIL_PATH} ({status_db})
"""


def main():
    # =========================================================================
    # TELA DE AJUDA (-h / --help): o argparse cria automaticamente o -h e o
    # --help aqui e monta a tela com description, help=... e epilog.
    # =========================================================================
    parser = argparse.ArgumentParser(
        description="CLI da API EMAIL - Consulta de Logs e Teste de Envio (Porta 5001)",  # Título da tela -h / --help
        epilog=montar_epilogo(),                                                          # Rodapé da tela -h / --help (status do banco)
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Cada linha abaixo define uma opção do terminal e o texto exibido no -h / --help:
    parser.add_argument(
        "--logs",
        action="store_true",
        help="[-h/--help] Lista o histórico de envios (SUCESSO ou FALHA) gravado na API EMAIL.",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=10,
        help="[-h/--help] Quantidade máxima de registros exibidos ao listar os logs (padrão: 10).",
    )
    parser.add_argument(
        "--teste-envio",
        nargs=3,
        metavar=("EMAIL", "ASSUNTO", "MENSAGEM"),
        help="[-h/--help] Envia um e-mail de teste direto para a API EMAIL.",
    )

    args = parser.parse_args()  # Lê os argumentos e exibe a ajuda sozinho se digitar -h ou --help

    # Se rodar 'python cli_email.py' sem opção nenhuma, mostra a tela de ajuda (-h / --help)
    if not (args.logs or args.teste_envio):
        parser.print_help()  # Exibe a tela de ajuda na tela
        return

    # OPÇÃO 1 (--logs): consulta o histórico de envios na API EMAIL (GET /logs)
    if args.logs:
        try:
            resp = requests.get(f"{BASE_URL_EMAIL}/logs", timeout=10)
            resp.raise_for_status()
            logs = resp.json()[: args.limite]
            print(f"📜 Exibindo até {args.limite} registros mais recentes da API EMAIL:")
            for item in logs:
                print(
                    f"   [{item['id']}] {item['data_envio']} | {item['destinatario']} | "
                    f"{item['status']} | Assunto: {item['assunto']}"
                )
        except requests.exceptions.ConnectionError:
            print(" ERRO: A API EMAIL (porta 5001) está desligada!")
        return

    # OPÇÃO 2 (--teste-envio): manda um e-mail de teste direto para a API EMAIL (POST /disparar)
    if args.teste_envio:
        destinatario, assunto, mensagem = args.teste_envio
        payload = {
            "destinatario": destinatario,
            "assunto": assunto,
            "mensagem": mensagem,
        }
        try:
            resp = requests.post(f"{BASE_URL_EMAIL}/disparar", json=payload, timeout=15)
            dados = resp.json()
            print(f" Resultado do envio para {destinatario}: {dados.get('status')}")
            if dados.get("detalhe_erro"):
                print(f"   Detalhe: {dados.get('detalhe_erro')}")
        except requests.exceptions.ConnectionError:
            print(" ERRO: A API EMAIL (porta 5001) está desligada!")


# Executa apenas a CLI ao rodar este arquivo diretamente no terminal
if __name__ == "__main__":
    main()