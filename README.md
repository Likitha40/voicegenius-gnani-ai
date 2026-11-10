# 🎙️ VoiceGenius — AI Voice Assistant powered by Gnani AI

> **Submission by:** Likitha Lekhya Para
> **Contest:** Great Indian AI Internship Challenge by Gnani AI
> **Deadline:** November 10, 2026

---

## 🤔 What Does This App Do?

**VoiceGenius** is a voice-based AI assistant. Here's exactly how it works in simple steps:

```
YOU SPEAK  →  App LISTENS  →  App UNDERSTANDS  →  AI THINKS  →  App SPEAKS BACK
```

1. 🎤 You **hold the mic button** and speak a question (in English, Hindi, Kannada, etc.)
2. 🧠 Gnani AI's **Prisma** model converts your speech to text
3. 💬 Google **Gemini AI** reads your question and writes a smart reply
4. 🔊 Gnani AI's **Timbre** model converts the reply back into natural speech
5. 🎧 You **hear the answer** spoken aloud in your chosen language

---

## 🛠️ Three AI Models Working Together

| Step | AI Model | What It Does |
|------|----------|--------------|
| 1 — Listen | **Gnani Prisma v3** | Converts your voice to text (Speech-to-Text) |
| 2 — Think | **Google Gemini 1.5 Flash** | Understands your question and writes an answer |
| 3 — Speak | **Gnani Timbre v3** | Converts the answer to natural-sounding voice (Text-to-Speech) |

---

## 🌟 Features at a Glance

| Feature | Details |
|---------|---------|
| 🎤 Push-to-Talk | Hold the mic button to record, release to send |
| 🌍 8 Indian Languages | English, Hindi, Kannada, Tamil, Telugu, Bengali, Marathi, Punjabi |
| 🤖 Auto Language Detect | Use `indic-auto` mode — it detects the language automatically |
| 🗣️ Hinglish Support | Codemix mode for mixed Hindi+English speech |
| 👩 Multiple Voices | Shivani ♀, Avinash ♂, Kalpana, Nalini |
| ⏩ Speed Control | Slow down or speed up the AI's voice (0.5× to 2×) |
| 💬 Chat History | Remembers the full conversation (multi-turn) |
| 📱 Mobile Friendly | Works on phone browsers too |
| 🌙 Dark Theme | Beautiful purple/indigo design |

---

## 📁 Project Folder Structure — What Each File Does

```
gnani-voice-assistant/
│
├── app.py               ← 🐍 THE MAIN SERVER (Python + Flask)
│                            Handles all API calls to Gnani and Gemini
│                            Run this file to start the app
│
├── templates/
│   └── index.html       ← 🌐 THE WEBPAGE (what you see in the browser)
│                            Contains the mic button, chat bubbles, dropdowns
│                            Uses JavaScript to record audio and talk to the server
│
├── static/
│   └── style.css        ← 🎨 THE STYLING
│                            Dark purple theme, animations, responsive layout
│
├── .env                 ← 🔑 YOUR SECRET API KEYS (never share this file!)
│                            GNANI_API_KEY and GEMINI_API_KEY go here
│
├── .env.example         ← 📋 TEMPLATE for the .env file
│                            Shows what variables are needed (without real keys)
│
├── requirements.txt     ← 📦 LIST OF PYTHON PACKAGES needed to run the app
│
└── README.md            ← 📖 THIS FILE
```

---

## ▶️ How to Run the App (Step by Step)

> ✅ **Already done on your machine!** The app is currently running.
> Just open: **http://localhost:5000**

If you ever close the terminal and need to restart:

**Step 1 — Open a terminal (PowerShell or Command Prompt)**

**Step 2 — Go to the project folder:**
```bash
cd "C:\Users\LIKITHA PARA\.gemini\antigravity\scratch\gnani-voice-assistant"
```

**Step 3 — Run the server:**
```bash
python app.py
```

**Step 4 — Open your browser and go to:**
```
http://localhost:5000
```

That's it! 🎉

---

## 🔑 API Keys Explained

Your app uses **2 API keys** (already saved in your `.env` file):

### 1. Gnani API Key (`GNANI_API_KEY`)
- **What it does:** Lets you use Prisma (voice-to-text) and Timbre (text-to-voice)
- **Where to get it:** [app.gnani.ai](https://app.gnani.ai) → API Dashboard → Create Key
- **You have:** 5,000 programme credits (from contest registration)

### 2. Gemini API Key (`GEMINI_API_KEY`)
- **What it does:** Lets you use Google's Gemini AI to answer questions
- **Where to get it:** [aistudio.google.com](https://aistudio.google.com/app/apikey) — Free!
- **Free limit:** 15 requests/minute, plenty for demo

### Your `.env` file looks like this:
```
GNANI_API_KEY=vach_1ytE2C...   ← Gnani key (already set ✅)
GEMINI_API_KEY=AQ.Ab8RN6...    ← Gemini key (already set ✅)
MOCK_MODE=false                 ← LIVE mode (using real APIs ✅)
DEFAULT_LANGUAGE=en-IN          ← Default: English (India)
```

> ⚠️ **NEVER share your `.env` file** or push it to GitHub. It contains private keys.

---

## 🌐 How the App Works Internally (API Flow)

```
Browser (index.html)
    │
    │  You press mic → browser records audio (WebM format)
    │
    ▼
Flask Server (app.py) on localhost:5000
    │
    ├─ POST /voice-pipeline ──────────────────────────────────┐
    │                                                          │
    │   Step 1: Send audio to Gnani Prisma STT                │
    │   URL: https://api.vachana.ai/stt/v3                    │
    │   → Gets back: "What is Gnani AI?"                      │
    │                                                          │
    │   Step 2: Send text to Google Gemini                    │
    │   → Gets back: "Gnani AI is a speech AI company..."     │
    │                                                          │
    │   Step 3: Send reply to Gnani Timbre TTS                │
    │   URL: https://api.vachana.ai/api/v1/tts/inference      │
    │   → Gets back: audio bytes (WAV file)                   │
    │                                                          │
    └──────────────────────────────────────────────────────────┘
    │
    │  Returns: transcript + reply text + audio (base64)
    │
    ▼
Browser plays the audio 🔊
```

---

## 🧪 Individual API Endpoints (for testing)

| Endpoint | Method | What it does |
|----------|--------|--------------|
| `/` | GET | Opens the main page |
| `/health` | GET | Shows if app + keys are working |
| `/voices` | GET | Lists available voices per language |
| `/transcribe` | POST | Voice → Text only |
| `/chat` | POST | Text → AI reply only |
| `/synthesize` | POST | Text → Voice only |
| `/voice-pipeline` | POST | **Full pipeline:** Voice → Text → AI → Voice |

**Test if app is running:**
```
http://localhost:5000/health
```
Should show: `{"status": "ok", "gnani_key": true, "gemini_key": true}`

---

## 🌍 Supported Languages

| Language | Code | Voices Available |
|----------|------|-----------------|
| English (India) | `en-IN` | Shivani ♀, Avinash ♂ |
| Hindi | `hi-IN` | Kalpana ♀, Nalini ♂ |
| Kannada | `kn-IN` | Shivani |
| Tamil | `ta-IN` | Shivani |
| Telugu | `te-IN` | Shivani |
| Bengali | `bn-IN` | Shivani |
| Marathi | `mr-IN` | Shivani |
| Punjabi | `pa-IN` | Shivani |
| Auto-detect (Hinglish) | `indic-auto` | Shivani |

---

## 🏆 Contest Award Categories This Targets

| Award Category | How This App Qualifies |
|---------------|----------------------|
| 🌍 Regional Languages | Supports 8 Indian languages natively |
| 🗣️ Hinglish/Code-Mixed | `indic-auto` + codemix STT mode |
| 🎤 Voice AI | Full end-to-end voice pipeline |
| 💡 Real-World Impact | Helps anyone who can't type — voice-first access to AI |
| 🏙️ Tier 2/3 Towns | Works in local languages, low internet dependency |
| 🎬 60-Second Demo | Simple UI — easy to record a great short demo |

---

## 📹 Steps to Submit Today (Before 11:59 PM)

1. ✅ **Test the app** at `http://localhost:5000`
2. 🎬 **Record a screen video** (use Windows + G or any screen recorder)
   - Show the app opening
   - Hold mic → speak a question in English
   - Show it reply with voice
   - Switch language to Hindi → speak in Hindi
   - Show it reply in Hindi
3. 📤 **Post on LinkedIn or X/Twitter:**
   - Upload the video
   - Add this caption (customize it!):
     ```
     🎙️ I built VoiceGenius — a multilingual AI Voice Assistant 
     using @GnaniAI's Prisma STT + Timbre TTS models!
     
     Supports 8 Indian languages + Hinglish 🇮🇳
     
     #GnaniAI #GreatIndianAIInternshipChallenge #VoiceAI
     ```
4. 📋 **Submit your project** at the [Project Submission Form](https://gnani.ai/internship)

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| App won't start | Make sure you're in the right folder and ran `python app.py` |
| Mic not working | Allow microphone permission in browser (click the 🔒 icon in URL bar) |
| No voice response | Check `.env` has the correct Gnani API key |
| Gemini error | Check `.env` has the correct Gemini API key |
| Browser says "not secure" | Use `http://` not `https://` for localhost |
| Want to test without keys | Set `MOCK_MODE=true` in `.env` and restart |

---

## 👩‍💻 Built By

**Likitha Lekhya Para**
Built for the **Great Indian AI Internship Challenge 2026** by Gnani AI
Using: Gnani Prisma STT + Gnani Timbre TTS + Google Gemini 1.5 Flash

---

*Built with ❤️ for India's voice-first AI future 🇮🇳*
