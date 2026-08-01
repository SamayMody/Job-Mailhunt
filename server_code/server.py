from fastapi import FastAPI

from agent_code.main import extract_info, run_agent

app = FastAPI()

@app.post("/gmail/webhook")
async def gmail_webhook():
    message = extract_info()
    if message == "No messages found.":
        return message
    result = run_agent(message)

    return {"status": "processed", "agent_output": result} 