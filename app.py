from fastapi import FastAPI, Body, Request
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from dataworkers.monday import AuthMondayWorker, CreateBoardMondayBackend, ChangeBoardMondayBackend
from models.forms import LoginFormModel, CreateBoardModel, ChangeTaskStatusModel




import logging

from fastapi import FastAPI
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles


app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def index():
    return RedirectResponse(url="./build/index.html")

# app.mount("/", StaticFiles(directory="build/static/ui/"), name="ui")


@app.post('/login')
async def login(data: LoginFormModel):
    print(data)
    auth_worker = AuthMondayWorker()
    result = auth_worker.check_auth_data(data)
    return JSONResponse(content=result)


@app.post('/create-board')
async def create_board(data: CreateBoardModel):
    print(data)
    result = CreateBoardMondayBackend().run(data.tag_id, data.email)
    return JSONResponse(content=result)


@app.post('/change-task-status')
async def change_task_status(data: ChangeTaskStatusModel):
    print('test')
    print(data)
    result = ChangeBoardMondayBackend().run(data.board_id, data.item_id, data.status)
    return JSONResponse(content=result)


