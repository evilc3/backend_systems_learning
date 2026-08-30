# Backend Systems Learning

Small, runnable examples for learning backend-system concepts. The first module
demonstrates Server-Sent Events (SSE), a one-way HTTP stream from server to
client.

## SSE examples

```text
sse/
├── simple_server.py       # minimal counter stream
├── resilient_server.py    # IDs, retry hints, resume, heartbeat, error handling
├── resilient_client.py    # Python client with reconnect/backoff
├── raw_http_server.py     # SSE without FastAPI or third-party packages
└── browser_client.html    # native browser EventSource client
```

### Setup

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the minimal server

```bash
uvicorn sse.simple_server:app --reload
curl -N http://127.0.0.1:8000/events
```

Each event ends with two newlines. `curl -N` disables output buffering so each
event is visible immediately.

### Run SSE without FastAPI

This version uses only Python's standard-library HTTP primitives:

```bash
python -m sse.raw_http_server
curl -N http://127.0.0.1:8000/events
```

Read [`tutorial.md`](tutorial.md) for a line-by-line explanation of the wire
format, polling comparisons, required fields, failure handling, production
design and interview questions.

### Run the resilient example

Terminal 1:

```bash
uvicorn sse.resilient_server:app --reload
```

Terminal 2:

```bash
python -m sse.resilient_client
```

Alternatively, open `sse/browser_client.html` to use the browser's native
`EventSource` API. The examples allow any origin only to keep this local demo
simple; production services should restrict CORS to trusted origins.

Stop and restart the server. The client reconnects and sends `Last-Event-ID`,
allowing the server to resume numbering after the last event it received.

> This example resumes an event sequence, but it does not persist event data.
> Production systems usually store events in Redis Streams, Kafka, a database,
> or another durable log so missed events can be replayed.

## Standards

See [`docs/standards`](docs/standards/README.md). It explains why SSE has a
WHATWG specification rather than its own RFC and includes a script that fetches
the authoritative SSE, HTTP Semantics, and HTTP/1.1 documents.
