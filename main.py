import os
import secrets
import threading
import time
from collections import deque

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from edi_parser import parse_997
from masking import mask_edi

app = FastAPI()

# Rate limit settings: 5 calls per 60 seconds for each API key (low, for testing)
RATE_LIMIT = 5
WINDOW_SECONDS = 60
_calls = {}
_lock = threading.Lock()


def verify_api_key(x_api_key: str = Header(default=None)):
    expected = os.environ.get("EDI_API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="Server API key is not configured")
    if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def rate_limit(x_api_key: str = Header(default=None)):
    now = time.time()
    with _lock:
        calls = _calls.setdefault(x_api_key, deque())
        # forget calls that are older than the time window
        while calls and now - calls[0] > WINDOW_SECONDS:
            calls.popleft()
        if len(calls) >= RATE_LIMIT:
            retry_after = int(WINDOW_SECONDS - (now - calls[0])) + 1
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )
        calls.append(now)


class ExplainRequest(BaseModel):
    type: str
    payload: str


def build_summary(parsed):
    """Turn the parsed 997 into one readable paragraph."""
    parts = []
    for s in parsed["transaction_sets"]:
        text = f"Transaction set {s['set_id']} (control {s['control_number']}): {s['status']}."
        for e in s["set_errors"]:
            text += f" {e}."
        for seg in s["segment_errors"]:
            text += f" Segment {seg['segment_id']} (position {seg['position']}): {seg['error']}."
            for el in seg["element_errors"]:
                text += f" Element {el['element_position']}: {el['error']}"
                if el["bad_value"]:
                    text += f" (value {el['bad_value']})"
                text += "."
        parts.append(text)
    return " ".join(parts)


@app.get("/")
def home():
    return {"message": "EDI Error Explainer is running"}


@app.post("/explain")
def explain(
    req: ExplainRequest,
    _key: None = Depends(verify_api_key),
    _limit: None = Depends(rate_limit),
):
    if req.type != "997":
        raise HTTPException(status_code=400, detail="Only type 997 is supported for now")

    # Mask sender and receiver IDs first. Everything after this line,
    # including any future AI step, only sees the masked copy.
    masked = mask_edi(req.payload)

    parsed = parse_997(masked)

    if not parsed["transaction_sets"]:
        raise HTTPException(status_code=400, detail="No AK2 transaction set found in the payload")

    return {
        "summary": build_summary(parsed),
        "masked_payload": masked,
        "details": parsed,
    }