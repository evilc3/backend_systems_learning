"""Python SSE client with resume support and bounded exponential backoff."""

import argparse
import random
import time

import httpx


def consume(url: str) -> None:
    last_event_id: str | None = None
    retry_seconds = 1.0

    while True:
        headers = {"Accept": "text/event-stream"}
        if last_event_id:
            headers["Last-Event-ID"] = last_event_id

        try:
            with httpx.stream(url=url, method="GET", headers=headers, timeout=None) as response:
                response.raise_for_status()
                retry_seconds = 1.0
                event: dict[str, list[str] | str] = {"data": []}

                for line in response.iter_lines():
                    if line == "":
                        if event["data"]:
                            print(
                                {
                                    "id": event.get("id"),
                                    "event": event.get("event", "message"),
                                    "data": "\n".join(event["data"]),
                                }
                            )
                        event = {"data": []}
                        continue

                    if line.startswith(":"):
                        continue

                    field, _, value = line.partition(":")
                    value = value.lstrip(" ")
                    if field == "data":
                        event["data"].append(value)
                    elif field == "id":
                        last_event_id = value
                        event["id"] = value
                    elif field == "event":
                        event["event"] = value
                    elif field == "retry" and value.isdigit():
                        retry_seconds = max(0.1, int(value) / 1000)

        except (httpx.HTTPError, OSError) as exc:
            jitter = random.uniform(0, retry_seconds * 0.2)
            delay = min(30.0, retry_seconds + jitter)
            print(f"stream failed: {exc}; reconnecting in {delay:.1f}s")
            time.sleep(delay)
            retry_seconds = min(30.0, retry_seconds * 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/events")
    consume(parser.parse_args().url)

