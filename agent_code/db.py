from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import json

from agent_code.output_class import MailInfo

load_dotenv(override=True)

db_connection = os.getenv("DATABASE_URL")
engine = create_engine(db_connection)

def db_query(agent_output):
    create_schema_and_table = text("""
    CREATE SCHEMA IF NOT EXISTS mails;

    CREATE TABLE IF NOT EXISTS mails.agent_output (
        id SERIAL PRIMARY KEY,
        from_sender TEXT,
        date TEXT,
        company_name TEXT,
        role TEXT,
        link TEXT
    );
    """)


    insert_query = text("""
    INSERT INTO mails.agent_output (
        from_sender,
        date,
        company_name,
        role,
        link
    )
    VALUES (
        :from_sender,
        :date,
        :company_name,
        :role,
        :link
    )
    """)

    with engine.begin() as conn:
        conn.execute(create_schema_and_table)
        agent_output = agent_output.model_dump()
        result = conn.execute(insert_query, agent_output)
    return "Inserted in db"

if __name__ == "__main__":
    data = {"from_sender": "Test", "date": "test", "company_name": "test", "role": "test", "link": "test"}
    pydantic_data = MailInfo(**data)
    response = db_query(pydantic_data)
    print(response)