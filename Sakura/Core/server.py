import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from Sakura.Core.logging import logger

# HTTP SERVER FOR DEPLOYMENT
# A dummy HTTP handler for keep-alive purposes on deployment platforms
class DummyHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for keep-alive server"""

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Sakura bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass


# Starts the dummy HTTP server
def start_server() -> None:
    """Start dummy HTTP server for deployment platforms"""
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    logger.info(f"🌐 Dummy server listening on port {port}")
    server.serve_forever()

def start_server_thread() -> None:
    """Start dummy server in background thread"""
    threading.Thread(target=start_server, daemon=True).start()