"""Minimal SSE server: sends one counter event per second."""

import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI(title="Minimal SSE example")


async def counter_events():
    for number in range(1, 11):
        payload = json.dumps({"number": number})
        yield f"data: {payload}\n\n"
        await asyncio.sleep(1)


@app.get("/events")
async def events() -> StreamingResponse:
    return StreamingResponse(
        counter_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",  # local browser demo only
        },
    )
