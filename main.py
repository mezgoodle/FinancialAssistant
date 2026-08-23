import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agent.assistant import FinancialAssistantAgent
from src.config import HOST, PORT

app = FastAPI(title="Financial Assistant AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Lazy agent instance
_agent: Optional[FinancialAssistantAgent] = None


def get_agent() -> FinancialAssistantAgent:
    global _agent
    if _agent is None:
        _agent = FinancialAssistantAgent()
    return _agent


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Financial Assistant AI"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Повідомлення не може бути порожнім.")
    
    try:
        agent = get_agent()
        reply = agent.send_message(request.message)
        return ChatResponse(reply=reply)
    except Exception as e:
        return ChatResponse(reply=f"⚠️ Помилка обробки запиту: {str(e)}")


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename or "upload.csv"
    ext = Path(filename).suffix.lower()
    
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400,
            detail="Непідтримуваний формат файлу. Будь ласка, завантажте .csv або .xlsx файл.",
        )

    file_path = UPLOAD_DIR / filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Ingest file message into agent
    agent = get_agent()
    prompt = f"Я завантажив файл '{filename}' (шлях: '{file_path.as_posix()}'). Будь ласка, імпортуй та проаналізуй його транзакції."
    try:
        reply = agent.send_message(prompt)
    except Exception as e:
        reply = f"Файл збережено за шляхом `{file_path}`. Помилка виклику агента: {str(e)}"

    return {
        "filename": filename,
        "saved_path": str(file_path),
        "reply": reply,
    }


@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial Assistant AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        .prose table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }
        .prose th, .prose td { border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }
        .prose th { background-color: #f8fafc; font-weight: 600; }
        .prose tr:nth-child(even) { background-color: #f1f5f9; }
        .chat-bubble { animation: fadeIn 0.25s ease-in-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 flex flex-col h-screen font-sans">
    <!-- Header -->
    <header class="bg-slate-800/80 backdrop-blur border-b border-slate-700 px-6 py-4 flex items-center justify-between shadow">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center font-bold text-xl shadow-lg">
                💰
            </div>
            <div>
                <h1 class="text-lg font-bold text-white tracking-wide">Financial Assistant AI</h1>
                <p class="text-xs text-emerald-400 font-medium">Google ADK & Gemini Engine</p>
            </div>
        </div>
        <div class="flex items-center space-x-3">
            <label class="cursor-pointer bg-slate-700 hover:bg-slate-600 transition text-sm font-medium px-4 py-2 rounded-lg border border-slate-600 flex items-center space-x-2">
                <span>📎 Завантажити CSV/XLSX</span>
                <input id="file-input" type="file" accept=".csv,.xlsx,.xls" class="hidden" onchange="uploadFile(event)">
            </label>
        </div>
    </header>

    <!-- Chat Container -->
    <main class="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 max-w-4xl w-full mx-auto" id="chat-box">
        <div class="chat-bubble flex space-x-3 bg-slate-800 border border-slate-700/60 p-4 rounded-2xl max-w-2xl shadow-sm">
            <div class="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-sm shrink-0">AI</div>
            <div class="prose prose-invert text-sm text-slate-200 leading-relaxed">
                Привіт! Я ваш персональний фінансовий асистент. 📊<br><br>
                Ви можете завантажити виписку (CSV або Excel від <b>Monobank</b>, <b>ПриватБанк</b> або <b>Money Manager</b>) або поставити будь-яке питання про ваші витрати та доходи.
            </div>
        </div>
    </main>

    <!-- Quick Prompts Bar -->
    <div class="max-w-4xl w-full mx-auto px-4 pb-2 flex flex-wrap gap-2 text-xs">
        <button onclick="sendQuickPrompt('Скільки я витратив цього місяця?')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-full border border-slate-700 transition">📅 Витрати цього місяця</button>
        <button onclick="sendQuickPrompt('Які мої найбільші категорії витрат за останній місяць?')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-full border border-slate-700 transition">🏷️ Топ категорій</button>
        <button onclick="sendQuickPrompt('Порівняй витрати за цей місяць і минулий місяць.')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-full border border-slate-700 transition">📈 Порівняння з минулим місяцем</button>
    </div>

    <!-- Input Bar -->
    <footer class="bg-slate-800/80 border-t border-slate-700 p-4">
        <div class="max-w-4xl mx-auto flex items-center space-x-3">
            <input id="user-input" type="text" placeholder="Запитайте щось про ваші фінанси..." 
                class="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-emerald-500 transition text-slate-100 placeholder-slate-500"
                onkeydown="if(event.key === 'Enter') sendMessage()">
            <button id="send-btn" onclick="sendMessage()" 
                class="bg-emerald-600 hover:bg-emerald-500 active:scale-95 transition text-white px-5 py-3 rounded-xl font-medium text-sm flex items-center space-x-1 shadow-md">
                <span>Надіслати</span>
                <span>➔</span>
            </button>
        </div>
    </footer>

    <script>
        const chatBox = document.getElementById('chat-box');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');

        function appendMessage(sender, text, isMarkdown = true) {
            const isUser = sender === 'user';
            const div = document.createElement('div');
            div.className = `chat-bubble flex space-x-3 p-4 rounded-2xl max-w-2xl shadow-sm ${isUser ? 'ml-auto bg-emerald-700 text-white' : 'bg-slate-800 border border-slate-700/60 text-slate-200'}`;
            
            const avatar = isUser ? '' : '<div class="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-sm shrink-0">AI</div>';
            const content = isMarkdown ? marked.parse(text) : text;
            
            div.innerHTML = `${avatar}<div class="prose prose-invert text-sm leading-relaxed overflow-x-auto">${content}</div>`;
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function sendMessage() {
            const text = userInput.value.trim();
            if (!text) return;
            
            appendMessage('user', text, false);
            userInput.value = '';
            userInput.disabled = true;
            sendBtn.disabled = true;

            const loadingDiv = document.createElement('div');
            loadingDiv.id = 'loading-indicator';
            loadingDiv.className = 'chat-bubble flex items-center space-x-2 text-slate-400 text-sm p-4';
            loadingDiv.innerHTML = '<span class="animate-spin text-emerald-400">⏳</span> <span>Асистент аналізує дані...</span>';
            chatBox.appendChild(loadingDiv);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await res.json();
                document.getElementById('loading-indicator')?.remove();
                appendMessage('ai', data.reply || 'Немає відповіді.');
            } catch (err) {
                document.getElementById('loading-indicator')?.remove();
                appendMessage('ai', '⚠️ Помилка з'єднання із сервером: ' + err.message, false);
            } finally {
                userInput.disabled = false;
                sendBtn.disabled = false;
                userInput.focus();
            }
        }

        function sendQuickPrompt(promptText) {
            userInput.value = promptText;
            sendMessage();
        }

        async function uploadFile(event) {
            const file = event.target.files[0];
            if (!file) return;

            appendMessage('user', `📁 Завантаження файлу: **${file.name}**...`);
            
            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                appendMessage('ai', data.reply || `✅ Файл **${file.name}** успішно оброблено!`);
            } catch (err) {
                appendMessage('ai', '⚠️ Помилка завантаження файлу: ' + err.message, false);
            } finally {
                event.target.value = '';
            }
        }
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
