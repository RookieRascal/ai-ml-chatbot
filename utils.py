# utils.py

import re
from typing import List, Tuple

EXIT_KEYWORDS = ["quit", "exit", "stop", "bye", "end"]

def check_exit(user_input: str) -> bool:
    if not user_input:
        return False
    s = user_input.lower()
    return any(k in s for k in EXIT_KEYWORDS)

def normalize_tech_stack(tech_text: str) -> List[str]:
    # Accept comma or slash separated inputs, remove extra spaces
    parts = re.split(r"[,/;|]+", tech_text)
    techs = [p.strip() for p in parts if p.strip()]
    return techs

def extract_candidate_fields(text: str) -> dict:
    """
    Extremely simple parser to extract common fields from a single-message resume-like text.
    Use this for basic auto-fill if candidate pastes a short block.
    """
    data = {}
    # name: naive heuristic
    name_match = re.search(r"(name[:\-]\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)*))", text, re.IGNORECASE)
    if name_match:
        data["full_name"] = name_match.group(2).strip()
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_match:
        data["email"] = email_match.group(0)
    phone_match = re.search(r"(\+?\d[\d\s\-]{7,}\d)", text)
    if phone_match:
        data["phone"] = phone_match.group(0)
    exp_match = re.search(r"(\d+)\s+years?", text, re.IGNORECASE)
    if exp_match:
        data["years_experience"] = int(exp_match.group(1))
    return data
