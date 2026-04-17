import os
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from excel_handler import save_student
from email_handler import send_email

load_dotenv()

app = FastAPI(title="XploreiT Corp Voice Agent", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Vapi Config ────────────────────────────────────────────────────────────────
VAPI_PRIVATE_KEY = os.getenv("VAPI_PRIVATE_KEY")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")  # Add this in .env!

VAPI_HEADERS = {
    "Authorization": f"Bearer {VAPI_PRIVATE_KEY}",
    "Content-Type":  "application/json",
}


# ── Models ─────────────────────────────────────────────────────────────────────
class StudentForm(BaseModel):
    name:   str
    email:  str = ""
    phone:  str
    course: str


# ── Vapi Outbound Call ─────────────────────────────────────────────────────────
async def make_vapi_call(student: StudentForm) -> dict:
    """
    Vapi REST API → outbound phone call to student.
    Phone must be E.164 format: +91XXXXXXXXXX
    """
    payload = {
        "assistantId": VAPI_ASSISTANT_ID,
        "customer": {
            "number": student.phone,
            "name":   student.name,
        },
        "assistantOverrides": {
            "firstMessage": (
                f"Hello {student.name}! Naan XploreiT Corp-oda AI assistant. "
                f"Neenga {student.course} course-la interest irukeenga nu theriyuthu. "
                f"Ungalukku enna help pannalam?"
            ),
            "variableValues": {
                "student_name":   student.name,
                "student_course": student.course,
            },
        },
    }

    # phoneNumberId required for outbound calls
    if VAPI_PHONE_NUMBER_ID:
        payload["phoneNumberId"] = VAPI_PHONE_NUMBER_ID

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            "https://api.vapi.ai/call/phone",
            headers=VAPI_HEADERS,
            json=payload,
        )

    if res.status_code in (200, 201):
        data = res.json()
        print(f"[Vapi] Call started → {student.phone} | id: {data.get('id')}")
        return {"success": True, "call_id": data.get("id"), "status": data.get("status")}
    else:
        print(f"[Vapi] Failed → {res.status_code} | {res.text}")
        return {"success": False, "error": res.text, "code": res.status_code}


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "XploreiT Corp Voice Agent v2.0 running!"}


@app.get("/test-vapi")
async def test_vapi():
    """Quick check — Vapi API key + assistant valid-a?"""
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(
            f"https://api.vapi.ai/assistant/{VAPI_ASSISTANT_ID}",
            headers=VAPI_HEADERS,
        )
    if res.status_code == 200:
        data = res.json()
        return {
            "status":       "Vapi connected!",
            "assistant":    data.get("name", "Unknown"),
            "assistant_id": VAPI_ASSISTANT_ID,
        }
    return {"status": "Failed", "code": res.status_code, "error": res.text}


@app.post("/submit")
async def submit_student(student: StudentForm):
    """
    Form submit:
    1. Save to Excel
    2. Send email notification
    3. Trigger Vapi outbound call to student
    """
    results = {"excel": False, "email": False, "call": None}

    # 1. Save Excel
    try:
        save_student(student.name, student.email,
                     student.phone, student.course)
        results["excel"] = True
        print(f"[Excel] Saved: {student.name}")
    except Exception as e:
        print(f"[Excel] Error: {e}")

    # 2. Send Email
    try:
        send_email(student.name, student.email, student.phone, student.course)
        results["email"] = True
        print(f"[Email] Sent for: {student.name}")
    except Exception as e:
        print(f"[Email] Error: {e}")

    # 3. Vapi Outbound Call
    try:
        call_result = await make_vapi_call(student)
        results["call"] = call_result
    except Exception as e:
        print(f"[Vapi] Exception: {e}")
        results["call"] = {"success": False, "error": str(e)}

    call_ok = results["call"] and results["call"].get("success")

    if call_ok:
        return {
            "status":  "success",
            "message": f"Form saved! Call initiated to {student.phone}",
            "call_id": results["call"].get("call_id"),
            "details": results,
        }
    else:
        err = results["call"].get(
            "error", "Unknown") if results["call"] else "Unknown"
        return {
            "status":  "partial",
            "message": f"Form saved but call failed: {err}",
            "details": results,
        }


@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    """
    Vapi call events receiver.
    Vapi Dashboard → Assistant → Server URL → http://YOUR_IP:8000/vapi-webhook
    """
    payload = await request.json()
    event = payload.get("type", "unknown")
    call_id = payload.get("call", {}).get("id", "")

    print(f"[Webhook] {event} | {call_id}")

    if event == "end-of-call-report":
        summary = payload.get("summary", "")
        customer = payload.get("call", {}).get(
            "customer", {}).get("number", "")
        print(f"[Webhook] Call ended: {customer} | Summary: {summary[:200]}")

    return {"received": True}


@app.get("/call-status/{call_id}")
async def call_status(call_id: str):
    """Check status of a specific call."""
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(
            f"https://api.vapi.ai/call/{call_id}",
            headers=VAPI_HEADERS,
        )
    if res.status_code == 200:
        data = res.json()
        return {
            "call_id":  call_id,
            "status":   data.get("status"),
            "ended_at": data.get("endedAt"),
        }
    return {"error": "Not found", "code": res.status_code}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
