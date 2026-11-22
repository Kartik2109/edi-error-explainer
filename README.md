# EDI Error Explainer

A small personal project that turns EDI 997 acknowledgment errors into plain-English explanations through a REST API.

**All data in this repo is invented demo data. No real partner or company data is used.**

## What it does

Send a 997 message to the API. It returns a readable summary of what was accepted or rejected, which segments were wrong, and why.

Example request:

```json
POST /explain
x-api-key: demo-key-12345

{ "type": "997", "payload": "ST*997*0001~AK1*PO*123~AK2*850*0001~AK3*PO1*5**8~AK4*2*235*7~AK5*R*5~AK9*R*1*1*0~SE*8*0001~" }
```

Example summary in the response:

> Transaction set 850 (control 0001): Rejected. One or more segments in error. Segment PO1 (position 5): Segment has data element errors. Element 2: Invalid code value.

## Architecture

```
Client (Postman or simulator) -> Python app (FastAPI) -> JSON explanation
                                  |- API key check (401)
                                  |- Rate limit (429)
                                  |- Masking of ISA/GS sender and receiver IDs
                                  |- 997 parser + error-code tables
```

The gateway features (key check, rate limit, masking) are written in code to practice the ideas behind API gateway policies such as Apigee's VerifyAPIKey, Quota/SpikeArrest and data masking. A real Apigee proxy and an optional LLM step are planned as later phases.

## Run it (Windows)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set EDI_API_KEY=demo-key-12345
uvicorn main:app
```

In a second window, run the Sterling-style simulator:

```
python sterling_simulator.py
```

## Files

- `main.py`: API, key check, rate limit
- `edi_parser.py`: 997 parser and error-code tables
- `masking.py`: masks sender and receiver IDs
- `sterling_simulator.py`: script that mimics a Sterling Integrator HTTP call
- `samples/`: demo 997 files

## Limitations

- Only 997 messages are supported.
- The error-code tables should be checked against the X12 standard or a partner spec before real use.
- The rate limit is kept in memory and works for a single server process only.
- Only ID fields are masked, not names or addresses.

## Possible next steps

- Put an Apigee proxy in front of the app
- Add an optional LLM step for friendlier explanations (using the masked data only)
- Support other EDI acknowledgments and error logs