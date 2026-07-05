"""
app.py
Streamlit UI for the AI Phishing Email Detection & Analysis tool.
"""

import streamlit as st

from detector import score_email
from header_analysis import analyze_headers
from ai_explain import explain_stream
from rules import RULES

st.set_page_config(page_title="AI Phishing Detector", page_icon="🛡️", layout="centered")

# --- Theme + styling ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg: #0d1117;
        --card: #161b26;
        --card-border: #2a3142;
        --text: #e6edf3;
        --muted: #8b949e;
        --accent: #3aa8c1;
        --green: #3fb950;
        --amber: #d29922;
        --red: #f85149;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: var(--bg);
        color: var(--text);
    }

    /* Trim Streamlit's big top padding */
    .block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 780px; }

    /* Header */
    .app-title { font-size: 2rem; font-weight: 700; margin-bottom: 0.15rem; }
    .app-subtitle { color: var(--muted); font-size: 0.95rem; margin-bottom: 1.2rem; }
    .divider { height: 1px; background: var(--card-border); margin: 0.5rem 0 1.5rem; }

    /* Inputs */
    .stTextArea textarea {
        background-color: var(--card);
        color: var(--text);
        border: 1px solid var(--card-border);
        border-radius: 10px;
    }
    .stFileUploader { background: transparent; }

    /* Buttons */
    .stButton button {
        background: var(--accent);
        color: #05222b;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.4rem;
        transition: filter 0.15s ease;
    }
    .stButton button:hover { filter: brightness(1.1); }

    /* Cards with staggered fade-in */
    .card {
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1rem;
        animation: fadeUp 0.45s ease both;
        transition: border-color 0.2s ease;
    }
    .card:hover { border-color: var(--accent); }
    .card h4 {
        margin: 0 0 0.7rem;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--muted);
        font-weight: 600;
    }
    .card:nth-of-type(1) { animation-delay: 0.00s; }
    .card:nth-of-type(2) { animation-delay: 0.08s; }
    .card:nth-of-type(3) { animation-delay: 0.16s; }
    .card:nth-of-type(4) { animation-delay: 0.24s; }
    .card:nth-of-type(5) { animation-delay: 0.32s; }
    .card:nth-of-type(6) { animation-delay: 0.40s; }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Badges & pills */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.8rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .pill {
        display: inline-block;
        padding: 0.18rem 0.65rem;
        margin: 0.15rem 0.3rem 0.15rem 0;
        border-radius: 999px;
        font-size: 0.82rem;
        background: #1f2633;
        border: 1px solid var(--card-border);
    }
    .score-num { font-size: 2.4rem; font-weight: 700; line-height: 1; }
    .score-label { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .url-mono { font-family: monospace; font-size: 0.85rem; word-break: break-all; }
    .flag { color: var(--amber); }
    .brk-row { display: flex; justify-content: space-between; padding: 0.2rem 0; border-bottom: 1px solid #20283610; }
    .brk-pts { color: var(--accent); font-weight: 600; }
    /* Native bordered container to match .card styling */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card);
        border: 1px solid var(--card-border) !important;
        border-radius: 12px;
        padding: 0.3rem 0.4rem;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

LEVEL_COLORS = {"Low": "#3fb950", "Medium": "#d29922", "High": "#f85149"}
AUTH_COLORS = {"pass": "#3fb950", "fail": "#f85149", "unknown": "#8b949e"}


def card(title, body_html):
    st.markdown(
        f"<div class='card'><h4>{title}</h4>{body_html}</div>",
        unsafe_allow_html=True,
    )


def show_results(text):
    header_result = analyze_headers(text)
    analysis = score_email(text, header_result)
    color = LEVEL_COLORS[analysis["level"]]

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --- Risk summary ---
    badge = (
        f"<span class='badge' style='background:{color}22; color:{color};'>"
        f"{analysis['level']} Risk</span>"
    )
    risk_body = (
        f"<div style='display:flex; align-items:center; justify-content:space-between;'>"
        f"<div><div class='score-num' style='color:{color};'>{analysis['score']}</div>"
        f"<div class='score-label'>Risk Score</div></div>"
        f"<div>{badge}</div></div>"
    )
    card("Risk Summary", risk_body)

    # --- Header analysis ---
    if header_result:
        auth = header_result["auth"]
        pills = " ".join(
            f"<span class='pill' style='color:{AUTH_COLORS.get(v, '#8b949e')};'>"
            f"{m.upper()}: {v}</span>"
            for m, v in auth.items()
        )
        flags_html = ""
        if header_result["flags"]:
            flags_html = "".join(
                f"<div class='flag'>⚠️ {f}</div>" for f in header_result["flags"]
            )
        else:
            flags_html = "<div style='color:var(--muted);'>No header red flags detected.</div>"
        body = (
            f"<div style='margin-bottom:0.5rem;'><b>From:</b> {header_result['from']}</div>"
            f"<div style='margin-bottom:0.7rem;'><b>Subject:</b> {header_result['subject']}</div>"
            f"<div style='margin-bottom:0.7rem;'>{pills}</div>{flags_html}"
        )
    else:
        body = "<div style='color:var(--muted);'>No header data found (body-only text). Content analysis only.</div>"
    card("Header Analysis", body)

    # --- Suspicious phrases ---
    if analysis["keywords"]:
        chips = "".join(f"<span class='pill'>{k}</span>" for k, _ in analysis["keywords"])
    else:
        chips = "<span style='color:var(--muted);'>None detected.</span>"
    card("Suspicious Phrases", chips)

    # --- URLs ---
    if analysis["urls"]:
        rows = ""
        for url in analysis["urls"]:
            tag = " <span class='flag'>⚠️ suspicious</span>" if url in analysis["suspicious_urls"] else ""
            rows += f"<div class='url-mono'>{url}{tag}</div>"
    else:
        rows = "<span style='color:var(--muted);'>No URLs found.</span>"
    card("Extracted URLs", rows)

    # --- Detected rules ---
    if analysis["detections"]:
        rules_html = "".join(
            f"<div style='margin-bottom:0.6rem;'>"
            f"<div><b>{d.matched}</b> "
            f"<span class='brk-pts'>+{d.score}</span></div>"
            f"<div style='color:var(--muted); font-size:0.85rem;'>{d.reason}</div>"
            f"</div>"
            for d in analysis["detections"]
        )
    else:
        rules_html = "<span style='color:var(--muted);'>No rules triggered.</span>"
    card("Detected Rules", rules_html)

    # --- Score breakdown ---
    if analysis["breakdown"]:
        brk = "".join(
            f"<div class='brk-row'><span>{reason}</span><span class='brk-pts'>+{pts}</span></div>"
            for reason, pts in analysis["breakdown"]
        )
    else:
        brk = "<span style='color:var(--muted);'>No scoring signals triggered.</span>"
    card("Why This Score", brk)

# --- AI explanation ---
    with st.container(border=True):
        st.markdown(
            "<h4 style='margin:0 0 0.7rem; font-size:0.8rem; text-transform:uppercase; "
            "letter-spacing:0.06em; color:var(--muted); font-weight:600;'>AI Explanation</h4>",
            unsafe_allow_html=True,
        )
        with st.spinner("Analyzing with AI..."):
            st.write_stream(explain_stream(analysis, header_result, text))

    # --- Report summary ---
    header_flag_count = len(header_result["flags"]) if header_result else 0
    sender = analysis["sender_domain"] or "n/a"
    report = (
        f"Risk: <b style='color:{color};'>{analysis['level']}</b> (score {analysis['score']}) &nbsp;|&nbsp; "
        f"Sender domain: <b>{sender}</b> &nbsp;|&nbsp; "
        f"{len(analysis['keywords'])} phrase(s) &nbsp;|&nbsp; "
        f"{len(analysis['urls'])} URL(s), {len(analysis['suspicious_urls'])} flagged &nbsp;|&nbsp; "
        f"{header_flag_count} header flag(s)"
    )
    card("Report Summary", report)


# --- Header ---
st.markdown("<div class='app-title'>🛡️ AI Phishing Email Detector</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='app-subtitle'>Analyze an email for phishing red flags — "
    "content, links, and sender authentication.</div>",
    unsafe_allow_html=True,
)

# Loaded rule counts — makes it clear the detection lists come from config/*.json.
st.markdown(
    "<div class='app-subtitle' style='font-size:0.82rem;'>"
    f"Loaded rules: {len(RULES.keywords)} keywords &nbsp;·&nbsp; "
    f"{len(RULES.url_shorteners)} URL shorteners &nbsp;·&nbsp; "
    f"{len(RULES.known_brands)} brands</div>",
    unsafe_allow_html=True,
)

# --- Input options ---
uploaded = st.file_uploader("Upload a .txt or .eml email", type=["txt", "eml"])
default_text = ""
if uploaded is not None:
    default_text = uploaded.read().decode("utf-8", errors="ignore")

email_text = st.text_area("Or paste the email here:", value=default_text, height=240)

if st.button("Analyze"):
    if email_text.strip():
        show_results(email_text)
    else:
        st.warning("Please paste an email or upload a .txt / .eml file first.")
