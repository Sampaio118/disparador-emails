import subprocess
import time
import webbrowser

print("🚀 Subindo API EMAIL (5001)...")
p_email = subprocess.Popen(
    ["python", "app_email.py"],
    cwd=r"C:\DISPARADOR\api_email",
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

time.sleep(2)

print("🚀 Subindo API CLIENTE (5000)...")
p_cliente = subprocess.Popen(
    ["python", "app_cliente.py"],
    cwd=r"C:\DISPARADOR\api_cliente",
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)

time.sleep(3)
webbrowser.open("http://127.0.0.1:5000")
print("✅ Tudo iniciado!")