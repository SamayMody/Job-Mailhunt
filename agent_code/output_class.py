from pydantic import BaseModel, Field

class MailValidation(BaseModel):
    """ Model that contains information where it is a valid mail or not"""
    valid_mail: bool = Field(description="The email is job related or not")

class MailInfo(BaseModel):
    """Model that contains information about a particular mail """
    from_sender: str = Field(description="The sender of the mail")
    date: str = Field(description="The date of the mail")
    company_name: str = Field(description="The name of the company")
    role: str = Field(description="The job role")
    link: str | None = Field(description="The link to application")
