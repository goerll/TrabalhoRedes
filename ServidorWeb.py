import socket

# Configuração do servidor
# Cria um socket TCP (socket.AF_INET) para comunicação de rede
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Define a porta que o servidor irá escutar
port = 6789
# Associa o socket a um endereço IP e porta específicos (nesse caso,
# o servidor escuta em todas as interfaces de rede na porta 6789)
server.bind(("", port))
# Coloca o servidor em modo de escuta
server.listen(1)
print(f"Servidor rodando na porta {port}...")

while True:
    try:
        # Aceita uma nova conexão de um cliente
        # Retorna um novo socket para a comunicação com o cliente
        # e o endereço do cliente
        client_connection, client_address = server.accept()
        print(f"Cliente conectado: {client_address}")

        # Recebe a requisição do cliente
        # A função recv() recebe até 1024 bytes da conexão
        request = client_connection.recv(1024).decode()

        # Extrai a primeira linha da requisição, que contém o método HTTP
        # e o caminho do recurso solicitado
        lines = request.split("\n")
        first_line = lines[0]
        file = first_line.split()[1]

        # Se o arquivo solicitado for a raiz ("/"), serve o arquivo index.html
        if file == "/":
            file = "/index.html"
        # Remove a barra inicial do caminho do arquivo
        file = file[1:]

        print(f"Arquivo pedido: {file}")

        try:
            # Tenta abrir o arquivo solicitado em modo binário (rb)
            with open(file, "rb") as f:
                content = f.read()

            # Cria o cabeçalho da resposta HTTP
            # O cabeçalho indica o status da requisição (200 OK),
            # o tipo de conteúdo (HTML ou texto plano) e o tamanho do conteúdo
            header = "HTTP/1.1 200 OK\n"
            if file.endswith(".html"):
                header += "Content-Type: text/html\n"
            else:
                header += "Content-Type: text/plain\n"
            header += f"Content-Length: {len(content)}\n\n"

            # Combina o cabeçalho e o conteúdo do arquivo em uma única resposta
            response = header.encode() + content

        except FileNotFoundError:
            # Se o arquivo não for encontrado, envia uma resposta de erro 404
            message = "<!DOCTYPE html><html><head><meta charset='UTF-8'></head><body><h1>Erro 404 - Arquivo não encontrado</h1></body></html>"
            header = "HTTP/1.1 404 Not Found\n"
            header += "Content-Type: text/html\n"
            header += f"Content-Length: {len(message)}\n\n"
            response = (header + message).encode()

        # Envia a resposta para o cliente
        client_connection.send(response)
        # Fecha a conexão com o cliente
        client_connection.close()

    except Exception as e:
        print(f"Erro: {e}")
        continue
