import socket
import ssl
import base64
import os

# ==== CONFIGURAÇÕES ====
smtp_server = 'smtp.gmail.com'
smtp_port = 587  # Porta para STARTTLS
meu_email = 'valdirrugiskijr@gmail.com'
senha_app = 'mbmd ajap ipvb iozh'         # Gere uma senha de app nas configs do Google!
destinatario = 'paulosergiopierdona@gmail.com'
imagem_path = 'imagem.png'         # Caminho de uma imagem PNG que esteja na mesma pasta

# ==== ABRE O SOCKET TCP ====
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((smtp_server, smtp_port))
print(cliente.recv(1024).decode())  # 220 ...

# ==== IDENTIFICAÇÃO: EHLO ====
ehlo = 'EHLO exemplo.com\r\n'
cliente.send(ehlo.encode())
print(cliente.recv(1024).decode())

# ==== NEGOCIAÇÃO DE TLS ====
starttls = 'STARTTLS\r\n'
cliente.send(starttls.encode())
print(cliente.recv(1024).decode())

# ==== HABILITA TLS/SSL SOBRE O SOCKET EXISTENTE ====
contexto = ssl.create_default_context()
cliente_ssl = contexto.wrap_socket(cliente, server_hostname=smtp_server)

# ==== EHLO APÓS TLS ====
cliente_ssl.send(ehlo.encode())
print(cliente_ssl.recv(1024).decode())

# ==== AUTENTICAÇÃO LOGIN EM BASE64 ====
cliente_ssl.send(b'AUTH LOGIN\r\n')
print(cliente_ssl.recv(1024).decode())  # 334 VXNlcm5hbWU6

usuario_base64 = base64.b64encode(meu_email.encode()).decode()
cliente_ssl.send((usuario_base64 + '\r\n').encode())
print(cliente_ssl.recv(1024).decode())  # 334 UGFzc3dvcmQ6

senha_base64 = base64.b64encode(senha_app.encode()).decode()
cliente_ssl.send((senha_base64 + '\r\n').encode())
print(cliente_ssl.recv(1024).decode())  # 235 ...

# ==== COMANDOS SMTP PADRÃO ====
cliente_ssl.send(f"MAIL FROM:<{meu_email}>\r\n".encode())
print(cliente_ssl.recv(1024).decode())

cliente_ssl.send(f"RCPT TO:<{destinatario}>\r\n".encode())
print(cliente_ssl.recv(1024).decode())

cliente_ssl.send(b"DATA\r\n")
print(cliente_ssl.recv(1024).decode())

# ==== MONTAGEM DA MENSAGEM MIME (TEXTO + IMAGEM) ====
boundary = "MINHA_DELIMITADORA123"
# Corpo textual
corpo_texto = "Olá!\nEste e-mail tem texto e uma imagem em anexo, enviados pelo cliente SMTP feito do zero!\n"

# Lê e codifica a imagem em base64
with open(imagem_path, "rb") as imgfile:
    img_b64 = base64.b64encode(imgfile.read()).decode()

# Monta mensagem em formato MIME multipart (texto + anexo imagem)
mensagem = f"""From: Eu mesmo <{meu_email}>
To: Meu Destinatário <{destinatario}>
Subject: Teste SMTP com imagem (Python + sockets)
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary={boundary}

--{boundary}
Content-Type: text/plain; charset=utf-8

{corpo_texto}

--{boundary}
Content-Type: image/png; name="imagem.png"
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="imagem.png"

{img_b64}

--{boundary}--
\r\n.\r\n
"""

# ==== ENVIO DO CORPO DA MENSAGEM (finalize com .) ====
cliente_ssl.send(mensagem.encode())
print(cliente_ssl.recv(1024).decode())

# ==== ENCERRA SESSÃO ====
cliente_ssl.send(b'QUIT\r\n')
print(cliente_ssl.recv(1024).decode())

# ==== FECHA O SOCKET ====
cliente_ssl.close()
