from socket import *
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
    print(">> Enviando:", msg.strip()) # strip() remove espaços em branco nas extremidades

def log_recebido(resp): # Print da resposta
    resp = resp.replace('\r\n', '\n') # \r faz com que o cursor volte ao início da linha
    print("<< Resposta:", resp.strip())
    print("-"*50)

def tratar_erro(resp, esperado, etapa):
    if resp[:3] != esperado:
        print(f'Erro na etapa {etapa}:', resp)
        exit()
    else:
        log_recebido(resp)

# ==== ABRE O SOCKET TCP ====
print("Iniciando conexão TCP com servidor SMTP...")
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((smtp_server, smtp_port))
recv = clientSocket.recv(1024).decode()
tratar_erro(recv, '220', 'conexão inicial') # 220 = Serviço pronto

# ==== ENVIA COMANDO HELO ====
log_envio(helo := 'HELO gmail.com\r\n')
clientSocket.send(helo.encode())
recv = clientSocket.recv(1024).decode()
tratar_erro(recv, '250', 'HELO') # 250 = Ação solicitada concluída

# ==== IDENTIFICAÇÃO: EHLO ====
log_envio(ehlo := 'EHLO gmail.com\r\n')
clientSocket.send(ehlo.encode())
recv = clientSocket.recv(1024).decode()
tratar_erro(recv, '250', 'EHLO pré-TLS') # 250 = Ação solicitada concluída

# ==== NEGOCIAÇÃO DE TLS ====
log_envio(starttls := 'STARTTLS\r\n')
clientSocket.send(starttls.encode())
recv = clientSocket.recv(1024).decode()
tratar_erro(recv, '220', 'STARTTLS') # 220 = Serviço pronto para iniciar TLS

# ==== HABILITA TLS/SSL SOBRE O SOCKET EXISTENTE ====
print("Estabelecendo canal seguro TLS/SSL...")
contexto = ssl.create_default_context()
cliente_ssl = contexto.wrap_socket(clientSocket, server_hostname=smtp_server) # Envelopa socket numa conexão TLS segura 

# ==== EHLO APÓS TLS ====
log_envio(ehlo) # Reenvia EHLO para reiniciar sessão SMTP segura
cliente_ssl.send(ehlo.encode())
recv = cliente_ssl.recv(1024).decode()
tratar_erro(recv, '250', 'EHLO pós-TLS') # 250 = Ação solicitada concluída

# ==== AUTENTICAÇÃO LOGIN EM BASE64 ====
log_envio('AUTH LOGIN')
cliente_ssl.send(b'AUTH LOGIN\r\n') # Envia comando para iniciar autenticação
recv = cliente_ssl.recv(1024).decode()
tratar_erro(recv, '334', 'AUTH LOGIN') # 334 = OK e solicita nome de usuário

usuario_base64 = base64.b64encode(meu_email.encode()).decode() # Codifica email em base64
log_envio(f'Base64 usuário: {usuario_base64}')
cliente_ssl.send((usuario_base64 + '\r\n').encode()) # Envia email codificado
recv = cliente_ssl.recv(1024).decode()
tratar_erro(recv, '334', 'Envio usuário') # 334 = OK e solicita senha

senha_base64 = base64.b64encode(senha_app.encode()).decode() # Codifica senha em base64
log_envio(f'Base64 senha: {"*"*len(senha_base64)}')
cliente_ssl.send((senha_base64 + '\r\n').encode()) # Envia senha codificada
recv = cliente_ssl.recv(1024).decode()
tratar_erro(recv, '235', 'Envio senha') # 235 = Autenticação bem-sucedida

# ==== COMANDOS SMTP PADRÃO ====
log_envio(mail_from := f"MAIL FROM:<{meu_email}>\r\n")
cliente_ssl.send(mail_from.encode()) # Envia endereço do remetente
recv = cliente_ssl.recv(1024).decode()
tratar_erro(recv, '250', 'MAIL FROM') # 250 = Ação solicitada concluída

log_envio(rcpt_to := f"RCPT TO:<{destinatario}>\r\n")
cliente_ssl.send(rcpt_to.encode()) # Envia endereço do destinatário
recv = cliente_ssl.recv(1024).decode()
tratar_erro(recv, '250', 'RCPT TO') # 250 = Ação solicitada concluída

# ==== INÍCIO DO ENVIO DA MENSAGEM ====
log_envio('DATA')
cliente_ssl.send(b"DATA\r\n") # Inicia o envio da mensagem, b indica que é um byte string
recv = cliente_ssl.recv(1024).decode()
tratar_erro(recv, '354', 'DATA') # 354 = Inicie a entrada do corpo da mensagem, termine com .

# ==== MONTAGEM DA MENSAGEM MIME MULTIPART ====
# MIME = Multipurpose Internet Mail Extensions
boundary = "--------DELIMITADORA--------"
content_id = "imagem1" # Content-ID para referenciar a imagem no HTML

# Corpo HTML referenciando a imagem pelo Content-ID
# f-strings permitem interpolação de variáveis diretamente na string
corpo_html = f""" 
<html>
  <body>
    <p>Eu amo redes de computadores!</p>
    <img src="cid:{content_id}">
  </body>
</html>
"""

# Lê e codifica a imagem em base64
with open(imagem_path, "rb") as imgfile: # rb = read binary
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

# ==== ENVIO DO CORPO DA MENSAGEM ====
print(">> Enviando mensagem MIME:")
cliente_ssl.send(mensagem.encode()) # Envia a mensagem completa
recv = cliente_ssl.recv(1024).decode()
tratar_erro(recv, '250', 'Envio mensagem DATA') # 250 = Ação solicitada concluída

# ==== ENCERRA SESSÃO ====
log_envio('QUIT')
cliente_ssl.send(b'QUIT\r\n') # Envia comando para encerrar a sessão
recv = cliente_ssl.recv(1024).decode()
tratar_erro(recv, '221', 'QUIT') # 221 = Encerrando conexão

# ==== FECHA O SOCKET ====
print("Sessão encerrada, socket fechado.")
cliente_ssl.close()