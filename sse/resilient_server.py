"""SSE server with event IDs, resume support, retry hints, and heartbeats."""

import asyncio
import json
from contextlib import suppress

from fastapi import FastAPI, Header, Request
from fastapi.responses import StreamingResponse

app = FastAPI(title="Resilient SSE example")


def parse_last_event_id(value: str | None) -> int:
    if not value:
        return 0
    try:
        return max(0, int(value))
    except ValueError:
        return 0


async def resilient_events(request: Request, start_after: int):
    event_id = start_after

    # Browsers use this delay before reconnecting after a dropped connection.
    yield "retry: 3000\n\n"

    try:
        while not await request.is_disconnected():
            event_id += 1
            payload = json.dumps({"event_id": event_id, "status": "ok"})
            yield f"id: {event_id}\nevent: update\ndata: {payload}\n\n"

            # A comment is a valid SSE heartbeat and is ignored by EventSource.
            yield ": heartbeat\n\n"
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        # Client disconnects normally cancel the streaming task.
        raise
    except Exception as exc:
        error = json.dumps({"message": str(exc)})
        with suppress(Exception):
            yield f"event: server-error\ndata: {error}\n\n"


@app.get("/events")
async def events(
    request: Request,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse:
    return StreamingResponse(
        resilient_events(request, parse_last_event_id(last_event_id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

