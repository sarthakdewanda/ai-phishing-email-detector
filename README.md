# 🛡️ AI Phishing Email Detector

A Streamlit app that analyzes emails for phishing indicators — combining content analysis, email header authentication checks, and a local AI-generated explanation of the red flags.

![App Homepage](screenshots/00-homepage.png)

---

## 📑 Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Features](#features)
- [Screenshots](#screenshots)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
  * [1. Install Dependencies](#1-install-dependencies)
  * [2. Install Ollama (Local AI)](#2-install-ollama-local-ai)
  * [3. Run the App](#3-run-the-app)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Notes & Limitations](#notes--limitations)
- [Resources](#resources)

---

## Overview

Phishing emails rely on two things working together: convincing content and a spoofed or unauthenticated sender. Most simple detectors only look at the first. This project analyzes both — parsing the actual email headers to check SPF/DKIM/DMARC results and sender spoofing, alongside the usual keyword and URL analysis — then uses a locally-run AI model (via Ollama) to explain the findings in plain English.

Built as a small, self-contained portfolio project. No database, no accounts, no external APIs — everything runs locally on your machine.

---

## How It Works

```
   ┌───────────────────────────┐
   │   Email (paste / upload)  │
   │      .txt or .eml         │
   └─────────────┬─────────────┘
                 │
     ┌───────────┴────────────┐
     │                        │
┌────┴─────┐          ┌───────┴────────┐
│ Content  │          │    Header      │
│ Analysis │          │   Analysis     │
│          │          │                │
│ • URLs   │          │ • SPF/DKIM/    │
│ • Phrases│          │   DMARC        │
└────┬─────┘          │ • Spoof checks │
     │                └───────┬────────┘
     └───────────┬────────────┘
                 │
          ┌──────┴───────┐
          │ Risk Scoring │
          │ Low/Med/High │
          └──────┬───────┘
                 │
          ┌──────┴───────┐
          │  Local AI    │
          │  (Ollama)    │
          │  explains    │
          │  the flags   │
          └──────┬───────┘
                 │
          ┌──────┴───────┐
          │ Analysis     │
          │ Report       │
          └──────────────┘
```

| Component | Role |
|---|---|
| `detector.py` | Extracts URLs, detects suspicious phrases, computes the weighted risk score |
| `header_analysis.py` | Parses raw email headers, reads SPF/DKIM/DMARC results, checks for sender spoofing |
| `ai_explain.py` | Sends findings to a local Ollama model and streams back a plain-language explanation |
| `app.py` | Streamlit UI that ties everything together |

> **No network calls for header analysis.** SPF/DKIM/DMARC results are read directly from the `Authentication-Results` header already stamped by the receiving mail server — not re-verified via live DNS.

---

## Features

- Paste an email directly, or upload a `.txt` / `.eml` file
- **URL extraction** with suspicious-link flagging (shorteners, raw IPs, `@` tricks)
- **Keyword detection** against a curated list of common phishing phrases
- **Header analysis**: SPF / DKIM / DMARC verdicts, display-name spoofing, Reply-To / Return-Path mismatches
- **Weighted risk score** → Low / Medium / High, combining content and header signals
- **"Why This Score" breakdown** — every point is itemized and traceable back to a specific signal
- **AI explanation**, streamed live from a local Ollama model, with an offline rule-based fallback if Ollama isn't running
- Clean, dark, minimal UI — no accounts, no database, no external services

---

## Screenshots

**Input and risk summary — header analysis flags authentication failures and sender spoofing:**

![Risk Summary and Header Analysis](screenshots/01-risk-summary.png)

**Detected phrases, extracted URLs, and the full score breakdown:**

![Suspicious Phrases, URLs, and Score Breakdown](screenshots/02-score-breakdown.png)

**AI-generated explanation and final report summary:**

![AI Explanation and Report Summary](screenshots/03-ai-explanation.png)

---

## Prerequisites

- Python 3.9+
- [Ollama](https://ollama.com) installed locally (optional — the app falls back to a rule-based summary without it)

---

## Setup

### 1. Install Dependencies

```
pip install -r requirements.txt
```

### 2. Install Ollama (Local AI)

Download and install from [ollama.com/download](https://ollama.com/download), then pull a lightweight model:

```
ollama pull llama3.2
```

Ollama runs automatically in the background on Windows/macOS after install. Verify it's running by opening `http://localhost:11434` in a browser — it should say **"Ollama is running."**

> If Ollama isn't running, the app still works — it shows a rule-based summary instead of the AI explanation.

### 3. Run the App

```
streamlit run app.py
```

---

## Usage

1. Paste an email into the text box, or upload one of the samples in `sample_emails/`.
2. Click **Analyze**.
3. Review the risk score, header analysis, suspicious phrases, URLs, score breakdown, AI explanation, and report summary.

Try both samples to see the contrast:

| Sample | Expected Result |
|---|---|
| `sample_emails/phishing.eml` | **High risk** — failed SPF/DKIM/DMARC, spoofed sender, Reply-To mismatch, multiple suspicious phrases |
| `sample_emails/legitimate.eml` | **Low risk** — passes all authentication checks, no red-flag phrases |

---

## Project Structure

```
phishing-detector/
├── app.py                 # Streamlit UI
├── detector.py             # Content analysis: URLs, keywords, scoring
├── header_analysis.py      # Header analysis: SPF/DKIM/DMARC, spoof checks
├── ai_explain.py           # AI explanation via Ollama (streaming + fallback)
├── sample_emails/
│   ├── phishing.eml
│   └── legitimate.eml
├── screenshots/
├── requirements.txt
└── README.md
```

---

## Notes & Limitations

- This is a demonstration/portfolio project using **sample emails only** — do not paste real personal or customer emails into it.
- Header analysis reads existing authentication verdicts; it does not perform live DNS lookups or cryptographic re-verification of SPF/DKIM.
- The keyword list is intentionally small and heuristic-based — a real production system would use more robust NLP/ML techniques. This project favors transparency and simplicity over completeness.

---

## Resources

- [Ollama](https://ollama.com)
- [SPF, DKIM, and DMARC Explained (Cloudflare)](https://www.cloudflare.com/learning/email-security/dmarc-dkim-spf/)
- [Streamlit Documentation](https://docs.streamlit.io)