# EDI Error Explainer

A small personal project that turns EDI 997 acknowledgment errors into plain-English explanations through a REST API. It combines a rule-based parser with an optional LLM step.

**All data in this repo is invented demo data. No real partner or company data is used.**

## What it does

Send a 997 message to the API. It returns:

- a table-based summary of what was accepted or rejected, which segments were wrong, and why (always)
- an optional AI explanation with practical things to check (when `use_ai` is true)

Example request:

```json
POST /explain
x-api-key: demo-key-12345

{
  "type": "997",
  "use_ai": true,
  "payload": "ST*997*0001~AK1*PO*123~AK2*850*0001~AK3*PO1*5**8~AK4*2*235*7~AK5*R*5~AK9*R*1*1*0~SE*8*0001~"
}
```

Example summary in the response:

> Transaction set 850 (control 0001): Rejected. One or more segments in error. Segment PO1 (position 5): Segment has data element errors. Element 2: Invalid code value.

## Architecture

Target design, and what runs locally today:

```
Real-world design:   Sterling Integrator -> Apigee X -> Python app -> LLM (optional)
Runs on a laptop:    Postman / simulator -> gateway code -> Python app -> Gemini API (optional)
```

Inside the Python app:

```
Client -> Python app (FastAPI)
           |- API key check (401)
           |- Rate limit (429)
           |- Masking of ISA/GS sender and receiver IDs
           |- 997 parser + error-code tables (source of truth)
           |- Optional LLM step (Gemini API)
```

How the AI step is kept safe:

- Only the parsed result is sent to the LLM, never the raw EDI.
- IDs are masked before parsing.
- The prompt tells the model to use only the facts it is given.
- If the AI call fails (for example HTTP 503), the response still contains the table-based summary, plus an `ai_error` note.

## Why a gateway?

The explainer works without a gateway. A gateway such as Apigee X is added for governance, not for functionality:

- **Cost control.** Each LLM call can cost money. Quota and spike arrest limit the calls before they reach the backend or the LLM.
- **Data protection.** EDI carries partner IDs. Masking at the gateway means no backend or AI service sees the raw values, and the rule is enforced in one place.
- **Many consumers, one rule set.** Sterling is only the first caller. Each consumer can get its own key and quota, and one key can be revoked without redeploying anything.
- **Secrets stay out of callers.** A Sterling process should not hold an LLM key. Callers hold a gateway key, and the provider key lives in the gateway.
- **Visibility.** Analytics show who calls the API, how often, and what fails.

In this repo, those controls are written in code to practice the ideas behind the matching Apigee policies:

| Code in this repo | Apigee policy it mirrors |
|---|---|
| API key check (401) | VerifyAPIKey |
| Per-key rate limit (429) | Quota, SpikeArrest |
| Masking of ISA/GS IDs | Masking with JavaScript or RegularExpressionProtection |

Apigee itself has not been built yet. It is a planned phase.

## Run it (Windows)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set EDI_API_KEY=demo-key-12345
set GEMINI_API_KEY=your-own-key
uvicorn main:app
```

`GEMINI_API_KEY` is only needed for `use_ai: true`. Optionally set `GEMINI_MODEL` to choose a different model. Keys are read from environment variables and never stored in the repo.

In a second window, run the Sterling-style simulator:

```
python sterling_simulator.py
python sterling_simulator.py --ai samples\997_rejected.edi
```

## Files

- `main.py`: API, key check, rate limit
- `edi_parser.py`: 997 parser and error-code tables
- `masking.py`: masks sender and receiver IDs
- `ai_explainer.py`: optional LLM step with fallback
- `sterling_simulator.py`: script that mimics a Sterling Integrator HTTP call (use `--ai` for the AI step)
- `samples/`: demo 997 files

## Limitations

- Only 997 messages are supported.
- The error-code tables should be checked against the X12 standard or a partner spec before real use.
- AI explanations can be wrong or vary between calls, so the parser output is the source of truth. An early version of the prompt made the model claim a value was "empty" when the 997 had not reported it, which is why the prompt now forbids that.
- The rate limit is kept in memory and works for a single server process only.
- Only ID fields are masked, not names or addresses.

## Possible next steps

- Put an Apigee proxy in front of the app and move the gateway controls into policies
- Retry the AI call on temporary errors
- Support other EDI acknowledgments and error logs