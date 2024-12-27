from pydantic import BaseModel

class LoginDataSchema(BaseModel):
    email: str
    password: str


class UserDataSchema(BaseModel):
    abf_credentials: LoginDataSchema
