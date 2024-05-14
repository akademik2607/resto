import json
from datetime import datetime, timedelta

from dataworkers.monday import GetTaskStatusBackend
from managers.socket_manager import manager
from redis_settings import redis_client


def find_nearest_date(target_time):
    current_time = datetime.now()
    target_hour, target_minute = target_time.split(':')
    target_datetime = current_time.replace(hour=int(target_hour), minute=int(target_minute), second=0,
                                           microsecond=0)

    if target_datetime < current_time:
        target_datetime += timedelta(days=1)

    return target_datetime


def check_times(board_id, task_list, tag_id):
    print('checking times')
    for task in task_list:
        if task.get('time'):
           status = GetTaskStatusBackend().run(board_id, task.get('id'))
           print('status', status)
           if status == 'נא לבחור':
               result = json.loads(redis_client.get(f'tasks_{tag_id}'))
               for item in result.get('items'):
                   if str(task.get('id')) == str(item.get('id')):
                      item['is_alert'] = True
                   redis_client.set(f'tasks_{tag_id}', json.dumps(result))
    result = json.loads(redis_client.get(f'tasks_{tag_id}'))
    manager.send_role_message(json.dumps(result), tag_id)

