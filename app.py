import os
import requests
from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import quote
import uvicorn
import hashlib
import secrets
from typing import Optional

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# MongoDB
client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsAllowInvalidCertificates=True)
db = client["ai_notes_db"]
collection = db["notes"]
users_col = db["users"]
sessions_col = db["sessions"]

# llama.cpp server config
LLAMA_URL = "http://localhost:8080/completion"
model_name = "gemma-3-1b-it"


# ── Auth helpers ──────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(user_id: str) -> str:
    token = secrets.token_hex(32)
    sessions_col.insert_one({"token": token, "user_id": user_id})
    return token

def get_current_user(request: Request) -> Optional[dict]:
    token = request.cookies.get("session")
    if not token:
        return None
    session = sessions_col.find_one({"token": token})
    if not session:
        return None
    try:
        user = users_col.find_one({"_id": ObjectId(session["user_id"])})
    except Exception:
        return None
    if user:
        user["_id"] = str(user["_id"])
    return user


# ── AI ────────────────────────────────────────────────────────
def generate_response(user_message: str):
    try:
        res = requests.post(LLAMA_URL, json={
            "prompt": f"<start_of_turn>user\n{user_message}<end_of_turn>\n<start_of_turn>model\n",
            "n_predict": 512,
            "temperature": 0.7,
            "stop": ["<end_of_turn>"]
        }, timeout=120)
        res.raise_for_status()
        return res.json().get("content", "No response.").strip(), False
    except requests.exceptions.ConnectionError:
        return "llama-server is not running.", True
    except Exception as e:
        return f"AI error: {str(e)}", True


# ── Routes ────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request, error: str = ""):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    notes = list(collection.find({"user_id": str(user["_id"])}, {"_id": 0}).sort("timestamp", -1))
    return templates.TemplateResponse(request=request, name="index.html", context={
        "notes": notes, "total": len(notes),
        "error": error, "model_name": model_name,
        "user": user
    })


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = ""):
    if get_current_user(request):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": error})


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = users_col.find_one({"email": email.lower()})
    if not user or user["password"] != hash_password(password):
        return RedirectResponse(url="/login?error=Invalid+email+or+password", status_code=303)
    token = create_session(str(user["_id"]))
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("session", token, httponly=True, max_age=86400 * 7)
    return response


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, error: str = ""):
    if get_current_user(request):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request=request, name="register.html", context={"error": error})


@app.post("/register")
def register(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if users_col.find_one({"email": email.lower()}):
        return RedirectResponse(url="/register?error=Email+already+registered", status_code=303)
    if len(password) < 6:
        return RedirectResponse(url="/register?error=Password+must+be+at+least+6+characters", status_code=303)
    user_id = ObjectId()
    users_col.insert_one({
        "_id": user_id,
        "name": name,
        "email": email.lower(),
        "password": hash_password(password),
        "joined": datetime.now().strftime("%Y-%m-%d")
    })
    token = create_session(str(user_id))
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("session", token, httponly=True, max_age=86400 * 7)
    return response

@app.get("/logout")
def logout(request: Request):
    token = request.cookies.get("session")
    if token:
        sessions_col.delete_one({"token": token})
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session")
    return response


@app.post("/chat")
def chat(request: Request, message: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    response, is_error = generate_response(message)
    if not is_error:
        collection.insert_one({
            "user_id": str(user["_id"]),
            "message": message,
            "response": response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return RedirectResponse(url="/", status_code=303)
    return RedirectResponse(url=f"/?error={quote(response)}", status_code=303)


@app.post("/clear")
def clear_notes(request: Request):
    user = get_current_user(request)
    if user:
        collection.delete_many({"user_id": str(user["_id"])})
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
