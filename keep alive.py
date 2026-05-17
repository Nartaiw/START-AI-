import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class AliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

    def log_message(self, format, *args):
        return

def run_keep_alive_server():
    # Render передает нужный порт в переменную PORT. Если её нет, используем 8080
    port = int(os.getenv("PORT", 8080))
    
    server = HTTPServer(('0.0.0.0', port), AliveHandler)
    server.serve_forever()

def keep_alive():
    """Функция для запуска сервера в фоновом потоке"""
    print("⏳ Запуск фонового веб-сервера Keep-Alive...")
    t = threading.Thread(target=run_keep_alive_server, daemon=True)
    t.start()
    print("🌐 Веб-сервер успешно инициализирован")
