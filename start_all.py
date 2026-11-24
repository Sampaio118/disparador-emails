import subprocess
import time
import webbrowser

#  Abre uma janela de terminal separada e liga a API EMAIL (porta 5001)
print(" Subindo API EMAIL (5001)...")
p_email = subprocess.Popen(
    ["python", "app_email.py"],
    cwd=r"C:\DISPARADOR\api_email",
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

# Espera 2 segundos para a API EMAIL terminar de ligar
time.sleep(2)

#  Abre outra janela separada e liga a API CLIENTE + Painel (porta 5000)
print(" Subindo API CLIENTE (5000)...")
p_cliente = subprocess.Popen(
    ["python", "app_cliente.py"],
    cwd=r"C:\DISPARADOR\api_cliente",
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

#  Espera 3 segundos e abre o painel automaticamente no navegador
time.sleep(3)
webbrowser.open("http://127.0.0.1:5000")
print(" Tudo iniciado!")