# Server-Sent Events: Developer and Interview Tutorial

## 1. What is SSE?

Server-Sent Events (SSE) is a standard way for a server to keep an HTTP
response open and continuously send text events to a client.

The communication direction is one-way:

```text
Client -- normal HTTP request --> Server
Client <-- continuous events ---- Server
```

The client makes one HTTP `GET` request. Instead of completing the response
after one body, the server sends multiple event blocks over the same response.

An SSE response uses the media type `text/event-stream`:

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

id: 1
event: order-updated
data: {"order_id": 42, "status": "shipped"}

id: 2
event: order-updated
data: {"order_id": 43, "status": "delivered"}

```

The blank line after each event is important: it tells the client that the
event is complete.

SSE is defined by the WHATWG HTML Living Standard, not by a dedicated RFC. It
runs over HTTP, whose semantics and HTTP/1.1 message rules are defined by RFC
9110 and RFC 9112.

## 2. Why was SSE required?

Traditional HTTP is client-driven: a client requests data and the server
returns a response. This is inefficient when data changes unpredictably and the
client needs updates quickly.

Before streaming approaches, clients repeatedly polled the server:

```text
GET /status -> no change
GET /status -> no change
GET /status -> changed
```

Polling creates requests even when nothing has changed. SSE allows the server
to push an update immediately while retaining normal HTTP behavior.

SSE fills the gap between polling and WebSockets:

- It provides real-time server-to-client updates.
- It is simpler than a bidirectional WebSocket protocol.
- It works with normal HTTP authentication, URLs and infrastructure.
- Browsers provide the native `EventSource` API, including reconnection.
- Event IDs allow a reconnecting client to request continuation.

## 3. Where is SSE used?

SSE is useful when most communication flows from the server to the client:

- LLM token streaming and agent-progress updates
- Notifications and activity feeds
- Job, upload or report progress
- CI/CD build logs
- Monitoring dashboards and live metrics
- Order, payment or delivery status
- Sports scores and news feeds
- Changes to collaborative documents when client writes use normal HTTP

Learning SSE is important because streaming is now common in AI and backend
systems. It teaches long-lived HTTP connections, incremental delivery,
buffering, disconnect detection, retry behavior, idempotency and backpressure.

Do not choose SSE when the client must continuously send messages over the same
connection, such as multiplayer games, voice calls or high-frequency chat.
WebSockets are usually a better fit for those cases.

## 4. SSE vs polling and long polling

| Property | Polling | Long polling | SSE |
|---|---|---|---|
| Connection | New request at a fixed interval | Request waits until an update or timeout | One long-lived response |
| Delivery latency | Up to the polling interval | Usually low | Usually low |
| Empty requests | Many | Fewer | Normally none |
| Server-to-client updates | One response per request | One update per request | Many events per response |
| Browser API | `fetch`/XHR and timers | `fetch`/XHR and retry logic | Native `EventSource` |
| Reconnection | Application code | Application code | Built into `EventSource` |
| Resume support | Application-specific | Application-specific | `id` and `Last-Event-ID` |
| Direction | Request/response | Request/response | Server to client |
| Infrastructure complexity | Low | Medium | Medium |

### Polling

```javascript
setInterval(async () => {
  const status = await fetch("/status").then(response => response.json());
  render(status);
}, 5000);
```

Polling is suitable when updates are infrequent and a delay of several seconds
is acceptable. It is stateless and easy to scale, but wastes requests and can
either increase latency or overload the server if the interval is too short.

### Long polling

The client sends a request and the server holds it until data becomes available
or a timeout occurs. After receiving a response, the client immediately creates
another request.

Long polling works where streaming responses are unavailable, but every update
still involves request/response overhead and reconnect logic.

### SSE

SSE is preferable when updates should arrive quickly, are text-based, and flow
primarily from server to client. Unlike polling, one response can contain an
unbounded sequence of events.

## 5. Required HTTP and SSE fields

### Request

A minimal browser request conceptually looks like this:

```http
GET /events HTTP/1.1
Host: example.com
Accept: text/event-stream
Last-Event-ID: 125
```

| Request field | Required? | Purpose |
|---|---:|---|
| `GET /events` | Yes | Opens the event stream. SSE endpoints conventionally use `GET`. |
| `Accept: text/event-stream` | Recommended | Tells the server which representation the client expects. |
| `Last-Event-ID` | Optional | Contains the last processed event ID after a reconnect so the server can resume or replay. Browsers manage it automatically when the stream uses `id`. |
| `Authorization` or cookie | Application-specific | Authenticates the stream. Native `EventSource` cannot set arbitrary request headers, so cookie authentication or a fetch-based SSE client may be required. |
| `Cache-Control: no-cache` | Optional request hint | Requests revalidation rather than a cached event stream. Correct response and proxy configuration matter more. |

### Response headers

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

| Response field | Required? | Purpose |
|---|---:|---|
| `200 OK` | Yes for an accepted stream | Indicates that the stream opened successfully. |
| `Content-Type: text/event-stream` | Yes | Makes the response an SSE event stream. |
| UTF-8 body encoding | Yes | The event stream is decoded as UTF-8. |
| `Cache-Control: no-cache` | Strongly recommended | Prevents caches from serving an old or stored stream. |
| `Connection: keep-alive` | Usually implicit | Expresses long-lived HTTP/1.1 intent. It is a hop-by-hop header and must not be sent with HTTP/2. |
| `X-Accel-Buffering: no` | Proxy-specific | Tells Nginx not to buffer incremental output. It is not part of the SSE standard. |
| `Access-Control-Allow-Origin` | Cross-origin only | Allows an approved web origin to open the stream. Use a restricted origin in production. |

Do not set `Content-Length`, because the complete response size is not known
when the stream begins. HTTP/1.1 will normally use chunked transfer coding;
HTTP/2 and HTTP/3 use their own framing.

### Event-stream fields

An event is a sequence of lines terminated by a blank line:

```text
id: 126
event: payment-status
retry: 5000
data: {"payment_id":"p-1","status":"complete"}

```

| Event field | Required? | Purpose |
|---|---:|---|
| `data` | Required for a useful message | Contains event data. Multiple consecutive `data:` lines are joined with newline characters. |
| `event` | Optional | Names the event. Without it, browsers dispatch a normal `message` event. |
| `id` | Optional, recommended | Sets the last event ID. The browser sends it as `Last-Event-ID` when reconnecting. IDs should be stable and ordered within the chosen replay model. |
| `retry` | Optional | Sets the browser reconnection delay in milliseconds. It must contain an integer. |
| `: comment` | Optional | Ignored by clients. Commonly sent as a heartbeat to keep intermediaries and idle-timeout detectors active. |
| Blank line | Yes | Dispatches the accumulated event. Without it, the client continues waiting. |

SSE has no built-in JSON requirement. `data` is text; JSON is merely a common
application-level encoding.

## 6. Coding SSE without FastAPI `StreamingResponse`

`StreamingResponse` does not create the SSE protocol. It helps FastAPI send
response-body chunks without buffering the entire response. The same protocol
can be implemented with Python's standard-library HTTP server by writing and
flushing bytes directly:

```python
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class SSEHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        if self.path != "/events":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        last_id = self.headers.get("Last-Event-ID", "0")
        try:
            event_id = int(last_id)
        except ValueError:
            event_id = 0

        try:
            while True:
                event_id += 1
                data = json.dumps({"count": event_id})
                event = f"id: {event_id}\nevent: count\ndata: {data}\n\n"
                self.wfile.write(event.encode("utf-8"))
                self.wfile.flush()  # send now instead of waiting in a buffer
                time.sleep(1)
        except (BrokenPipeError, ConnectionResetError):
            # The browser closed the tab or otherwise disconnected.
            pass


server = ThreadingHTTPServer(("127.0.0.1", 8000), SSEHandler)
server.serve_forever()
```

This demonstrates the essential work hidden by a framework:

1. Keep the HTTP response open.
2. Set `Content-Type: text/event-stream`.
3. Format events as UTF-8 lines.
4. End each event with a blank line.
5. Flush output so events are delivered immediately.
6. Detect and clean up disconnected clients.

The standard-library server is educational, not a recommended production
server. Production code should use an asynchronous server or a proven streaming
stack so each open client does not occupy a dedicated OS thread.

## 7. Client example

```javascript
const source = new EventSource("/events");

source.onopen = () => console.log("stream connected");

source.onmessage = event => {
  console.log("default event", event.data, event.lastEventId);
};

source.addEventListener("payment-status", event => {
  const payment = JSON.parse(event.data);
  console.log(payment.status);
});

source.onerror = () => {
  // EventSource normally reconnects automatically. This callback does not
  // necessarily mean the stream has permanently failed.
  console.log("stream interrupted; waiting for reconnect");
};

// Call this when the page no longer needs updates.
source.close();
```

`EventSource.readyState` can be:

- `EventSource.CONNECTING` (`0`)
- `EventSource.OPEN` (`1`)
- `EventSource.CLOSED` (`2`)

## 8. Error cases and solutions

### 8.1 Server stalls but the TCP connection remains open

This is more subtle than a clean disconnect. The browser may see an open socket
and therefore will not reconnect, even though no useful data is arriving.

Server solution:

- Send comment heartbeats such as `: heartbeat\n\n` every 15-30 seconds.
- Avoid blocking work inside the stream writer.
- Monitor event-loop lag and stream-delivery latency.

Client solution:

- Native `EventSource` has no configurable read timeout.
- Track the time of the last event or heartbeat at the application level.
- If it exceeds a chosen threshold, call `source.close()` and create a new
  `EventSource`.
- Add randomized delay to manual reconnections so many clients do not reconnect
  simultaneously.

If heartbeats are comments, native `EventSource` does not expose them to
JavaScript. Send a named `heartbeat` event when client-side stall detection is
required.

### 8.2 Network disconnect or server restart

The browser automatically attempts to reconnect. The server should emit event
IDs and use the incoming `Last-Event-ID` to replay events after that ID.

Event IDs alone do not provide replay. The server needs a durable or retained
event log, such as Redis Streams, Kafka or a database.

### 8.3 Duplicate events after reconnect

A connection may break after the client receives an event but before delivery
state is known elsewhere. At-least-once replay can therefore produce duplicates.

Solution:

- Make event handling idempotent.
- Store the highest processed event ID per logical stream.
- Ignore already processed IDs.
- Never use delivery of an SSE event alone as proof that a financial or other
  critical action occurred.

### 8.4 Events are missing after reconnect

Causes include no replay store, expired history, invalid IDs or connecting to a
server instance that cannot access the same event log.

Solution:

- Store events in shared durable storage.
- Define a retention period.
- If an ID is too old, send a reset/snapshot event or return a response that
  tells the client to reload current state.
- Treat the normal REST API as the source of truth and SSE as change
  notification when full replay is unnecessary.

### 8.5 Proxy buffers events

The application writes events, but the proxy waits for a larger buffer before
forwarding them. The client receives several events at once.

Solution:

- Disable response buffering for the SSE route.
- Disable transformations/compression when they cause buffering.
- Use `X-Accel-Buffering: no` for a compatible Nginx configuration.
- Test through the real load balancer and CDN, not only on localhost.

### 8.6 Proxy, load balancer or firewall closes idle streams

Solution:

- Send heartbeats more frequently than the shortest infrastructure idle
  timeout.
- Configure appropriate upstream and downstream read timeouts.
- Allow automatic reconnection and replay.

### 8.7 Slow client and backpressure

If a client reads more slowly than events are generated, per-client buffers can
grow until the server runs out of memory.

Solution:

- Bound every client queue.
- Coalesce replaceable events, such as sending only the newest progress value.
- Disconnect clients that remain too slow.
- Put durable events in a log and let reconnecting clients catch up.
- Measure queue depth and dropped/disconnected clients.

### 8.8 Too many open connections

Every SSE client consumes a socket and server/proxy resources. HTTP/1.1 browsers
also have low per-origin connection limits; HTTP/2 multiplexing improves this.

Solution:

- Use an asynchronous server.
- Tune file-descriptor and connection limits.
- Prefer one SSE connection carrying multiple event types rather than many
  connections per page.
- Capacity-test the application and every intermediary.

### 8.9 Authentication expires while streaming

An already-open connection may continue even after its token expires, depending
on server policy. Native `EventSource` also cannot attach a custom bearer header.

Solution:

- Prefer secure, same-site, HTTP-only cookies for browser `EventSource`, or use
  a fetch-based SSE parser when authorization headers are required.
- Validate authorization when opening the stream.
- Define whether long streams must be periodically reauthorized.
- Close the stream when access is revoked.
- Never place long-lived secrets in query strings because URLs are commonly
  logged.

### 8.10 Server sends malformed events

Examples include missing blank lines, invalid UTF-8 expectations, a non-integer
`retry`, or JSON that the application cannot parse.

Solution:

- Centralize event serialization.
- Escape data by writing each logical line as its own `data:` line.
- Validate application payload schemas.
- Handle JSON parsing errors without terminating all future event processing.

### 8.11 Server returns an HTTP error

Authentication failures, rate limits and server errors can cause reconnect
loops. Native `EventSource` exposes limited status information to JavaScript.

Solution:

- Authenticate or validate parameters before starting the `200` stream.
- Use suitable HTTP error statuses before response headers are committed.
- Prevent infinite aggressive retries for permanent failures.
- If clients need detailed control over status codes and retry policy, use
  `fetch` with an SSE parser instead of native `EventSource`.

After a server sends `200 OK` and begins the body, it cannot change that response
to `500`. It can send an application-level `event: server-error`, then close the
stream, but the HTTP response itself remains `200`.

### 8.12 Deployment during active streams

Solution:

- Stop accepting new streams on the draining instance.
- Allow existing streams a grace period, then close them.
- Ensure clients reconnect to another instance.
- Keep replay state outside individual application instances.

### 8.13 Reconnection storm

If a service or network recovers, thousands of clients may reconnect at once.

Solution:

- Use exponential backoff with jitter in custom clients.
- Send a reasonable `retry` value.
- Rate-limit connection establishment carefully.
- Scale connection handlers independently where appropriate.

### 8.14 Multi-instance ordering problems

Different servers can produce conflicting or out-of-order IDs.

Solution:

- Generate IDs in the shared log rather than inside each web process.
- Define whether ordering is global, per user or per topic.
- Route all instances through the same event system.

## 9. Production checklist

- [ ] `Content-Type` is `text/event-stream`.
- [ ] Every event ends with a blank line.
- [ ] Events are UTF-8 encoded and flushed promptly.
- [ ] Proxy buffering is disabled for the route.
- [ ] Heartbeat interval is shorter than infrastructure idle timeouts.
- [ ] Event IDs and replay behavior are defined.
- [ ] Duplicate processing is safe.
- [ ] Slow-client queues are bounded.
- [ ] Authentication and CORS are restricted appropriately.
- [ ] Deployments drain or safely disconnect streams.
- [ ] Reconnection uses delay/jitter and cannot create a retry storm.
- [ ] Open connections, stream age, queue depth, disconnects, reconnects and
      event-delivery latency are observable.
- [ ] Behavior is tested through the production proxy/load balancer/CDN.

## 10. Common interview questions

### Is SSE a protocol separate from HTTP?

No. It is a standardized event-stream format and browser API transported in a
long-lived HTTP response.

### Is SSE bidirectional?

No. The stream is server-to-client. The client can send separate normal HTTP
requests back to the server.

### SSE or WebSockets?

Choose SSE for text-based, mainly server-to-client updates where HTTP semantics
and automatic browser reconnection are valuable. Choose WebSockets when both
sides need frequent messages, binary frames or lower-level full-duplex control.

### Does SSE guarantee delivery?

No. `id` and `Last-Event-ID` provide building blocks for resumption. Delivery
guarantees depend on retained events, replay rules and idempotent client logic.

### What delivery model is common?

At-least-once delivery is practical when events are retained and replayed.
Duplicates must be expected. Exactly-once end-to-end delivery is not supplied by
SSE.

### How does a browser reconnect?

When the connection closes unexpectedly, `EventSource` waits for its
reconnection delay and opens a new request. If an `id` was received, it sends
that value in `Last-Event-ID`.

### Why are heartbeats needed?

They prevent idle intermediaries from closing healthy connections and help
applications detect streams that are open but no longer delivering data.

### What is the role of `StreamingResponse`?

It is a framework abstraction that sends iterable or asynchronous-iterable
chunks without buffering the whole response. The application must still create
valid SSE fields, delimit events, handle cancellation and design replay.

### How do you scale SSE?

Use asynchronous connection handling, shared pub/sub or durable event storage,
bounded per-client queues, proxy configurations that support streaming, and a
replay strategy that does not depend on one server instance.

### Can SSE carry binary data?

Not directly; its stream is UTF-8 text. Binary data must be encoded, for example
with Base64, which adds overhead. WebSockets or ordinary object downloads are
usually better for significant binary traffic.

### Why might events arrive in batches?

The application, compression layer, reverse proxy, CDN or client library may be
buffering the response. Flushing application output alone is not sufficient if
an intermediary still buffers it.

## 11. Authoritative references

- WHATWG HTML Living Standard, Server-sent events:
  <https://html.spec.whatwg.org/multipage/server-sent-events.html>
- RFC 9110, HTTP Semantics: <https://www.rfc-editor.org/rfc/rfc9110.html>
- RFC 9112, HTTP/1.1: <https://www.rfc-editor.org/rfc/rfc9112.html>

