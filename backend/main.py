from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse

import requests
import os
from dotenv import load_dotenv

# ===== LOAD ENV =====
load_dotenv()

app = FastAPI()

# ===== RATE LIMITER =====
limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: JSONResponse(
        status_code=429,
        content={"reply": "⚠️ Too many requests! Slow down miner ⛏️"}
    ),
)
app.add_middleware(SlowAPIMiddleware)

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== API KEY =====
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ===== SYSTEM PROMPT =====
SYSTEM_PROMPT = """You are Shivansh Saxena.
Answer in first person as Shivansh.
Keep responses short, confident, and slightly Minecraft-themed occasionally.
Talk about projects, skills, and portfolio like a developer.
"""

# ===== CHAT ENDPOINT =====
@app.post("/chat")
@limiter.limit("10/minute")  # 🔥 10 requests per minute per IP
async def chat(request: Request):
    data = await request.json()
    print("Incoming:", data)

    messages = data.get("messages", [])

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openrouter/auto",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *messages
                ],
                "max_tokens": 20,
            },
            timeout=10
        )
        if not OPENROUTER_API_KEY:
            return {"reply": "⚠️ API key not configured"}
        result = response.json()
        print("OpenRouter response:", result)

        # ✅ HANDLE ERROR SAFELY
        
        if not response.ok:
            return {
                "reply": f"⚠️ API Error: {result.get('error', {}).get('message', 'Request failed')}"
            }

        if "choices" not in result:
            return {"reply": "⚠️ Invalid response from AI"}

                # ✅ EXTRACT RESPONSE SAFELY
        bot_reply = result["choices"][0]["message"]["content"]

        return {
            "reply": bot_reply
        }

    except Exception as e:
        print("Server Error:", str(e))
        return {
            "reply": f"⚠️ Server Error: {str(e)}"
        }

# ===== ROOT (OPTIONAL) =====
@app.get("/")
def home():
    return {"message": "Backend is running 🚀"}