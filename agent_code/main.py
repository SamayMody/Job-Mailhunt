import os
import json
from dotenv import load_dotenv
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.telemetry import StrandsTelemetry
from bs4 import BeautifulSoup


from agent_code.db import db_query
from agent_code.output_class import MailInfo, MailValidation  
from agent_code.gmail_setup import gmail_credentials
from agent_code.prompts import analyser_system_message, system_message
from agent_code.utility import push_notifications, get_plain_text

load_dotenv(override=True)
db_connection = os.getenv("DATABASE_URL")

def extract_info(last_history_id):
    service = gmail_credentials()

    history = service.users().history().list(
        userId="me",
        startHistoryId=last_history_id,
        historyTypes=["messageAdded"]
    ).execute()

    changes = history.get("history", [])
    new_message_ids = []
    for record in changes:
        for added in record.get("messagesAdded", []):
            new_message_ids.append(added["message"]["id"])

    if not new_message_ids:
        return "No messages found."

    msg_id = new_message_ids[-1]

    msg = (
        service.users().messages().get(userId="me", id=msg_id).execute()
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
        print("Not a job related mail")
        return "The email is not a job oppurtunity related mail"

if __name__ == '__main__':
    info = extract_info()
    message = info
    print(run_agent(message))