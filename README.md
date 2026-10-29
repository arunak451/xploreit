# 🎙️ AI Voice Agent for Student Admissions

An AI voice assistant that calls prospective students, answers their questions about courses, fees and admissions, and logs every enquiry. When a student submits the enquiry form, the system saves their details, notifies the admissions team by email, and places an outbound AI phone call to the student within seconds.

## Architecture

```
Enquiry form (index.html)
        │
        ▼
FastAPI server (server.py)
   ├── Save lead to Excel          (excel_handler.py)
   ├── Email notification via Gmail (email_handler.py)
   └── Outbound AI call via Vapi    ──► Student's phone
                                          │
                                   Webhook: call events & summary

Live voice agent (agent.py, LiveKit)
   Silero VAD → Deepgram STT → Llama 3.1 (Groq) + RAG context → Deepgram TTS
                                     ▲
                    Knowledge base (rag.py)
          Website pages scraped → chunked → ChromaDB (MiniLM embeddings)
```

## Features

- **Real-time voice conversation:** speech-to-text, LLM dialogue and text-to-speech in one LiveKit agent session
- **RAG knowledge base:** scrapes the institute website, embeds it into ChromaDB and grounds the agent's answers in real course and admission information
- **Automated outbound calls:** a form submission triggers a personalised Vapi phone call greeting the student by name and course
- **Bilingual:** responds in English or Tamil based on the caller's preference
- **Lead management:** every enquiry saved to Excel and emailed to the team
- **Call tracking:** webhook receives call events and end-of-call summaries; endpoint to check call status

## Tech stack

| Layer | Tools |
|-------|-------|
| Voice agent | LiveKit Agents, Silero VAD |
| Speech-to-text / Text-to-speech | Deepgram (STT, Aura TTS) |
| LLM | Llama 3.1 8B Instant via Groq |
| RAG | ChromaDB, Sentence Transformers (all-MiniLM-L6-v2), BeautifulSoup |
| Telephony | Vapi |
| Backend | FastAPI, httpx, Pydantic |
| Integrations | Gmail SMTP, openpyxl |

## API endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/submit` | Save enquiry, send email, start AI call |
| `POST` | `/vapi-webhook` | Receive call events and summaries |
| `GET` | `/call-status/{call_id}` | Check a call's status |
| `GET` | `/test-vapi` | Verify the Vapi assistant connection |

## Setup

```bash
git clone https://github.com/arunak451/xploreit.git
cd xploreit
pip install fastapi uvicorn httpx python-dotenv openpyxl requests beautifulsoup4 chromadb sentence-transformers \
            "livekit-agents" livekit-plugins-deepgram livekit-plugins-groq livekit-plugins-silero
```

Create a `.env` file (never commit it):

```env
VAPI_PRIVATE_KEY=your_vapi_private_key
VAPI_ASSISTANT_ID=your_vapi_assistant_id
VAPI_PHONE_NUMBER_ID=your_vapi_phone_number_id
DEEPGRAM_API_KEY=your_deepgram_key
GROQ_API_KEY=your_groq_key
GMAIL_USER=your_email@gmail.com
GMAIL_PASSWORD=your_gmail_app_password
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_key
LIVEKIT_API_SECRET=your_livekit_secret
```

## Run

```bash
# Enquiry + outbound call server
python server.py

# Live voice agent
python agent.py dev
```

Open `index.html` in a browser to submit an enquiry and receive the AI call.
