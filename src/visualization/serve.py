#!/usr/bin/env python3
"""Simple HTTP server for the schedule visualization."""

import http.server
import logging
import os
import socketserver
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


# Change to the static directory
static_dir = Path(__file__).parent / "static"
os.chdir(static_dir)

PORT = 8000


class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers."""

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.end_headers()


def main() -> None:
    """Start the HTTP server."""
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        logger.info("Schedule Visualization Server")
        logger.info("============================")
        logger.info(f"Serving at: http://localhost:{PORT}")
        logger.info(f"Directory: {static_dir}")
        logger.info(f"\nOpen http://localhost:{PORT} in your browser")
        logger.info("Press Ctrl+C to stop the server")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("\nShutting down server...")
            sys.exit(0)


if __name__ == "__main__":
    main()
