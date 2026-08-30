"""Download authoritative SSE and HTTP standards for offline reading."""

from pathlib import Path
from urllib.request import urlopen

DOCUMENTS = {
    "whatwg-server-sent-events.html": (
        "https://html.spec.whatwg.org/multipage/server-sent-events.html"
    ),
    "rfc9110-http-semantics.txt": "https://www.rfc-editor.org/rfc/rfc9110.txt",
    "rfc9112-http-1.1.txt": "https://www.rfc-editor.org/rfc/rfc9112.txt",
}


def main() -> None:
    destination = Path(__file__).parent / "downloads"
    destination.mkdir(parents=True, exist_ok=True)

    for filename, url in DOCUMENTS.items():
        print(f"Downloading {url}")
        with urlopen(url, timeout=30) as response:
            (destination / filename).write_bytes(response.read())


if __name__ == "__main__":
    main()

