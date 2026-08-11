import os
from agent_code.gmail_setup import gmail_credentials
from agent_code.utility import save_historyid

HISTORY_ID_FILE = "agent_code/history_id.json"
def gmail_watch():
    if os.path.exists(HISTORY_ID_FILE):
        os.remove(HISTORY_ID_FILE)
        print("Old history tracker file deleted: agent_code/history_id.json")

    gmail = gmail_credentials()
    request = {
    'labelIds': ['INBOX'],
    'topicName': 'projects/mailhunt-500910/topics/mailhunt',
    'labelFilterBehavior': 'INCLUDE'
    }
    response = gmail.users().watch(userId='me', body=request).execute()
    save_historyid(response["historyId"])
    print(f"New watch registered baseline saved: {response}")

if __name__ == "__main__":
    gmail_watch()