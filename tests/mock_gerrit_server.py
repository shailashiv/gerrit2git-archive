"""
Mock Gerrit Server for testing
Provides a simple HTTP server that emulates Gerrit REST API responses
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64
import threading
import time


class MockGerritHandler(BaseHTTPRequestHandler):
    """Handle mock Gerrit API requests"""
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        
        # Mock changes list (remove /a/ prefix for matching)
        path = self.path.replace('/a/', '/')
        
        if '/changes/' in path and 'q=' in path:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            changes = [
                {
                    '_number': 12345,
                    'change_id': 'I1234567890abcdef1234567890abcdef12345678',
                    'project': 'test-project',
                    'branch': 'main',
                    'subject': 'Add new feature: user authentication',
                    'status': 'MERGED',
                    'created': '2025-11-15 10:30:00.000000000',
                    'updated': '2025-11-16 14:20:00.000000000',
                    'current_revision': 'abc123',
                    'owner': {
                        'name': 'John Doe',
                        'email': 'john.doe@example.com'
                    }
                },
                {
                    '_number': 12346,
                    'change_id': 'I2234567890abcdef1234567890abcdef12345678',
                    'project': 'test-project',
                    'branch': 'develop',
                    'subject': 'Fix bug in data validation',
                    'status': 'MERGED',
                    'created': '2025-11-17 08:00:00.000000000',
                    'updated': '2025-11-18 11:30:00.000000000',
                    'current_revision': 'def456',
                    'owner': {
                        'name': 'Alice Johnson',
                        'email': 'alice.j@example.com'
                    }
                }
            ]
            
            response = ")]}'\n" + json.dumps(changes)
            self.wfile.write(response.encode())
        
        # Mock change detail
        elif '/changes/' in path and '/detail' in path:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            change = {
                '_number': 12345,
                'change_id': 'I1234567890abcdef1234567890abcdef12345678',
                'project': 'test-project',
                'branch': 'main',
                'subject': 'Add new feature: user authentication',
                'status': 'MERGED',
                'created': '2025-11-15 10:30:00.000000000',
                'updated': '2025-11-16 14:20:00.000000000',
                'current_revision': 'abc123',
                'owner': {
                    'name': 'John Doe',
                    'email': 'john.doe@example.com'
                },
                'revisions': {
                    'abc123': {
                        'commit': {
                            'message': 'Add new feature: user authentication\n\nChange-Id: I1234567890abcdef1234567890abcdef12345678',
                            'author': {
                                'name': 'John Doe',
                                'email': 'john.doe@example.com'
                            }
                        }
                    }
                },
                'labels': {
                    'Code-Review': {
                        'approved': {'name': 'Jane Smith'},
                        'all': [{'value': 2, 'name': 'Jane Smith'}]
                    }
                },
                'messages': [
                    {
                        'author': {'name': 'John Doe'},
                        'date': '2025-11-15 10:30:00.000000000',
                        'message': 'Uploaded patch set 1.'
                    }
                ]
            }
            
            response = ")]}'\n" + json.dumps(change)
            self.wfile.write(response.encode())
        
        # Mock comments
        elif '/changes/' in path and '/comments' in path:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            comments = {
                'src/auth.py': [
                    {
                        'author': {'name': 'Jane Smith'},
                        'line': 42,
                        'message': 'Consider using a stronger hash algorithm.'
                    }
                ]
            }
            
            response = ")]}'\n" + json.dumps(comments)
            self.wfile.write(response.encode())
        
        # Mock files
        elif '/changes/' in path and '/files/' in path:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            files = {
                'src/auth.py': {
                    'status': 'A',
                    'lines_inserted': 150,
                    'lines_deleted': 0
                },
                'tests/test_auth.py': {
                    'status': 'A',
                    'lines_inserted': 80,
                    'lines_deleted': 0
                }
            }
            
            response = ")]}'\n" + json.dumps(files)
            self.wfile.write(response.encode())
        
        # Mock patch
        elif '/changes/' in path and '/patch' in path:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            
            patch = """From abc123def456 Mon Sep 17 00:00:00 2001
From: John Doe <john.doe@example.com>
Date: Wed, 15 Nov 2025 10:30:00 +0000
Subject: [PATCH] Add new feature: user authentication

Change-Id: I1234567890abcdef1234567890abcdef12345678
---
 src/auth.py | 150 +++++++++++++++++++++++++++++++++
 1 file changed, 150 insertions(+)

diff --git a/src/auth.py b/src/auth.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/auth.py
@@ -0,0 +1,150 @@
+def authenticate_user(username, password):
+    pass
"""
            encoded_patch = base64.b64encode(patch.encode()).decode()
            self.wfile.write(encoded_patch.encode())
        
        else:
            self.send_response(404)
            self.end_headers()


def start_mock_server(port=8080):
    """Start the mock Gerrit server"""
    server = HTTPServer(('localhost', port), MockGerritHandler)
    print(f"Mock Gerrit server running on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


def start_mock_server_background(port=8080):
    """Start mock server in background thread"""
    def run_server():
        server = HTTPServer(('localhost', port), MockGerritHandler)
        server.serve_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(0.5)  # Give server time to start
    print(f"✓ Mock Gerrit server started on http://localhost:{port}")


if __name__ == '__main__':
    start_mock_server(8080)
