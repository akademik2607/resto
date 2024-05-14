import json

from fastapi import APIRouter
from starlette.responses import JSONResponse

from dataworkers.monday import CreateBoardMondayBackend, LinesBoardMondayBackend
from models.forms import CreateBoardModel

from redis_settings import redis_client
from shedullers import check_times

router = APIRouter(
    prefix='/board'
)


@router.post('/take')
async def create_board(data: CreateBoardModel):
    print(data)
    print('redis check > ', redis_client.get(f'tasks_{data.tag_id}'))
    if not redis_client.get(f'tasks_{data.tag_id}') \
            or len(json.loads(redis_client.get(f'tasks_{data.tag_id}')).get('items')) == 0:
        print('из monday')
        print(data.tag_id)
        print(type(data.tag_id))
        if data.tag_id == 4:
            print('lines')
            result = LinesBoardMondayBackend().run(data.tag_id, data.email)
            redis_client.set(f'tasks_{data.tag_id}', json.dumps(result))
        else:
            print('unlines')
            result = CreateBoardMondayBackend().run(data.tag_id, data.email)
            redis_client.set(f'tasks_{data.tag_id}', json.dumps(result))
            check_times(result.get('id').get('id'), result.get('items'), data.tag_id)
    else:
        print('из redis')
        # print(len(json.loads(redis_client.get(f'tasks_{data.tag_id}')).get('items')))
        result = json.loads(redis_client.get(f'tasks_{data.tag_id}'))
    return JSONResponse(content=result)
