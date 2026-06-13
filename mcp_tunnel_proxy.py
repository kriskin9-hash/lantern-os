#!/usr/bin/env python3
"""
Simple HTTP Proxy for Lantern OS MCP Server
Exposes MCP server on a local port with proper routing
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json
from urllib.parse import urlparse, urljoin
import sys

MCP_LOCAL_URL = "http://127.0.0.1:8771"
PROXY_PORT = 9999

class MCP ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Forward to local MCP server
            full_url = urljoin(MCP_LOCAL_URL, self.path)
            response = requests.get(full_url)

            self.send_response(response.status_code)
            for header, value in response.headers.items():
                self.send_header(header, value)
            self.end_headers()

            self.wfile.write(response.content)
        except Exception as e:
            self.send_error(502, str(e))

    def do_POST(self):
        """Handle POST requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            full_url = urljoin(MCP_LOCAL_URL, self.path)
            response = requests.post(
                full_url,
                data=body,
                headers={
                    'Content-Type': self.headers.get('Content-Type', 'application/json')
                }
            )

            self.send_response(response.status_code)
            for header, value in response.headers.items():
                self.send_header(header, value)
            self.end_headers()

            self.wfile.write(response.content)
        except Exception as e:
            self.send_error(502, str(e))

    def log_message(self, format, *args):
        """Suppress verbose logging"""
        return

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PROXY_PORT), MCPProxyHandler)
    print(f"MCP Proxy listening on http://127.0.0.1:{PROXY_PORT}")
    print(f"Forwarding to {MCP_LOCAL_URL}")
    print("Press Ctrl+C to stop")
    server.serve_forever()
