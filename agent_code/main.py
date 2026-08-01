import os
import base64
import json
from dotenv import load_dotenv
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.telemetry import StrandsTelemetry
from googleapiclient.discovery import build
from bs4 import BeautifulSoup


from agent_code.db import db_query
from agent_code.output_class import MailInfo, MailValidation  
from agent_code.gmail_setup import gmail_credentials
from agent_code.prompts import analyser_system_message, system_message
from agent_code.utility import push_notifications, get_plain_text

load_dotenv(override=True)
db_connection = os.getenv("DATABASE_URL")

def extract_info():
    service = gmail_credentials()
    results = (
        service.users().messages().list(userId="me", maxResults=1).execute()
    )
    messages = results.get("messages", [])

    if not messages:
        return "No messages found."

    for message in messages:
        print(f'Message ID: {message["id"]}')
        msg = (
            service.users().messages().get(userId="me", id=message["id"]).execute()
        )

        headers = msg['payload']['headers']
        subject = next(h['value'] for h in headers if h['name'].lower() == 'subject')
        sender = next(h['value'] for h in headers if h['name'].lower() == 'from')
        date = next(h['value'] for h in headers if h['name'].lower() == 'date')

        result = get_plain_text(msg['payload'])

        if isinstance(result, tuple) and result[0] == 'html':
            soup = BeautifulSoup(result[1], 'html.parser')
            clean_text = soup.get_text(separator='\n', strip=True)
        elif result:
            clean_text = result
        else:
            clean_text = "(no body found)"
        # To get the full body text (if available in the payload)
        # parts = msg['payload'].get('parts', [])
        # for part in parts:
        #     if part['mimeType'] == 'text/plain':
        #         body_data = part['body'].get('data', '')
        #         clean_text = base64.urlsafe_b64decode(body_data).decode('utf-8')
    # we have date, subject, sender, clean_text

    extracted_information = {
    "from": sender,
    "date": date,
    "subject": subject,
    "body": clean_text
    }

    mail_info = json.dumps(extracted_information)
    return {"subject": subject, "mail_info": mail_info} 

def run_agent(extracted_info):
    openai = os.getenv("OPENAI_API_KEY")
    model = OpenAIModel(
        client_args={
            "api_key": openai
        },
        model_id="gpt-4o-mini"
    )
    strands_telemetry = StrandsTelemetry()
    strands_telemetry.setup_otlp_exporter() # Send traces to OTLP endpoint
    
    analyser_agent = Agent(model=model, system_prompt=analyser_system_message, structured_output_model=MailValidation)
    analyser_agent_run = analyser_agent(extracted_info["subject"])
    analyser_agent_result = analyser_agent_run.structured_output

    if analyser_agent_result.valid_mail:
        worker_agent = Agent(model=model, system_prompt=system_message, structured_output_model=MailInfo)
        worker_agent_run = worker_agent(extracted_info["mail_info"])
        worker_agent_result = worker_agent_run.structured_output

        db_insert = db_query(worker_agent_result)
        print(db_insert)
        push_noti = push_notifications(worker_agent_result)
        print(push_noti)
        

        return worker_agent_result

    else:
        return "The email is not a job oppurtunity related mail"

if __name__ == '__main__':
    info = extract_info()
    message = info
    print(run_agent(message))