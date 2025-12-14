#!/usr/bin/env python3
"""
Local development server for DevSentinel frontend.
Serves the HTML/JS frontend and proxies API requests to the backend.
"""
import http.server
import socketserver
import urllib.request
import json
from pathlib import Path

PORT = 3000
API_URL = "http://localhost:8000"

class DevSentinelHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Proxy API requests to backend
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        elif self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_file = Path(__file__).parent / 'index.html'
            with open(html_file, 'rb') as f:
                self.wfile.write(f.read())
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404)
    
    def proxy_to_backend(self):
        """Proxy API requests to the backend server."""
        try:
            # Read request body for POST
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Build backend URL - keep /api prefix
            backend_url = API_URL + self.path
            
            # Create request
            req = urllib.request.Request(
                backend_url,
                data=body,
                method=self.command
            )
            
            # Copy relevant headers
            if body:
                req.add_header('Content-Type', 'application/json')
            
            # Make request to backend
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    self.send_response(response.status)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(response.read())
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(e.read())
            except urllib.error.URLError as e:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_msg = json.dumps({"error": "Backend service unavailable", "detail": str(e)})
                self.wfile.write(error_msg.encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_msg = json.dumps({"error": str(e)})
            self.wfile.write(error_msg.encode())

def start_server():
    """Start the development server."""
    Handler = DevSentinelHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n{'='*60}")
        print(f"  DevSentinel Frontend Server")
        print(f"{'='*60}")
        print(f"\n  Frontend: http://localhost:{PORT}")
        print(f"  Backend API: {API_URL}")
        print(f"\n  Press Ctrl+C to stop\n")
        print(f"{'='*60}\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)
    start_server()
