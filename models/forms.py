from typing import List

from pydantic import BaseModel


class LoginFormModel(BaseModel):
    email: str
    password: str


class AuthUserModel(BaseModel):
    email: str = None
    password: str = None
    tags: List[int] = None
    id: str = None


class CreateBoardModel(BaseModel):
    tag_id: int = None
    email: str = None


class ChangeTaskStatusModel(BaseModel):
    board_id: str = None
    item_id: int = None
    status: str = None
