# Iteration 0 — Echo client-server

FastAPI server that returns the message it receives, plus a small CLI client.

| Method | Path      | Body                     | Response              |
|--------|-----------|--------------------------|-----------------------|
| POST   | `/echo`   | `{"message": "hello"}`   | `{"echo": "hello"}`   |
| GET    | `/health` | –                        | `{"status": "ok"}`    |

## Run locally

```bash
python3.14 -m venv .venv          # brew install python@3.14
.venv/bin/pip install -r requirements-dev.txt

# terminal 1: server
.venv/bin/uvicorn server:app --port 8000

# terminal 2: client
.venv/bin/python client.py "hello"      # one message
.venv/bin/python client.py              # interactive, empty line quits
curl -X POST localhost:8000/echo -H 'Content-Type: application/json' -d '{"message":"hi"}'
```

## Tests

```bash
.venv/bin/pytest
```

## Docker (optional)

```bash
docker build -t echo-server .
docker run --rm -p 8000:8000 echo-server
docker run --rm --network host echo-server python client.py "hello"   # Linux; on macOS use --url http://host.docker.internal:8000
```
