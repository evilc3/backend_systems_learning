"""Educational SSE server using only Python's standard HTTP primitives."""

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class SSEHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/events":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")  # local demo only
        self.end_headers()

        try:
            event_id = max(0, int(self.headers.get("Last-Event-ID", "0")))
        except ValueError:
            event_id = 0

        try:
            self._send("retry: 3000\n\n")
            while True:
                event_id += 1
                data = json.dumps({"count": event_id})
                self._send(
                    f"id: {event_id}\n"
                    "event: count\n"
                    f"data: {data}\n\n"
                )
                time.sleep(1)
        except (BrokenPipeError, ConnectionResetError):
            # Expected when the browser closes or the network disappears.
            return

    def _send(self, event: str) -> None:
        self.wfile.write(event.encode("utf-8"))
        self.wfile.flush()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), SSEHandler)
    print("SSE stream: http://127.0.0.1:8000/events")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()

