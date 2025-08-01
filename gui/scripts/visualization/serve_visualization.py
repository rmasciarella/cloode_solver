#!/usr/bin/env python3
"""Simple HTTP server for viewing schedule visualizations."""

import http.server
import os
import socketserver
import sys

# Change to the output directory
output_dir = sys.argv[1] if len(sys.argv) > 1 else "output/simple_concurrent_demo"

os.chdir(output_dir)

PORT = 8888


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow loading local files
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


print(f"Serving visualization from: {os.getcwd()}")
print(f"Open your browser to: http://localhost:{PORT}")
print("Press Ctrl+C to stop the server")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
