from fastapi import FastAPI, Request
import base64
import json
from agent_code.main import extract_info, run_agent
from agent_code.utility import last_historyid, save_historyid

app = FastAPI()

@app.post("/gmail/webhook")
async def gmail_webhook(request: Request):
    envelope = await request.json()
    data = json.loads(base64.b64decode(envelope["message"]["data"]).decode())
    new_historyid = data["historyId"]
    old_historyid = last_historyid()
    if old_historyid == None:
        save_historyid(new_historyid)
        return "Initialized history tracking"

    message = extract_info(old_historyid)
    save_historyid(new_historyid)
    
    if message == "No messages found.":
        return message
    result = run_agent(message)

    return {"status": "processed", "agent_output": result} 