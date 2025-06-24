import http.server
import socketserver
import os

# Define a porta em que o servidor irá rodar
PORT = 8000
# Define o diretório que o servidor irá servir (nossa pasta frontend)
DIRECTORY = "frontend"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # O construtor é inicializado com o diretório que queremos servir
        super().__init__(*args, directory=DIRECTORY, **kwargs)

# Cria e inicia o servidor
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Servidor local iniciado na porta {PORT}")
    print(f"Servindo o conteúdo da pasta: '{DIRECTORY}'")
    print(f"Acesse em: http://localhost:{PORT}")
    # Mantém o servidor rodando até que seja interrompido (Ctrl+C)
    httpd.serve_forever()