import socket
import os
from urllib.parse import urlparse

# Definindo a porta que o proxy irá escutar
PORT = 8888
# Definindo o diretório onde o cache será armazenado
CACHE_DIR = "cache"

# Cria o diretório caso ele não existir na mesma pasta do script 
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Cria o socket para o servidor proxy
proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Configura o socket para permitir reutilizar o endereço
proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Associa o socket à porta e ao endereço de escuta
proxy_socket.bind(("localhost", PORT))
# Coloca o socket em modo de escuta para aceitar conexões
proxy_socket.listen(5)
print(f"Servidor proxy iniciado e aguardando conexões na porta {PORT}...")

# Inicia um loop para aceitar conexões de clientes
while True:
    # Aceita a conexão de um cliente
    client_socket, client_address = proxy_socket.accept()
    print(f"Conexão estabelecida com {client_address}")

    try:
        # Recebe a requisição do cliente (até 4096 bytes)
        request = client_socket.recv(4096).decode('utf-8')
        print(f"Requisição recebida:\n{request}\n")

        # Extrai a primeira linha da requisição HTTP (método, URL, e versão)
        first_line = request.split("\r\n")[0]
        method, full_path, _ = first_line.split()

        # Verifica se o método HTTP é GET, caso contrário, retorna erro
        if method != "GET":
            client_socket.sendall(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
            client_socket.close()
            continue

        # Verifica se a URL começa com "/http://" ou "/https://"
        if full_path.startswith("/http://") or full_path.startswith("/https://"):
            # Remove o prefixo "/http://" ou "/https://"
            full_url = full_path[1:]  # Remove a primeira barra "/"
        else:
            # Se não começar com os prefixos esperados, retorna erro
            client_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            client_socket.close()
            continue

        # Analisa a URL para obter componentes como hostname e path
        parsed_url = urlparse(full_url)
        hostname = parsed_url.hostname
        path = parsed_url.path if parsed_url.path else "/"

        # Se não conseguir extrair o hostname, retorna erro
        if not hostname:
            client_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            client_socket.close()
            continue

        # Define o nome do arquivo de cache com base no hostname e path
        cache_filename = os.path.join(CACHE_DIR, hostname + path.replace("/", "_"))

        # Verifica se o arquivo existe no cache
        if os.path.exists(cache_filename):
            print("Servindo do cache...")
            # Abre o arquivo em cache e envia ao cliente
            with open(cache_filename, "rb") as cached_file:
                cached_data = cached_file.read()
                client_socket.sendall(cached_data)
            client_socket.close()
            continue

        # Cria um novo socket para se conectar ao servidor remoto
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Conecta-se ao servidor remoto no endereço e porta HTTP (80)
        server_socket.connect((hostname, 80))

        # Cria a requisição HTTP a ser enviada ao servidor remoto
        server_request = f"GET {path} HTTP/1.1\r\nHost: {hostname}\r\nConnection: close\r\n\r\n"
        # Envia a requisição HTTP para o servidor remoto
        server_socket.sendall(server_request.encode('utf-8'))

        # Inicializa uma variável para armazenar a resposta do servidor
        server_response = b""
        # Recebe a resposta do servidor remoto em pedaços de até 4096 bytes
        while True:
            chunk = server_socket.recv(4096)
            if not chunk:
                break
            server_response += chunk
        server_socket.close()

        # Salva a resposta no cache para futuras requisições
        with open(cache_filename, "wb") as cache_file:
            cache_file.write(server_response)

        # Envia a resposta do servidor remoto para o cliente
        client_socket.sendall(server_response)
        client_socket.close()

    except Exception as e:
        # Se ocorrer algum erro, envia resposta de erro para o cliente
        print(f"Erro: {e}")
        client_socket.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
        client_socket.close()