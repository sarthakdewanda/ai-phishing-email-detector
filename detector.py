"""
detector.py
Core content-detection logic: URL extraction, keyword detection, and
weighted risk scoring. 
"""

import re
from dataclasses import dataclass

from rules import RULES

# Matches http/https URLs up to the first whitespace or common delimiter.
URL_REGEX = re.compile(r'https?://[^\s<>"\')]+', re.IGNORECASE)

# Matches a URL whose host is a raw IPv4 address.
IP_URL_REGEX = re.compile(r'https?://\d{1,3}(\.\d{1,3}){3}', re.IGNORECASE)


@dataclass
class Detection:

    matched: str    # the concrete thing that matched (phrase, URL, domain...)
    reason: str     # plain-language explanation of why it is suspicious
    score: int      # points this detection adds to the total


# --------------------------------------------------------------------------- #
# URL extraction and helpers
# --------------------------------------------------------------------------- #

def extract_urls(text: str) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for url in URL_REGEX.findall(text):
        url = url.rstrip(".,;:!?)")  # strip trailing sentence punctuation
        if url not in seen:
            seen.add(url)
            cleaned.append(url)
    return cleaned


def _host_of(url: str) -> str:
    host = re.sub(r'^https?://', '', url, flags=re.IGNORECASE)
    host = host.split("/", 1)[0]        # drop path
    host = host.split("@", 1)[-1]       # drop any user-info prefix
    host = host.split(":", 1)[0]        # drop port
    return host.lower()


def registered_domain(host: str) -> str:
    labels = host.split(".")
    if len(labels) >= 2:
        return ".".join(labels[-2:])
    return host


# --------------------------------------------------------------------------- #
# Detection rules
# --------------------------------------------------------------------------- #

def detect_keywords(text: str) -> list[Detection]:
    lower = text.lower()
    detections: list[Detection] = []
    for phrase, weight in RULES.keywords.items():
        if phrase in lower:
            detections.append(
                Detection(
                    matched=phrase,
                    reason=f'Contains the phishing phrase "{phrase}".',
                    score=weight,
                )
            )
    return detections


def detect_suspicious_urls(urls: list[str]) -> list[Detection]:
    detections: list[Detection] = []
    for url in urls:
        host = _host_of(url)

        if any(short in host for short in RULES.url_shorteners):
            detections.append(
                Detection(
                    matched=url,
                    reason="Uses a URL shortener, which hides the real destination.",
                    score=RULES.weight("suspicious_url"),
                )
            )
        elif IP_URL_REGEX.match(url):
            detections.append(
                Detection(
                    matched=url,
                    reason="Links to a raw IP address instead of a domain name.",
                    score=RULES.weight("ip_address_url"),
                )
            )
        elif "@" in url.split("//", 1)[-1]:
            detections.append(
                Detection(
                    matched=url,
                    reason="Uses a 'user@host' trick to disguise the real host.",
                    score=RULES.weight("userinfo_url"),
                )
            )
    return detections


def detect_many_urls(urls: list[str]) -> list[Detection]:
    if len(urls) >= RULES.many_urls_threshold:
        return [
            Detection(
                matched=f"{len(urls)} URLs",
                reason=f"Contains {len(urls)} links; phishing emails often pack in many.",
                score=RULES.weight("many_urls"),
            )
        ]
    return []


def detect_domain_mismatch(sender_domain: str, urls: list[str]) -> list[Detection]:
    if not sender_domain:
        return []

    sender_root = registered_domain(sender_domain)
    detections: list[Detection] = []
    already_flagged: set[str] = set()

    for url in urls:
        link_root = registered_domain(_host_of(url))
        if link_root and link_root != sender_root and link_root not in already_flagged:
            already_flagged.add(link_root)
            detections.append(
                Detection(
                    matched=url,
                    reason=(
                        f"Sender domain is '{sender_root}' but this link points "
                        f"to '{link_root}'."
                    ),
                    score=RULES.weight("domain_mismatch"),
                )
            )
    return detections


def detect_header_signals(header_result: dict | None) -> list[Detection]:
    if not header_result:
        return []

    detections: list[Detection] = []
    auth = header_result["auth"]

    auth_rules = {"spf": "spf_fail", "dkim": "dkim_fail", "dmarc": "dmarc_fail"}
    for mech, rule_name in auth_rules.items():
        if auth.get(mech) == "fail":
            detections.append(
                Detection(
                    matched=f"{mech.upper()}=fail",
                    reason=f"{mech.upper()} authentication failed, suggesting a forged sender.",
                    score=RULES.weight(rule_name),
                )
            )

    for flag in header_result["flags"]:
        if "Display name" in flag:
            detections.append(
                Detection(matched=flag, reason=flag, score=RULES.weight("display_name_spoof"))
            )
        elif "differs from" in flag:
            detections.append(
                Detection(matched=flag, reason=flag, score=RULES.weight("replyto_mismatch"))
            )
    return detections


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #

def _risk_level(score: int) -> str:
    if score >= RULES.high_threshold:
        return "High"
    if score >= RULES.medium_threshold:
        return "Medium"
    return "Low"


def score_email(text: str, header_result: dict | None = None) -> dict:
    urls = extract_urls(text)
    sender_domain = header_result["from_domain"] if header_result else ""

    keyword_hits = detect_keywords(text)
    url_hits = detect_suspicious_urls(urls)
    url_hits += detect_domain_mismatch(sender_domain, urls)
    many_url_hits = detect_many_urls(urls)
    header_hits = detect_header_signals(header_result)

    detections = keyword_hits + url_hits + many_url_hits + header_hits

    score = min(sum(d.score for d in detections), 100)

    suspicious_urls = [d.matched for d in url_hits]
    breakdown = [(d.reason, d.score) for d in detections]

    return {
        "score": score,
        "level": _risk_level(score),
        "urls": urls,
        "suspicious_urls": suspicious_urls,
        "keywords": [(d.matched, d.score) for d in keyword_hits],
        "header_flags": header_result["flags"] if header_result else [],
        "detections": detections,
        "breakdown": breakdown,
        "sender_domain": sender_domain,
    }
