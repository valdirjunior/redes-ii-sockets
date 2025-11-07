import socket
import ssl
import base64
import os

# ==== CONFIGURAÇÕES ====
smtp_server = 'smtp.gmail.com' # Servidor de email
smtp_port = 587  # Porta para STARTTLS
meu_email = 'valdirrugiskijr@gmail.com' # Meu email
senha_app = 'mbmd ajap ipvb iozh' # Senha de app gerada
# destinatario = 'matheuswogt10@gmail.com'
# destinatario = 'paulosergiopierdona@gmail.com'
# destinatario = 'wesleylmb@gmail.com'
destinatario = 'valdirrugiskijr@gmail.com'
imagem_path = 'rede-computadores.png'

def log_envio(msg): # Print do envio
    print(">> Enviando:", msg.strip())

def log_recebido(resp): # Print da resposta
    resp = resp.replace('\r\n', '\n')
    print("<< Resposta:", resp.strip())
    print("-"*50)

# ==== ABRE O SOCKET TCP ====
print("Iniciando conexão TCP com servidor SMTP...")
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect((smtp_server, smtp_port))
recv = clientSocket.recv(1024).decode()
log_recebido(recv) # Esperado: 220

# ==== IDENTIFICAÇÃO: EHLO ====
log_envio(ehlo := 'EHLO gmail.com\r\n')
clientSocket.send(ehlo.encode())
log_recebido(clientSocket.recv(1024).decode()) # Esperado: 250

# ==== NEGOCIAÇÃO DE TLS ====
log_envio(starttls := 'STARTTLS\r\n')
clientSocket.send(starttls.encode())
log_recebido(clientSocket.recv(1024).decode()) # Esperado: 220 Ready to start TLS

# ==== HABILITA TLS/SSL SOBRE O SOCKET EXISTENTE ====
print("Estabelecendo canal seguro TLS/SSL...")
contexto = ssl.create_default_context()
cliente_ssl = contexto.wrap_socket(clientSocket, server_hostname=smtp_server)

# ==== EHLO APÓS TLS ====
log_envio(ehlo)
cliente_ssl.send(ehlo.encode())
log_recebido(cliente_ssl.recv(1024).decode()) # Esperado: 250

# ==== AUTENTICAÇÃO LOGIN EM BASE64 ====
log_envio('AUTH LOGIN')
cliente_ssl.send(b'AUTH LOGIN\r\n')
log_recebido(cliente_ssl.recv(1024).decode()) # Esperado: 334 para usuário

usuario_base64 = base64.b64encode(meu_email.encode()).decode()
log_envio(f'Base64 usuário: {usuario_base64}')
cliente_ssl.send((usuario_base64 + '\r\n').encode())
log_recebido(cliente_ssl.recv(1024).decode()) # Esperado: 334 para senha

senha_base64 = base64.b64encode(senha_app.encode()).decode()
log_envio(f'Base64 senha: {"*"*len(senha_base64)}')
cliente_ssl.send((senha_base64 + '\r\n').encode())
log_recebido(cliente_ssl.recv(1024).decode()) # Esperado: 235 Autenticação bem-sucedida

# ==== COMANDOS SMTP PADRÃO ====
log_envio(mail_from := f"MAIL FROM:<{meu_email}>\r\n")
cliente_ssl.send(mail_from.encode())
log_recebido(cliente_ssl.recv(1024).decode()) # Esperado: 250

log_envio(rcpt_to := f"RCPT TO:<{destinatario}>\r\n")
cliente_ssl.send(rcpt_to.encode())
log_recebido(cliente_ssl.recv(1024).decode()) # Esperado: 250

log_envio('DATA')
cliente_ssl.send(b"DATA\r\n")
log_recebido(cliente_ssl.recv(1024).decode()) # Esperado: 354 Start mail input

# ==== MONTAGEM DA MENSAGEM MIME MULTIPART/RELATED (HTML + IMAGEM INLINE) ====
boundary = "--------DELIMITADORA--------"
content_id = "imagem1"

# Corpo HTML referenciando a imagem pelo Content-ID
corpo_html = f"""
<html>
  <body>
    <p>Eu amo redes de computadores!</p>
    <img src="cid:{content_id}">
  </body>
</html>
"""

# Lê e codifica a imagem em base64
with open(imagem_path, "rb") as imgfile:
    img_b64 = base64.b64encode(imgfile.read()).decode()

# Monta mensagem MIME multipart/related
mensagem = f"""From: <{meu_email}>
To: <{destinatario}>
Subject: Cliente de email SMTP - Redes de Computadores 
MIME-Version: 1.0
Content-Type: multipart/related; boundary="{boundary}"

--{boundary}
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: 7bit

{corpo_html}

--{boundary}
Content-Type: image/png
Content-Transfer-Encoding: base64
Content-ID: <{content_id}>
Content-Disposition: inline; filename="{os.path.basename(imagem_path)}"

{img_b64}

--{boundary}--
\r\n.\r\n
"""

# ==== ENVIO DO CORPO DA MENSAGEM (finalize com .) ====
print(">> Enviando mensagem MIME (resumida):")
print("- HTML + imagem inline -")
cliente_ssl.send(mensagem.encode())
log_recebido(cliente_ssl.recv(1024).decode()) # Esperado: 250 OK


# ==== ENCERRA SESSÃO ====
log_envio('QUIT')
cliente_ssl.send(b'QUIT\r\n')
log_recebido(cliente_ssl.recv(1024).decode()) # Esperado: 221

# ==== FECHA O SOCKET ====
print("Sessão encerrada, socket fechado.")
cliente_ssl.close()