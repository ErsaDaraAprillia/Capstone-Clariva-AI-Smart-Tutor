import google.generativeai as genai
import os
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Configure API ──────────────────────────────────────────────
def get_model():
    """
    Initialize model fresh each call so API key updates
    from .env or st.secrets are always picked up.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    # Fallback: jika .env kosong, coba baca dari Streamlit secrets
    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found. "
            "Please set it in your .env file or Streamlit secrets."
        )

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")


# ── Error Types ────────────────────────────────────────────────
RETRYABLE_ERRORS = (
    "quota",
    "rate",
    "limit",
    "overloaded",
    "503",
    "502",
    "500",
    "resource exhausted",
)

USER_FRIENDLY_ERRORS = {
    "api_key": "❌ Invalid API key. Please check your GEMINI_API_KEY in the .env file.",
    "quota":   "⏳ API quota exceeded. Please wait a moment and try again.",
    "rate":    "⏳ Too many requests. Please wait a few seconds and try again.",
    "network": "🌐 Network error. Please check your internet connection.",
    "empty":   "⚠️ The AI returned an empty response. Please try rephrasing your input.",
    "default": "❌ Something went wrong. Please try again.",
}


def _classify_error(error_message: str) -> str:
    """Map raw error message to a user-friendly category."""
    msg = error_message.lower()
    if any(k in msg for k in ("api key", "invalid key", "api_key", "unauthenticated")):
        return "api_key"
    if any(k in msg for k in ("quota", "resource exhausted")):
        return "quota"
    if any(k in msg for k in ("rate", "limit", "429")):
        return "rate"
    if any(k in msg for k in ("network", "connection", "timeout", "unreachable")):
        return "network"
    return "default"


# ── Main Function ──────────────────────────────────────────────
def generate_response(prompt: str, max_retries: int = 3) -> str:
    """
    Call Gemini API with:
    - Retry logic (exponential backoff) for quota/rate errors
    - User-friendly error messages for all failure types
    - Empty response detection
    - Returns string always (never crashes the app)
    """

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            model = get_model()
            response = model.generate_content(prompt)

            # ── Empty response check ───────────────────────────
            if not response or not response.text or not response.text.strip():
                return USER_FRIENDLY_ERRORS["empty"]

            return response.text

        except Exception as e:
            last_error = str(e)
            error_lower = last_error.lower()

            # ── Retryable errors: wait then retry ─────────────
            if any(k in error_lower for k in RETRYABLE_ERRORS):
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # 2s, 4s, 8s
                    time.sleep(wait_time)
                    continue  # retry

            # ── Non-retryable: break immediately ──────────────
            break

    # ── All retries exhausted or non-retryable error ───────────
    category = _classify_error(last_error or "")
    friendly_msg = USER_FRIENDLY_ERRORS.get(category, USER_FRIENDLY_ERRORS["default"])

    # Log raw error to console for debugging (not shown to user)
    print(f"[EduMind Error] Attempt {attempt} failed: {last_error}")

    return friendly_msg


# ── Optional: Connection Test ──────────────────────────────────
def test_connection() -> tuple[bool, str]:
    """
    Quick ping to verify API key works.
    Returns (True, "OK") or (False, "error message").
    Used in the sidebar API status indicator.
    """
    try:
        model = get_model()
        response = model.generate_content("Say 'OK' in one word.")
        if response and response.text:
            return True, "Connected"
        return False, "Empty response from API"
    except Exception as e:
        category = _classify_error(str(e))
        return False, USER_FRIENDLY_ERRORS.get(category, USER_FRIENDLY_ERRORS["default"])