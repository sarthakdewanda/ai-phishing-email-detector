"""
detector.py
Core content-detection logic: URL extraction, keyword detection, and
weighted risk scoring. 
"""

import re

# Suspicious phrases commonly found in phishing emails.
# Each maps to a weight reflecting how strong a signal it is.
SUSPICIOUS_KEYWORDS = {
    "verify your account": 3,
    "verify your identity": 3,
    "confirm your password": 3,
    "update your payment": 3,
    "suspended": 2,
    "unusual activity": 2,
    "click here": 2,
    "act now": 2,
    "urgent": 2,
    "immediately": 2,
    "limited time": 2,
    "you have won": 3,
    "congratulations": 1,
    "gift card": 2,
    "wire transfer": 3,
    "bank account": 2,
    "social security": 3,
    "login to confirm": 3,
    "account will be closed": 3,
    "final notice": 2,
    "dear customer": 1,
    "dear user": 1,
}

# URL shorteners
SUSPICIOUS_URL_HINTS = [
    "bit.ly", "tinyurl", "goo.gl", "t.co", "ow.ly",
    "is.gd", "buff.ly", "rebrand.ly",
]

URL_REGEX = re.compile(r'https?://[^\s<>"\')]+', re.IGNORECASE)


def extract_urls(text):
    urls = URL_REGEX.findall(text)
    cleaned = []
    seen = set()
    for url in urls:
        url = url.rstrip(".,;:!?)")
        if url not in seen:
            seen.add(url)
            cleaned.append(url)
    return cleaned


def flag_suspicious_urls(urls):
    flagged = []
    for url in urls:
        lower = url.lower()
        if any(hint in lower for hint in SUSPICIOUS_URL_HINTS):
            flagged.append(url)
        elif re.search(r'https?://\d{1,3}(\.\d{1,3}){3}', url):  # raw IP address
            flagged.append(url)
        elif "@" in url.split("//", 1)[-1]:  # user@host trick
            flagged.append(url)
    return flagged


def detect_keywords(text):
    lower = text.lower()
    found = []
    for phrase, weight in SUSPICIOUS_KEYWORDS.items():
        if phrase in lower:
            found.append((phrase, weight))
    return found


def score_email(text, header_result=None):
    urls = extract_urls(text)
    suspicious_urls = flag_suspicious_urls(urls)
    keywords = detect_keywords(text)

    score = 0
    breakdown = []  # list of (reason, points)

    # --- Content signals ---
    for phrase, weight in keywords:
        score += weight
        breakdown.append((f"Keyword: \"{phrase}\"", weight))

    for url in suspicious_urls:
        score += 3
        breakdown.append((f"Suspicious URL: {url}", 3))

    if len(urls) >= 3:
        score += 2
        breakdown.append((f"Many links ({len(urls)} URLs)", 2))

    # --- Header signals ---
    header_flags = []
    if header_result:
        header_flags = header_result["flags"]
        auth = header_result["auth"]

        if auth["dkim"] == "fail":
            score += 3
            breakdown.append(("DKIM authentication failed", 3))
        if auth["spf"] == "fail":
            score += 3
            breakdown.append(("SPF authentication failed", 3))
        if auth["dmarc"] == "fail":
            score += 4
            breakdown.append(("DMARC authentication failed", 4))

        # Spoofing / mismatch flags
        for flag in header_flags:
            if "Display name" in flag or "differs from" in flag:
                score += 4
                breakdown.append((flag, 4))

    score = min(score, 100)

    if score >= 10:
        level = "High"
    elif score >= 5:
        level = "Medium"
    else:
        level = "Low"

    return {
        "score": score,
        "level": level,
        "urls": urls,
        "suspicious_urls": suspicious_urls,
        "keywords": keywords,
        "header_flags": header_flags,
        "breakdown": breakdown,
    }