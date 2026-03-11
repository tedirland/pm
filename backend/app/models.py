from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class CardCreateRequest(BaseModel):
    column_id: str
    title: str
    details: str = ""
    due_date: str | None = None


class CardUpdateRequest(BaseModel):
    title: str
    details: str = ""
    due_date: str | None = None
    labels: str | None = None


class CardMoveRequest(BaseModel):
    column_id: str
    position: int


class ColumnCreateRequest(BaseModel):
    title: str


class ColumnRenameRequest(BaseModel):
    title: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class BoardCreateRequest(BaseModel):
    title: str = "My Board"


class BoardUpdateRequest(BaseModel):
    title: str
