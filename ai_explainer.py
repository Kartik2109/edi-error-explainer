import json
import os
import urllib.error
import urllib.request

# Model name can be changed without editing code: set GEMINI_MODEL
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"

INSTRUCTIONS = (
    "You help support staff understand EDI X12 997 acknowledgment errors. "
    "You receive a parsed result as JSON. Use only the facts in that JSON. "
    "Do not invent segment names, partner names or error codes. "
    "An empty bad_value means the value was not reported in the 997. "
    "Never say that a value was empty, blank or missing unless the error "
    "text itself says so. "
    "Reply in plain English, under 120 words, in two parts: "
    "'What happened' and 'What to check'. "
    "In 'What to check', give 2 or 3 practical checks, such as the mapping "
    "for the failing segment or the partner's specification."
)


def explain_with_ai(parsed):
    """Return (text, error). Exactly one of them is None."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None, "GEMINI_API_KEY is not set on the server"

    prompt = "Parsed 997 result:\n" + json.dumps(parsed, indent=2)
    body = json.dumps({
        "system_instruction": {"parts": [{"text": INSTRUCTIONS}]},
        "contents": [{"parts": [{"text": prompt}]}],
    }).encode("utf-8")

    request = urllib.request.Request(
        URL.format(MODEL),
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read())
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            return None, "The AI service returned an empty answer"
        return text, None
    except urllib.error.HTTPError as err:
        # Print details on the server window only, to help you debug
        print("AI service error", err.code, err.read()[:300])
        return None, f"The AI service returned HTTP {err.code}"
    except (urllib.error.URLError, TimeoutError):
        return None, "Could not reach the AI service"
    except (KeyError, IndexError, ValueError):
        return None, "Unexpected response from the AI service"