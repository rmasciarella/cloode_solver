#!/usr/bin/env python3
import http.server
import os
import socketserver

os.chdir("output/high_capacity_demo")
PORT = 8080

Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server started at http://localhost:{PORT}")
    httpd.serve_forever()
