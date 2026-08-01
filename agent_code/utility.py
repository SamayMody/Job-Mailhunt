import os
from dotenv import load_dotenv
import requests
import json
import pyshorteners
from agent_code.output_class import MailInfo
from bs4 import BeautifulSoup
import base64

load_dotenv(override=True)

def url_shortner(long_url: str):
    """To reduce the length og the application link

    Args:
        long_url: the long link to application
     """

    pyshortener  = pyshorteners.Shortener()
    result = pyshortener.isgd.short(long_url)

    if result.lower().startswith("error"):
        return long_url
        
    return result

def push_notifications(agent_output):
    agent_output = agent_output.model_dump()
    pushover_url = "https://api.pushover.net/1/messages.json"
    pushover_apiKey = os.getenv("PUSHOVER_API_KEY")
    pushover_user = os.getenv("PUSHOVER_USER_KEY")

    payload = {
        "token": pushover_apiKey,
        "user": pushover_user,
        "title": f"{agent_output['role']} at {agent_output['company_name']}",
        "message": f"<a href={agent_output['link']}>Apply now</a>",
        "html": 1,
        "sound": "tugboat"
    }

    requests.post(url=pushover_url, data=payload)
    return "Notification sent"

def get_plain_text(payload):
    # Recurse through multipart structures, preferring text/plain
    if 'parts' in payload:
        html_fallback = None
        for part in payload['parts']:
            text = get_plain_text(part)
            if isinstance(text, tuple) and text[0] == 'html':
                html_fallback = text[1]
            elif text:
                return text
        return html_fallback

    mime_type = payload.get('mimeType')
    body_data = payload.get('body', {}).get('data', '')

    if mime_type == 'text/plain' and body_data:
        return base64.urlsafe_b64decode(body_data).decode('utf-8')

    if mime_type == 'text/html' and body_data:
        html = base64.urlsafe_b64decode(body_data).decode('utf-8')
        return ('html', html)   # tagged so caller knows to fall back to this only if no plain text found

    return None

if __name__ == '__main__':
    print(url_shortner("https://en.wikipedia.org/wiki/Main_Page"))

    data = {"from_sender": "Test", "date": "test", "company_name": "test", "role": "test", "link": "https://is.gd/cjvxKD"}
    pydantic_data = MailInfo(**data)
    print(push_notifications(pydantic_data))


