from fastapi import BackgroundTasks, FastAPI, Request

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


async def process_text_message(chat_id: int, text: str):
    print(f"Processing text message from {chat_id}: {text}")


async def process_document_message(chat_id: int, document: dict):
    print(f"Processing document from {chat_id}: {document}")


@app.post("/webhook")
async def webhook(background_tasks: BackgroundTasks, request: Request):
    body = await request.json()
    message = body.get("message")
    if not message:
        return {"ok": True}

    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return {"ok": True}
    if "text" in message:
        background_tasks.add_task(process_text_message, chat_id, message["text"])
    elif "document" in message:
        background_tasks.add_task(
            process_document_message, chat_id, message["document"]
        )

    return {"ok": True}
