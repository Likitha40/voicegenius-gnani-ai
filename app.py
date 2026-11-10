"""
VoiceGenius - AI Voice Assistant powered by Gnani AI
Flask Backend — FINAL VERSION

Uses:
- Gnani Prisma STT v3 (speech-to-text)
- Gnani Timbre TTS v3 (text-to-speech)
- Google Gemini via REST API (with retry + fallback models)
- Server-side mic recording via sounddevice
"""

import os, io, base64, logging, threading, time, wave
import numpy as np
import sounddevice as sd
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from dotenv import load_dotenv
import requests as http_req

load_dotenv()
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
GNANI_API_KEY    = os.getenv("GNANI_API_KEY", "")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")
MOCK_MODE        = os.getenv("MOCK_MODE", "false").lower() == "true"
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en-IN")

STT_URL = "https://api.vachana.ai/stt/v3"
TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"
SAMPLE_RATE, CHANNELS = 16000, 1

# Gemini models to try in order (fallback chain)
GEMINI_MODELS = ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-flash-latest"]

def gnani_h(extra=None):
    h = {"X-API-Key-ID": GNANI_API_KEY}
    if extra: h.update(extra)
    return h

LANG_NAMES = {
    "en-IN":"English","hi-IN":"Hindi","kn-IN":"Kannada","ta-IN":"Tamil",
    "te-IN":"Telugu","bn-IN":"Bengali","mr-IN":"Marathi","pa-IN":"Punjabi",
    "indic-auto":"the same language the user spoke in",
}
LANGUAGE_VOICES = {
    "en-IN":["Shivani","Avinash"],"hi-IN":["Kalpana","Nalini"],
    "kn-IN":["Shivani"],"ta-IN":["Shivani"],"te-IN":["Shivani"],
    "bn-IN":["Shivani"],"mr-IN":["Shivani"],"pa-IN":["Shivani"],
    "indic-auto":["Shivani"],
}

conversation_history = []
_recording = False
_recorded_frames = []
_record_lock = threading.Lock()

# ── Mock ────────────────────────────────────────────────────────────────────
MOCK_TRANSCRIPT = "Hello! I'm testing VoiceGenius."
MOCK_RESPONSES = [
    "VoiceGenius is powered by Gnani AI's Prisma and Timbre models.",
    "Gnani AI supports multiple Indian languages natively.",
    "Prisma gives state-of-the-art speech recognition for Indian languages.",
    "The Timbre TTS model sounds very natural!",
    "Multilingual AI is the future, especially for India!",
]
_mock_idx = 0
MOCK_WAV_B64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA="
def get_mock_audio(): return base64.b64decode(MOCK_WAV_B64)
def get_mock_response():
    global _mock_idx
    r = MOCK_RESPONSES[_mock_idx % len(MOCK_RESPONSES)]; _mock_idx += 1; return r

# ── Audio helpers ───────────────────────────────────────────────────────────
def numpy_to_wav(audio_np, sr=SAMPLE_RATE):
    buf = io.BytesIO()
    a16 = (audio_np * 32767).astype(np.int16)
    with wave.open(buf, "wb") as w:
        w.setnchannels(CHANNELS); w.setsampwidth(2); w.setframerate(sr); w.writeframes(a16.tobytes())
    return buf.getvalue()

# ── Gemini LLM via REST API (reliable, no SDK dependency issues) ───────────
def call_gemini(user_text, language="en-IN"):
    """Call Gemini via REST API with retry across multiple model names."""
    lang_name = LANG_NAMES.get(language, "English")
    if not GEMINI_API_KEY:
        return template_response(user_text)

    system_msg = (
        f"You are VoiceGenius, a friendly multilingual AI voice assistant by Gnani AI. "
        f"User speaks {lang_name}. Reply in {lang_name}. Keep to 1-2 short sentences. "
        f"Be warm and conversational."
    )

    # Build contents
    contents = []
    for h in conversation_history[-6:]:
        role = "user" if h["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": h["parts"][0]}]})
    contents.append({"role": "user", "parts": [{"text": user_text}]})

    payload = {
        "system_instruction": {"parts": [{"text": system_msg}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 200, "temperature": 0.7}
    }

    # Try each model in the fallback chain
    for model_name in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            resp = http_req.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                if reply:
                    logger.info(f"Gemini ({model_name}) replied: {reply[:80]}")
                    conversation_history.append({"role": "user",  "parts": [user_text]})
                    conversation_history.append({"role": "model", "parts": [reply]})
                    return reply
            elif resp.status_code == 503:
                logger.warning(f"Gemini {model_name} overloaded (503), trying next...")
                continue
            elif resp.status_code == 404:
                logger.warning(f"Gemini model {model_name} not found, trying next...")
                continue
            else:
                logger.error(f"Gemini {model_name} error {resp.status_code}: {resp.text[:200]}")
                continue
        except Exception as e:
            logger.error(f"Gemini {model_name} network error: {e}")
            continue

    logger.warning("All Gemini models failed — using template fallback")
    return template_response(user_text)


def template_response(text):
    """Smart multilingual fallback when Gemini is unavailable."""
    t = text.lower()
    # Greetings in multiple languages
    if any(w in t for w in ["hello","hi","hey","namaste","नमस्ते","నమస్కారం","ನಮಸ್ಕಾರ","வணக்கம்","নমস্কার","नमस्कार"]):
        if "नमस्ते" in text or "नमस्कार" in text:
            return "नमस्ते! मैं VoiceGenius हूँ, Gnani AI द्वारा संचालित। मैं आपकी कैसे मदद करूँ?"
        if "నమస్కారం" in text:
            return "నమస్కారం! నేను VoiceGenius, Gnani AI ద్వారా నడిచే AI వాయిస్ అసిస్టెంట్."
        if "ನಮಸ್ಕಾರ" in text:
            return "ನಮಸ್ಕಾರ! ನಾನು VoiceGenius, Gnani AI ಚಾಲಿತ AI ಧ್ವನಿ ಸಹಾಯಕ."
        if "வணக்கம்" in text:
            return "வணக்கம்! நான் VoiceGenius, Gnani AI இயக்கும் AI குரல் உதவியாளர்."
        if "নমস্কার" in text:
            return "নমস্কার! আমি VoiceGenius, Gnani AI চালিত AI ভয়েস সহকারী."
        return "Hello! I'm VoiceGenius, your AI voice assistant powered by Gnani AI. How can I help you?"
    if any(w in t for w in ["gnani","prisma","timbre"]):
        return "Gnani AI provides world-class speech AI for Indian languages with Prisma STT and Timbre TTS."
    if any(w in t for w in ["language","hindi","kannada","tamil","telugu","bengali","marathi","punjabi","भाषा","భాష"]):
        return "VoiceGenius supports 8 Indian languages: English, Hindi, Kannada, Tamil, Telugu, Bengali, Marathi & Punjabi!"
    if any(w in t for w in ["what","can you","help","how","tell","about"]):
        return "I can listen to your voice in any Indian language, understand it, and reply with natural speech — powered by Gnani AI!"
    if any(w in t for w in ["bye","goodbye","thanks","thank","धन्यवाद","ధన్యవాదాలు","நன்றி"]):
        return "Thank you! Goodbye! It was wonderful talking with you."
    return f"I heard: \"{text[:80]}\". I'm VoiceGenius by Gnani AI — supporting 8 Indian languages!"

# ── Gnani Prisma STT ────────────────────────────────────────────────────────
def call_stt(audio_bytes, language="en-IN", fmt="transcribe"):
    if MOCK_MODE or not GNANI_API_KEY: return MOCK_TRANSCRIPT
    try:
        resp = http_req.post(STT_URL, headers=gnani_h(),
            files={"audio_file": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")},
            data={"model":"prisma-v3.0","language_code":language,"format":fmt}, timeout=30)
        resp.raise_for_status()
        r = resp.json()
        logger.info(f"STT response: {r}")
        return (r.get("transcript") or r.get("text") or
                r.get("result",{}).get("transcript") or r.get("data",{}).get("transcript") or "").strip()
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise RuntimeError(f"STT failed: {e}")

# ── Gnani Timbre TTS ────────────────────────────────────────────────────────
def call_tts(text, language="en-IN", voice="Shivani", speed=1.0):
    if MOCK_MODE or not GNANI_API_KEY: return get_mock_audio()
    valid = LANGUAGE_VOICES.get(language, ["Shivani"])
    if voice not in valid: voice = valid[0]
    tts_lang = language if language != "indic-auto" else "hi-IN"
    payload = {"text":text,"voice":voice,"model":"timbre-v3.0","language":tts_lang,
               "speed":speed,"audio_config":{"sample_rate":48000,"num_channels":1,
               "sample_width":2,"encoding":"linear_pcm","container":"wav"}}
    try:
        resp = http_req.post(TTS_URL, headers=gnani_h({"Content-Type":"application/json"}),
                             json=payload, timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise RuntimeError(f"TTS failed: {e}")

# ── Routes ──────────────────────────────────────────────────────────────────
@app.route("/")
def index(): return render_template("index.html")

@app.route("/test")
def test_page(): return render_template("test.html")

@app.route("/health")
def health():
    return jsonify({"status":"ok","mock_mode":MOCK_MODE,"stt_url":STT_URL,"tts_url":TTS_URL,
                    "gnani_key":bool(GNANI_API_KEY),"gemini_key":bool(GEMINI_API_KEY)})

@app.route("/voices")
def voices(): return jsonify(LANGUAGE_VOICES)

# ── Server-side mic recording ──────────────────────────────────────────────
@app.route("/record/start", methods=["POST"])
def record_start():
    global _recording, _recorded_frames
    with _record_lock:
        if _recording: return jsonify({"error":"Already recording"}), 400
        _recorded_frames = []; _recording = True
    def _cap():
        global _recording, _recorded_frames
        logger.info("Recording started")
        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32") as s:
                while _recording:
                    d, _ = s.read(SAMPLE_RATE // 10); _recorded_frames.append(d.copy())
        except Exception as e:
            logger.error(f"Recording error: {e}")
            _recording = False
        logger.info(f"Recording stopped: {len(_recorded_frames)} chunks")
    threading.Thread(target=_cap, daemon=True).start()
    return jsonify({"status":"recording"})

@app.route("/record/stop", methods=["POST"])
def record_stop():
    global _recording
    with _record_lock:
        if not _recording: return jsonify({"error":"Not recording"}), 400
        _recording = False
    time.sleep(0.25)
    if not _recorded_frames: return jsonify({"error":"No audio captured — check system microphone"}), 422
    audio = np.concatenate(_recorded_frames, axis=0).flatten()
    dur = len(audio) / SAMPLE_RATE
    logger.info(f"Recorded {dur:.1f}s")
    if dur < 0.5: return jsonify({"error":"Too short — speak for at least 1 second"}), 422
    wav = numpy_to_wav(audio)
    b = request.get_json(force=True, silent=True) or {}
    lang, voice, speed, fmt = b.get("language",DEFAULT_LANGUAGE), b.get("voice","Shivani"), float(b.get("speed",1.0)), b.get("format","transcribe")
    try: transcript = call_stt(wav, lang, fmt)
    except RuntimeError as e: return jsonify({"error":str(e)}), 502
    if not transcript: return jsonify({"error":"Could not understand — speak clearly"}), 422
    reply = get_mock_response() if MOCK_MODE else call_gemini(transcript, lang)
    try: audio_out = call_tts(reply, lang, voice, speed)
    except: audio_out = get_mock_audio()
    return jsonify({"transcript":transcript,"response":reply,
                    "audio_b64":base64.b64encode(audio_out).decode(),"language":lang,"voice":voice,"duration":round(dur,1)})

# ── Standard routes ────────────────────────────────────────────────────────
@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files: return jsonify({"error":"No audio"}), 400
    ab = request.files["audio"].read()
    if not ab: return jsonify({"error":"Empty"}), 400
    lang, fmt = request.form.get("language",DEFAULT_LANGUAGE), request.form.get("format","transcribe")
    try: return jsonify({"transcript":call_stt(ab,lang,fmt),"language":lang})
    except RuntimeError as e: return jsonify({"error":str(e)}), 502

@app.route("/chat", methods=["POST"])
def chat():
    b = request.get_json(force=True, silent=True) or {}
    text, lang = b.get("text","").strip(), b.get("language",DEFAULT_LANGUAGE)
    if not text: return jsonify({"error":"No text"}), 400
    reply = get_mock_response() if MOCK_MODE else call_gemini(text, lang)
    return jsonify({"response":reply})

@app.route("/synthesize", methods=["POST"])
def synthesize():
    b = request.get_json(force=True, silent=True) or {}
    text = b.get("text","").strip()
    if not text: return jsonify({"error":"No text"}), 400
    lang, voice, speed = b.get("language",DEFAULT_LANGUAGE), b.get("voice","Shivani"), float(b.get("speed",1.0))
    try: return Response(call_tts(text,lang,voice,speed), mimetype="audio/wav")
    except RuntimeError as e: return jsonify({"error":str(e)}), 502

@app.route("/voice-pipeline", methods=["POST"])
def voice_pipeline():
    if "audio" not in request.files: return jsonify({"error":"No audio"}), 400
    ab = request.files["audio"].read()
    if not ab: return jsonify({"error":"Empty"}), 400
    lang  = request.form.get("language",DEFAULT_LANGUAGE)
    voice = request.form.get("voice","Shivani")
    speed = float(request.form.get("speed",1.0))
    fmt   = request.form.get("format","transcribe")
    try: transcript = call_stt(ab,lang,fmt)
    except RuntimeError as e: return jsonify({"error":str(e)}), 502
    if not transcript: return jsonify({"error":"Could not transcribe"}), 422
    reply = get_mock_response() if MOCK_MODE else call_gemini(transcript,lang)
    try: ao = call_tts(reply,lang,voice,speed)
    except: ao = get_mock_audio()
    return jsonify({"transcript":transcript,"response":reply,
                    "audio_b64":base64.b64encode(ao).decode(),"language":lang,"voice":voice})

# ── Entry ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mode = "MOCK" if MOCK_MODE else "LIVE"
    logger.info(f"VoiceGenius {mode} | STT: {STT_URL} | TTS: {TTS_URL}")
    app.run(debug=False, host="0.0.0.0", port=5000, use_reloader=False)
