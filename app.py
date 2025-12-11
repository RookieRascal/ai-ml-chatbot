# app.py
"""
TalentScout Hiring Assistant (Gradio)
- Collects candidate info
- Generates 3-5 technical questions per declared tech
- Keeps context
- Exit keywords
- Optional: sentiment analysis + multilingual support
"""

import os
import json
import re
from typing import List, Tuple, Dict

import gradio as gr
import openai

from prompts import SYSTEM_PROMPT, GREETING_PROMPT, TECH_STACK_QUESTION_GENERATION_TEMPLATE, FALLBACK_PROMPT
from utils import check_exit, extract_candidate_fields, normalize_tech_stack
from enhancements import analyze_sentiment, detect_and_translate_to_en, translate_from_en

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or "YOUR_OPENAI_KEY"
openai.api_key = OPENAI_API_KEY
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")  # Use best available

# --- Helpers ---
def call_llm(messages: List[Dict], temperature: float = 0.2) -> str:
    """
    Calls OpenAI chat completion API.
    Falls back to a simple deterministic message if API fails.
    """
    try:
        resp = openai.ChatCompletion.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=800
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        # Fallback short reply
        print("LLM call failed:", e)
        return "Sorry — I'm unable to reach the model right now. Please try again later."

def build_system_and_history(history: List[Tuple[str, str]]) -> List[Dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for user, bot in history:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": bot})
    return messages

# --- Core chatbot logic ---
def process_user_message(user_message: str, history, detect_language: bool = True):
    """
    Handles a user message, maintains context, returns assistant reply and optionally new context.
    """
    user_message = user_message or ""
    # Exit keywords
    if check_exit(user_message):
        reply = "Thank you for your time! We'll review your responses and get back to you about next steps."
        return reply, history

    # Multilingual: detect + translate to English for processing
    original_lang = None
    translated = user_message
    if detect_language:
        translated, original_lang = detect_and_translate_to_en(user_message)

    # Sentiment analysis (optional)
    sentiment = analyze_sentiment(translated)

    # Build messages
    messages = build_system_and_history(history)
    messages.append({"role": "user", "content": translated})

    # If user provided tech stack line like "Tech stack: Python, Django", try to detect and trigger question generation flow
    tech_match = re.search(r"tech stack[:\-]\s*(.+)", translated, re.IGNORECASE)
    if tech_match:
        tech_list_raw = tech_match.group(1)
        techs = normalize_tech_stack(tech_list_raw)

        # Create generation prompt
        generation_prompt = TECH_STACK_QUESTION_GENERATION_TEMPLATE.format(tech_stack=", ".join(techs))
        messages.append({"role": "user", "content": generation_prompt})

        assistant_reply = call_llm(messages)
        # Translate back if needed
        assistant_reply = translate_from_en(assistant_reply, original_lang) if original_lang else assistant_reply

        # Append to history
        history.append((user_message, assistant_reply))
        return assistant_reply, history

    # Otherwise simple conversational step
    messages.append({"role": "user", "content": translated})
    assistant_reply = call_llm(messages)
    assistant_reply = translate_from_en(assistant_reply, original_lang) if original_lang else assistant_reply

    # Include sentiment summary in a short bracket (non-intrusive)
    if sentiment:
        assistant_reply = f"{assistant_reply}\n\n[Sentiment detected: {sentiment}]"

    history.append((user_message, assistant_reply))
    return assistant_reply, history

# --- Minimal chat UI ---
def demo():
    with gr.Blocks(title="TalentScout Hiring Assistant") as demo_app:
        gr.Markdown("# 👋 TalentScout — Hiring Assistant")
        with gr.Row():
            chatbot = gr.Chatbot()
        state = gr.State([])

        txt = gr.Textbox(show_label=False, placeholder="Enter your message here (e.g. 'My name is...'; 'Tech stack: Python, Django')")

        def user_submit(message, history):
            reply, new_history = process_user_message(message, history)
            return "", new_history

        def bot_update(history):
            # return the last assistant message to update Chatbot display
            if not history:
                return []
            # history is list of tuples; Chatbot expects list of [user, bot] pairs flatten
            chat_display = []
            for u, b in history:
                chat_display.append([u, b])
            return chat_display

        txt.submit(user_submit, [txt, state], [txt, state], _js="() => {return null}")  # prevent textbox from showing content again
        txt.submit(lambda history: gr.update(), None, None)  # no-op to ensure submit triggers

        # Start button to show greeting
        start_btn = gr.Button("Start")
        def start_chat(history):
            messages = [{"role":"system","content": SYSTEM_PROMPT},
                        {"role":"user","content": GREETING_PROMPT}]
            greeting = call_llm(messages)
            history.append(("__system__", greeting))
            return gr.update(), history

        start_btn.click(start_chat, state, [txt, state])

        demo_app.launch()

if __name__ == "__main__":
    demo()
