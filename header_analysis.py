"""
header_analysis.py
Analyzes raw email headers for phishing signals using Python's built-in
email module.
"""

import re
from email import message_from_string
from email.utils import parseaddr, getaddresses


KNOWN_BRANDS = [
    "paypal", "amazon", "apple", "microsoft", "google", "netflix",
    "bank", "facebook", "instagram", "linkedin", "dhl", "fedex",
]


def has_headers(raw_text):
    return bool(re.search(r'^(From|To|Subject|Received):', raw_text, re.MULTILINE))


def _domain_of(address):
    _, addr = parseaddr(address)
    if "@" in addr:
        return addr.split("@")[-1].lower()
    return ""


def _parse_auth_results(msg):
    results = {"spf": "unknown", "dkim": "unknown", "dmarc": "unknown"}
    raw = " ".join(msg.get_all("Authentication-Results", []))
    if not raw:
        return results
    for mech in results:
        match = re.search(rf'{mech}=(\w+)', raw, re.IGNORECASE)
        if match:
            results[mech] = match.group(1).lower()
    return results


def _check_display_name_spoof(from_header):
    display_name, _ = parseaddr(from_header)
    domain = _domain_of(from_header)
    name_lower = display_name.lower()

    for brand in KNOWN_BRANDS:
        if brand in name_lower and brand not in domain:
            return f"Display name mentions '{brand}' but sender domain is '{domain or 'unknown'}'"
    return None


def _check_replyto_mismatch(msg):
    from_domain = _domain_of(msg.get("From", ""))
    if not from_domain:
        return None

    for header in ("Reply-To", "Return-Path"):
        value = msg.get(header, "")
        other_domain = _domain_of(value)
        if other_domain and other_domain != from_domain:
            return f"{header} domain '{other_domain}' differs from From domain '{from_domain}'"
    return None


def analyze_headers(raw_text):
    if not has_headers(raw_text):
        return None

    msg = message_from_string(raw_text)

    auth = _parse_auth_results(msg)
    flags = []

    # Authentication failures are strong signals.
    for mech in ("spf", "dkim", "dmarc"):
        if auth[mech] == "fail":
            flags.append(f"{mech.upper()} authentication failed")

    spoof = _check_display_name_spoof(msg.get("From", ""))
    if spoof:
        flags.append(spoof)

    mismatch = _check_replyto_mismatch(msg)
    if mismatch:
        flags.append(mismatch)

    return {
        "from": msg.get("From", "(none)"),
        "subject": msg.get("Subject", "(none)"),
        "auth": auth,
        "flags": flags,
    }