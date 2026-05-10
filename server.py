#!/usr/bin/env python3
"""
AHAA Local Server
Run: python server.py
Then open: http://localhost:8000
"""

import json
import os
import sys
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

# ════════════════════════════════════════════════════
#  STEP 1: PASTE YOUR ANTHROPIC API KEY BELOW
#  Get it free at: https://console.anthropic.com
#  It starts with: sk-ant-api03-...
# ════════════════════════════════════════════════════
API_KEY = "sk-ant-PASTE-YOUR-KEY-HERE"
# ════════════════════════════════════════════════════

class AHAAHandler(SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        # Only log errors, not every request
        if args[1] not in ('200', '304'):
            super().log_message(format, *args)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/chat':
            self._proxy_to_anthropic()
        else:
            self.send_error(404)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _proxy_to_anthropic(self):
        # Read request body
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, 'Bad JSON')
            return

        # Force correct model and add stream:true
        payload['model']      = 'claude-sonnet-4-20250514'
        payload['max_tokens'] = payload.get('max_tokens', 2048)
        payload['stream']     = True

        # Forward to Anthropic
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data    = json.dumps(payload).encode(),
            headers = {
                'Content-Type'      : 'application/json',
                'x-api-key'         : API_KEY,
                'anthropic-version' : '2023-06-01',
            },
            method  = 'POST',
        )

        try:
            with urllib.request.urlopen(req) as resp:
                self.send_response(200)
                self._cors()
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('X-Accel-Buffering', 'no')
                self.end_headers()

                # Stream SSE chunks directly to browser
                while True:
                    chunk = resp.read(1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()

        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            self.send_response(e.code)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(err_body.encode())
        except Exception as e:
            self.send_error(500, str(e))


if __name__ == '__main__':
    port = 8000

    print('\n' + '='*55)
    print('  AHAA — Adaptive Health Advisor Agent')
    print('='*55)

    # Check API key
    if API_KEY == 'sk-ant-PASTE-YOUR-KEY-HERE' or not API_KEY.startswith('sk-ant-'):
        print('\n  ❌ ERROR: API key not set!')
        print('\n  FIX: Open server.py in Notepad')
        print('  Change line 13 to your real key:')
        print('  API_KEY = "sk-ant-api03-YOUR-REAL-KEY"')
        print('\n  Get a free key at:')
        print('  https://console.anthropic.com')
        print('\n' + '='*55)
        print('\n  Press Enter to exit...')
        input()
        sys.exit(1)

    # Check Python version
    if sys.version_info < (3, 6):
        print(f'\n  ❌ Python {sys.version_info.major}.{sys.version_info.minor} detected.')
        print('  Python 3.6+ required.')
        print('  Download at: https://python.org/downloads')
        input('\n  Press Enter to exit...')
        sys.exit(1)

    # Change to script directory so index.html is served
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Verify index.html exists
    if not os.path.exists('index.html'):
        print('\n  ❌ ERROR: index.html not found!')
        print(f'  Make sure index.html is in the same folder as server.py')
        print(f'  Current folder: {os.getcwd()}')
        input('\n  Press Enter to exit...')
        sys.exit(1)

    print(f'\n  ✅ API key found')
    print(f'  ✅ index.html found')
    print(f'\n  🚀 Starting server...')
    print(f'  👉 Opening Chrome automatically...')
    print(f'  👉 If browser does not open, go to: http://localhost:{port}')
    print(f'\n  Keep this window open while using AHAA!')
    print(f'  Press Ctrl+C to stop the server')
    print('='*55 + '\n')

    httpd = HTTPServer(('localhost', port), AHAAHandler)

    # Auto-open browser after short delay
    import threading, webbrowser, time
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(f'http://localhost:{port}')
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n\n  👋 Server stopped. Goodbye!')
    except OSError as e:
        if 'Address already in use' in str(e) or '10048' in str(e):
            print(f'\n  ❌ Port {port} is already in use!')
            print(f'  Fix: Close any other terminal running server.py')
            print(f'  Or change port = 8000 to port = 8001 in server.py')
        else:
            print(f'\n  ❌ Server error: {e}')
        input('\n  Press Enter to exit...')
        sys.exit(1)
