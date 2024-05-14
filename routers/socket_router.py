


# @app.get("/")
# async def get():
#     await manager.broadcast('Новый пользователь собирается подключиться')
#     return HTMLResponse(html)
import json

from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect

from dataworkers.monday import ChangeBoardMondayBackend, ChangeCookMondayBackend, CreateTaskMondayBackend
from managers.socket_manager import manager
from redis_settings import redis_client

router = APIRouter(
    prefix='/ws',
)

TYPES = {
    'TASK_COMPLETE': 'done',
    'TASK_ERROR': 'waiter task error',
    'COOK_INFO': 'cook_info',
    'CREATE_DYNAMIC_TASK': 'create_dynamic_task'
}


@router.websocket("/{role_id}")
async def websocket_endpoint(websocket: WebSocket, role_id: int):
    print('result success')
    await manager.connect(websocket, role_id)

    try:
        while True:
            data = await websocket.receive_text()

            print(data)
            print(json.loads(data))
            data = json.loads(data)
            if data.get('type') == TYPES['TASK_COMPLETE']:

                tasks = json.loads(redis_client.get(f'tasks_{role_id}'))
                tasks['items'] = [item for item in tasks.get('items') if item.get('id') != data.get('task_id')]
                redis_client.set(f'tasks_{role_id}', json.dumps(tasks))
                ChangeBoardMondayBackend().run(tasks.get('id').get('id'), data.get('task_id'), data.get('status'))
                await manager.send_role_message(json.dumps(tasks), role_id)

            if data.get('type') == TYPES['TASK_ERROR']:
                print('task_error')
                print(data)
                tasks = json.loads(redis_client.get(f'tasks_{role_id}'))
                for item in tasks['items']:
                    if item.get('id') == data.get('task_id'):
                        item['comment'] = data.get('comment')
                tasks['items'] = [item for item in tasks.get('items') if item.get('id') != data.get('task_id')]
                redis_client.set(f'tasks_{role_id}', json.dumps(tasks))
                ChangeBoardMondayBackend().run(tasks.get('id').get('id'), data.get('task_id'), data.get('status'), data.get('comment'))
                await manager.send_role_message(json.dumps(tasks), role_id)
            if data.get('type') == TYPES['COOK_INFO']:
                tasks = json.loads(redis_client.get(f'tasks_{role_id}'))
                tasks['items'] = [item for item in tasks.get('items') if item.get('id') != data.get('task_id')]
                redis_client.set(f'tasks_{role_id}', json.dumps(tasks))
                print(data)
                ChangeCookMondayBackend().run(
                    tasks.get('id').get('id'),
                    data.get('task_id'),
                    data.get('morning'),
                    data.get('evening'),
                    data.get('empty'),
                    data.get('description'),
                    data.get('work_shift'),
                    role_id
                )
                await manager.send_role_message(json.dumps(tasks), role_id)
            if data.get('type') == TYPES['CREATE_DYNAMIC_TASK']:
                print('task for', data.get("role_id"))
                print(type(data.get('role_id')))
                tasks = json.loads(redis_client.get(f'tasks_{data.get("role_id")}'))
                task_id = CreateTaskMondayBackend().run(tasks.get('id').get('id'), data.get('task_text', '-'))
                task_id = task_id['data']['create_item']['id']
                tasks['items'].insert(0, {
                    'id': task_id,
                    'name': data.get('task_text', '-'),
                    'author': data.get('author_name'),
                    'author_role_id': data.get('author_role_id'),
                    'is_dyn_task': True,
                    'time': ''
                })
                print(tasks['items'][0])
                redis_client.set(f'tasks_{data.get("role_id")}', json.dumps(tasks))
                print(tasks.get('id').get('id'), task_id)
                print(tasks['items'][0])
                await manager.send_role_message(json.dumps(tasks), data.get("role_id"))
    except Exception as e:
        manager.disconnect(websocket)




# @router.websocket("/{client_id}")
# async def websocket_endpoint(websocket: WebSocket, client_id: int):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await manager.send_personal_message(f"You wrote: {data}", websocket)
#             await manager.broadcast(f"Client #{client_id} says: {data}")
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"Client #{client_id} left the chat")
