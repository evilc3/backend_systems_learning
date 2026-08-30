# SSE standards

SSE is **not itself defined by an RFC**. Its normative specification is the
[WHATWG HTML Living Standard: Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html).

The transport runs over HTTP, so these IETF standards are also relevant:

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [RFC 9112: HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html)

Download offline copies from the authoritative publishers:

```bash
python docs/standards/download_standards.py
```

The downloaded documents are ignored by Git to avoid vendoring large external
standards and to ensure you deliberately fetch the current WHATWG Living
Standard.

Important SSE wire-format rules:

- Respond with `Content-Type: text/event-stream`.
- Encode text as UTF-8.
- Separate events with a blank line.
- Supported fields include `data`, `event`, `id`, and `retry`.
- A line beginning with `:` is a comment and is commonly used as a heartbeat.
- On reconnect, a client can send `Last-Event-ID`; browsers do this automatically.

