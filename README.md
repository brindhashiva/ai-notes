# AI Notes App

A full-stack AI-powered chat application built with FastAPI, MongoDB Atlas, and a local LLM (Gemma 3 via llama.cpp).

---

## Features

- User authentication — Register, Login, Logout
- Chat with a local LLM (Gemma 3 1B via llama-server)
- Chat history saved per user in MongoDB Atlas
- Dashboard with stats and recent conversations
- Profile page with account info
- Dark / Light theme toggle
- Markdown rendering in AI responses

---

## Screenshots

### Register
![Register](screenshots/register-page.png)

### Login
![Login](screenshots/login-page.png)

### Chat
![Chat](screenshots/chat-demo.png)

### Profile
![Profile](screenshots/profile-page.png)

### MongoDB — Notes Collection
![MongoDB Notes](screenshots/mongodb_notes.png)

### MongoDB — Users Collection
![MongoDB Users](screenshots/mongodb_users.png)

---

## Project Structure

```
ai-notes/
├── app.py
├── .env
├── requirements.txt
├── templates/
│   ├── index.html
│   ├── login.html
│   └── register.html
├── screenshots/
└── README.md
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure `.env`
```env
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/
GEMINI_API_KEY=your_key_here
```

### 3. Start the local LLM server
```bash
llama-server -hf ggml-org/gemma-3-1b-it-GGUF --port 8080
```

### 4. Run the app
```bash
python app.py
```

Open http://127.0.0.1:8000

---

## Tech Stack

| Layer     | Technology                       |
|-----------|----------------------------------|
| Backend   | Python, FastAPI                  |
| Frontend  | HTML, CSS, Jinja2, marked.js     |
| Database  | MongoDB Atlas                    |
| AI Model  | Gemma 3 1B (llama.cpp, local)    |
| Auth      | Session cookies, SHA-256         |

---

## MongoDB Collections

### users
| Field    | Type   | Description             |
|----------|--------|-------------------------|
| name     | string | Full name               |
| email    | string | Unique email            |
| password | string | SHA-256 hashed          |
| joined   | string | Registration date       |

### notes
| Field     | Type   | Description             |
|-----------|--------|-------------------------|
| user_id   | string | Reference to user       |
| message   | string | User message            |
| response  | string | AI response             |
| timestamp | string | Date and time           |

---

## Security

- Passwords hashed with SHA-256
- Sessions use secure random tokens stored in MongoDB
- Secrets loaded from `.env` — never hardcoded
- `.env` is in `.gitignore`

---

## License

MIT
