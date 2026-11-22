import json
import os
import sys
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8000/explain"
API_KEY = os.environ.get("EDI_API_KEY", "demo-key-12345")  # demo key only


def send(path, use_ai):
    with open(path) as f:
        edi = f.read().strip()

    body = json.dumps({"type": "997", "payload": edi, "use_ai": use_ai}).encode("utf-8")
    request = urllib.request.Request(
        URL,
        data=body,
        headers={"Content-Type": "application/json", "x-api-key": API_KEY},
        method="POST",
    )

    try:
        # AI calls can take a few seconds, so allow a longer wait
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read())
            print(f"{path} -> {response.status} OK")
            print("  " + data["summary"])
            if use_ai:
                if data.get("ai_explanation"):
                    print("  AI explanation:")
                    for line in data["ai_explanation"].splitlines():
                        print("    " + line)
                else:
                    print("  AI not available: " + str(data.get("ai_error")))
    except urllib.error.HTTPError as err:
        print(f"{path} -> {err.code} {err.reason}")
        print("  " + err.read().decode("utf-8"))
    except urllib.error.URLError as err:
        print("Could not reach the API. Is the server running?")
        print("  " + str(err.reason))


if __name__ == "__main__":
    args = sys.argv[1:]
    use_ai = "--ai" in args
    files = [a for a in args if a != "--ai"] or [
        "samples/997_rejected.edi",
        "samples/997_accepted.edi",
    ]
    for file_path in files:
        send(file_path, use_ai)