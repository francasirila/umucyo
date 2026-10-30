from pydantic import BaseModel


class UssdRequest(BaseModel):
    phone_number: str
    text: str


class UssdResponse(BaseModel):
    response: str
