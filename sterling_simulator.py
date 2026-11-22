import json
import os
import sys
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8000/explain"
API_KEY = os.environ.get("EDI_API_KEY", "demo-key-12345")  # demo key only


def send(path):
    with open(path) as f:
        edi = f.read().strip()

    body = json.dumps({"type": "997", "payload": edi}).encode("utf-8")
    request = urllib.request.Request(
        URL,
        data=body,
        headers={"Content-Type": "application/json", "x-api-key": API_KEY},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read())
            print(f"{path} -> {response.status} OK")
            print("  " + data["summary"])
    except urllib.error.HTTPError as err:
        print(f"{path} -> {err.code} {err.reason}")
        print("  " + err.read().decode("utf-8"))
    except urllib.error.URLError as err:
        print("Could not reach the API. Is the server running?")
        print("  " + str(err.reason))


if __name__ == "__main__":
    files = sys.argv[1:] or [
        "samples/997_rejected.edi",
        "samples/997_accepted.edi",
    ]
    for file_path in files:
        send(file_path)