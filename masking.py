def mask_edi(raw):
    """Hide sender and receiver IDs in ISA and GS segments."""
    out = []
    for seg in raw.split("~"):
        p = seg.split("*")
        tag = p[0].strip()
        if tag == "ISA":
            # ISA06 and ISA08 are fixed width, so keep the same length
            for i in (6, 8):
                if len(p) > i:
                    p[i] = "X" * len(p[i])
        elif tag == "GS":
            for i in (2, 3):
                if len(p) > i and p[i]:
                    p[i] = "MASKED"
        out.append("*".join(p))
    return "~".join(out)