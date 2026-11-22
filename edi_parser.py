import json
import sys

STATUS = {
    "A": "Accepted",
    "E": "Accepted, but errors were noted",
    "R": "Rejected",
    "P": "Partially accepted",
}

SET_ERRORS = {
    "1": "Transaction set not supported",
    "2": "Transaction set trailer missing",
    "3": "Control number in header and trailer do not match",
    "4": "Segment count in trailer does not match actual count",
    "5": "One or more segments in error",
    "6": "Missing or invalid transaction set identifier",
    "7": "Missing or invalid transaction set control number",
    "23": "Transaction set control number not unique in the group",
}

SEGMENT_ERRORS = {
    "1": "Unrecognized segment ID",
    "2": "Unexpected segment",
    "3": "Mandatory segment missing",
    "4": "Loop occurs over maximum times",
    "5": "Segment exceeds maximum use",
    "6": "Segment not in defined transaction set",
    "7": "Segment not in proper sequence",
    "8": "Segment has data element errors",
}

ELEMENT_ERRORS = {
    "1": "Mandatory data element missing",
    "2": "Conditional required data element missing",
    "3": "Too many data elements",
    "4": "Data element too short",
    "5": "Data element too long",
    "6": "Invalid character in data element",
    "7": "Invalid code value",
    "8": "Invalid date",
    "9": "Invalid time",
    "10": "Exclusion condition violated",
}


def part(parts, i):
    """Safely get item i from a list, or empty text if it is missing."""
    return parts[i] if len(parts) > i else ""


def parse_997(raw):
    # 1. Split the message into segments (each ends with ~)
    segments = [s.strip() for s in raw.split("~") if s.strip()]

    group = {}
    sets = []
    current_set = None
    current_seg_error = None

    for seg in segments:
        # 2. Split a segment into elements (separated by *)
        p = seg.split("*")
        tag = p[0]

        if tag == "AK1":
            group["functional_id"] = part(p, 1)
            group["control_number"] = part(p, 2)

        elif tag == "AK2":
            current_set = {
                "set_id": part(p, 1),
                "control_number": part(p, 2),
                "status": "",
                "set_errors": [],
                "segment_errors": [],
            }
            sets.append(current_set)
            current_seg_error = None

        elif tag == "AK3" and current_set is not None:
            current_seg_error = {
                "segment_id": part(p, 1),
                "position": part(p, 2),
                "error": SEGMENT_ERRORS.get(part(p, 4), "Unknown error code " + part(p, 4)),
                "element_errors": [],
            }
            current_set["segment_errors"].append(current_seg_error)

        elif tag == "AK4" and current_seg_error is not None:
            current_seg_error["element_errors"].append({
                "element_position": part(p, 1),
                "error": ELEMENT_ERRORS.get(part(p, 3), "Unknown error code " + part(p, 3)),
                "bad_value": part(p, 4),
            })

        elif tag == "AK5" and current_set is not None:
            current_set["status"] = STATUS.get(part(p, 1), "Unknown status " + part(p, 1))
            for code in p[2:]:
                if code:
                    current_set["set_errors"].append(
                        SET_ERRORS.get(code, "Unknown error code " + code)
                    )

        elif tag == "AK9":
            group["status"] = STATUS.get(part(p, 1), "Unknown status " + part(p, 1))
            group["sets_included"] = part(p, 2)
            group["sets_accepted"] = part(p, 4)

    return {"group": group, "transaction_sets": sets}


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        print(json.dumps(parse_997(f.read()), indent=2))