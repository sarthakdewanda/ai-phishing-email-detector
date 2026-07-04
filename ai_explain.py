"""
ai_explain.py
Lightweight AI explanation using a local Ollama model.
"""

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2" 


def _format_header_info(header_result):
    """Turn header findings into short text lines for the prompt/fallback."""
    if not header_result:
        return "No email headers were provided."
    auth = header_result["auth"]
    auth_line = (
        f"SPF={auth['spf']}, DKIM={auth['dkim']}, DMARC={auth['dmarc']}"
    )
    flags = "; ".join(header_result["flags"]) or "none"
    return f"Authentication: {auth_line}. Header flags: {flags}."


def _build_prompt(analysis, header_result, email_text):
    """Create a short, focused prompt from all detection results."""
    keywords = ", ".join(k for k, _ in analysis["keywords"]) or "none"
    urls = ", ".join(analysis["suspicious_urls"]) or "none"

    return f"""You are a cybersecurity assistant. Explain briefly (3-5 sentences)
why the following email may or may not be a phishing attempt.

Risk level: {analysis['level']} (score {analysis['score']})
Suspicious phrases found: {keywords}
Suspicious URLs found: {urls}
{_format_header_info(header_result)}

Email:
\"\"\"
{email_text[:1500]}
\"\"\"

Give a short, plain-language explanation of the red flags, mentioning both
the content and the email authentication results where relevant."""


def _fallback_explanation(analysis, header_result):
    keywords = [k for k, _ in analysis["keywords"]]
    parts = [f"This email scored {analysis['level']} risk."]

    if keywords:
        parts.append(
            "It contains suspicious phrases such as "
            + ", ".join(keywords[:5]) + "."
        )
    if analysis["suspicious_urls"]:
        parts.append(
            "It includes suspicious links: "
            + ", ".join(analysis["suspicious_urls"]) + "."
        )
    if header_result and header_result["flags"]:
        parts.append(
            "Header analysis found: " + "; ".join(header_result["flags"]) + "."
        )
    if not keywords and not analysis["suspicious_urls"] and (
        not header_result or not header_result["flags"]
    ):
        parts.append("No strong phishing indicators were detected.")

    parts.append("(AI service unavailable — showing rule-based summary.)")
    return " ".join(parts)


def explain(analysis, header_result, email_text):
    prompt = _build_prompt(analysis, header_result, email_text)
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        text = response.json().get("response", "").strip()
        return text or _fallback_explanation(analysis, header_result)
    except Exception:
        return _fallback_explanation(analysis, header_result)


def explain_stream(analysis, header_result, email_text):
    import json

    prompt = _build_prompt(analysis, header_result, email_text)
    try:
        with requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": True},
            timeout=60,
            stream=True,
        ) as response:
            response.raise_for_status()
            got_any = False
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line.decode("utf-8"))
                chunk = data.get("response", "")
                if chunk:
                    got_any = True
                    yield chunk
            if not got_any:
                yield _fallback_explanation(analysis, header_result)
    except Exception:
        yield _fallback_explanation(analysis, header_result)