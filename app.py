from fastapi import FastAPI, Body, Request
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from dataworkers.monday import AuthMondayWorker, CreateBoardMondayBackend, ChangeBoardMondayBackend
from models.forms import LoginFormModel, CreateBoardModel, ChangeTaskStatusModel


from routers.login import router as login_router
from routers.socket_router import router as websocket_router
from routers.board import router as board_router


import logging

from fastapi import FastAPI
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles


app = FastAPI(

)


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login_router)
app.include_router(websocket_router)
app.include_router(board_router)


@app.get("/")
async def index():
    return RedirectResponse(url="./build/index.html")


@app.post('/change-task-status')
async def change_task_status(data: ChangeTaskStatusModel):
    print('test')
    print(data)
    result = ChangeBoardMondayBackend().run(data.board_id, data.item_id, data.status)
    return JSONResponse(content=result)









