"""
rules.py
Loads the detection rules from the JSON files in ``config/`` once at startup
and exposes them through a single read-only ``Rules`` object.
"""

import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "config"


@dataclass(frozen=True)
class Rules:

    keywords: dict[str, int]          # phrase -> weight
    url_shorteners: list[str]         # shortener domains
    known_brands: list[str]           # brands phishers impersonate
    weights: dict[str, int]           # rule name -> score contribution
    many_urls_threshold: int          # number of links that counts as "many"
    high_threshold: int               # score at/above this is "High" risk
    medium_threshold: int             # score at/above this is "Medium" risk

    def weight(self, rule_name: str) -> int:
        return self.weights.get(rule_name, 0)


def _load_json(filename: str) -> dict:
    path = CONFIG_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_rules() -> Rules:
    keywords = _load_json("keywords.json")["keywords"]
    url_shorteners = _load_json("url_shorteners.json")["url_shorteners"]
    known_brands = _load_json("domains.json")["known_brands"]

    cfg = _load_json("weights.json")
    thresholds = cfg["risk_thresholds"]

    return Rules(
        keywords=keywords,
        url_shorteners=url_shorteners,
        known_brands=known_brands,
        weights=cfg["weights"],
        many_urls_threshold=cfg["many_urls_threshold"],
        high_threshold=thresholds["high"],
        medium_threshold=thresholds["medium"],
    )


RULES = load_rules()
