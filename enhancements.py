# enhancements.py
from typing import Tuple
import os

# Try to import optional libs (safe fallbacks implemented)
try:
    from langdetect import detect
    from deep_translator import GoogleTranslator
except Exception:
    detect = None
    GoogleTranslator = None

# Sentiment: try transformers pipeline, else fallback to simple rules
try:
    from transformers import pipeline
    _sentiment_pipe = pipeline("sentiment-analysis")
except Exception:
    _sentiment_pipe = None

def detect_and_translate_to_en(text: str) -> Tuple[str, str]:
    """
    Detect language and return (text_in_english, original_lang_code or None)
    If detection/translation tools are not installed, returns (text, None)
    """
    if not text:
        return text, None
    if detect is None or GoogleTranslator is None:
        return text, None
    try:
        lang = detect(text)
        if lang != "en":
            translated = GoogleTranslator(source=lang, target="en").translate(text)
            return translated, lang
        else:
            return text, None
    except Exception:
        return text, None

def translate_from_en(text: str, target_lang: str) -> str:
    if not target_lang:
        return text
    if GoogleTranslator is None:
        return text
    try:
        return GoogleTranslator(source="en", target=target_lang).translate(text)
    except Exception:
        return text

def analyze_sentiment(text: str) -> str:
    if not text:
        return ""
    if _sentiment_pipe:
        try:
            res = _sentiment_pipe(text[:512])
            if res and isinstance(res, list):
                label = res[0]["label"]
                score = res[0].get("score", 0.0)
                return f"{label} ({score:.2f})"
        except Exception:
            pass
    # fallback heuristic
    text_low = text.lower()
    positive_words = ["good", "great", "excellent", "happy", "confident", "interested"]
    negative_words = ["bad", "issue", "problem", "confused", "concerned"]
    pos = sum(1 for w in positive_words if w in text_low)
    neg = sum(1 for w in negative_words if w in text_low)
    if pos > neg:
        return "POSITIVE (heuristic)"
    if neg > pos:
        return "NEGATIVE (heuristic)"
    return "NEUTRAL (heuristic)"
