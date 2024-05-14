from fastapi import APIRouter
from starlette.responses import JSONResponse

from dataworkers.monday import AuthMondayWorker
from models.forms import LoginFormModel

router = APIRouter(
    prefix='/auth',
    tags=['login'],
)


@router.post('/')
async def login(data: LoginFormModel):
    print(data)
    auth_worker = AuthMondayWorker()
    result = auth_worker.check_auth_data(data)
    return JSONResponse(content=result)
