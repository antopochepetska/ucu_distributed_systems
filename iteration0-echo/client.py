"""Echo client.

Usage:
    python client.py "hello"          # send one message
    python client.py                  # interactive mode, empty line to quit
"""
import argparse
import os

import httpx


def send(base_url: str, message: str) -> str:
    resp = httpx.post(f"{base_url}/echo", json={"message": message}, timeout=5)
    resp.raise_for_status()
    return resp.json()["echo"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Echo client")
    parser.add_argument("message", nargs="?", help="message to send")
    parser.add_argument(
        "--url",
        default=os.getenv("ECHO_URL", "http://localhost:8000"),
        help="server base URL (default: $ECHO_URL or http://localhost:8000)",
    )
    args = parser.parse_args()

    if args.message is not None:
        print(send(args.url, args.message))
        return

    while True:
        message = input("> ")
        if not message:
            break
        print(send(args.url, message))


if __name__ == "__main__":
    main()
