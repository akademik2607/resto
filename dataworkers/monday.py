import json
import os
import time

from graphql_query import Query, Operation, Argument, Field

from models.forms import LoginFormModel, AuthUserModel
import requests
from dotenv import load_dotenv
import datetime

from settings import EMPLOYEES

load_dotenv()

TAG_BOARD_IDS = {
    EMPLOYEES['BAR']: {
        'template': '6491006289',
        'folder': '14092820'
    },   #Бар
    EMPLOYEES['HOTLINE']: {
        'template': '6435726538',
        'folder': '14092831'
    },  #Горячая полоса
    EMPLOYEES['COLDLINE']: {
        'template': '6491000334',
        'folder': '14092833'
    },         #Холодная полоса
    EMPLOYEES['SUPERVISOR']: {
        'template': '6491020502',
        'folder': '14092825'
    },           #см
    EMPLOYEES['DIRECTOR']: {
        'template': '6491013724',
        'folder': '14092828'
    },   #Директор
    EMPLOYEES['WAITER']: {
        'template': '6240196911',
        'folder': '14115969'
    },              #Офицант
    EMPLOYEES['CHECKER']: {
        'template': '6491025411',
        'folder': '14092835'
    },    #Чекер
    EMPLOYEES['CLEANER']: {
        'template': '6491028745',
        'folder': '14092836',
    },             #Уборщик
    EMPLOYEES['HOSTESS']: {
        'template': '6491030859',
        'folder': '14092837'
    },             #Хостес
}


WORK_SHIFTS = {
    'morning': 'ערב',
    'evening': 'בוקר'
}

# {
#     'index': 3,
#     'value': 'בר'
#   },
#   {
#     'index': 4,
#     'value':'פס חם'
#   },
#   {
#     'index': 5,
#     'value': 'פס קר'
#   },
#   {
#     'index': 6,
#     'value':'אחמ"ש'
#   },
#   {
#     'index': 7,
#     'value':'מנהל'
#   },
#   {
#     'index': 8,
#     'value':'מלצר'
#   },
#   {
#     'index': 9,
#     'value':"צ'קר"
#   },
#   {
#     'index': 10,
#     'value':'ניקיון'
#   },
#   {
#     'index': 11,
#     'value':'הוסטס'
#   },



class AuthMondayBackend:

    def __init__(self):
        self.token = os.getenv('MONDAY_API_TOKEN')
        self.api_url = 'https://api.monday.com/v2'
        self.headers = {"Authorization": self.token, "API-Version": "2023-04"}
        self.query_data = ''
        self.row_data = ''
        self.data = ''

    def _auth_info_query(self):
        board_ids = Argument(name="ids", value='6271518251')
        column_values = Argument(name="ids", value=['"id"', '"status"', '"email"', '"text"', '"dropdown"'])

        auth_user = Query(
            name='boards',
            arguments=[board_ids],
            fields=[
                Field(
                    name='items_page',
                    fields=[
                        Field(
                            name='items',
                            fields=[
                                'name',
                                Field(
                                    name='column_values',
                                    arguments=[column_values],
                                    fields=[
                                        'id',
                                        'text',
                                        'value'
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ])
        operation = Operation(type='query', queries=[auth_user])
        # print(operation.render())
        self.query_data = operation.render()

    def _get_query(self):
        self.data = {'query': self.query_data}
        return requests.post(url=self.api_url, json=self.data, headers=self.headers)

    def _get_emails_passwords_tags(self):
        items = self.row_data.get('data').get('boards')[0].get('items_page').get('items')
        # print(items)
        users = []
        for item in items:
            user = AuthUserModel()
            user.username = item.get('name')
            for column in item.get('column_values'):
                if column.get('id') == 'email':
                    user.email = column.get('text')
                elif column.get('id') == 'text':
                    user.password = column.get('value')
                elif column.get('id') == 'dropdown':
                    user.tags = column.get('value')
                elif column.get('id') == 'id':
                    user.id = column.get('value')
                elif column.get('id') == 'status':
                    user.status = column.get('text')
            if not user.email or not user.password or not user.tags:
                continue
            users.append(user)
            print(user)
        return users

    def run(self):
        self._auth_info_query()
        # print(self._get_query().json())
        self.row_data = self._get_query().json()
        users = self._get_emails_passwords_tags()
        return users


class AuthMondayWorker:
    def __init__(self):
        pass

    @staticmethod
    def check_auth_data(data: LoginFormModel=None):
        backend = AuthMondayBackend()
        users = backend.run()
        for user in users:
            print(user)
            if data.email == user.email and data.password == user.password.strip('"') and user.status == 'פעיל':
                return json.dumps({
                    'message': 'success',
                    'tags': user.tags,
                    'id': user.id,
                    'email': user.email,
                    'username': user.username})
        print('send ', json.dumps({'message': 'User not found!', 'error': True}))
        return json.dumps({'message': 'User not found!', 'error': True})


class CreateBoardMondayBackend:
    def __init__(self):
        self.token = os.getenv('MONDAY_API_TOKEN')
        self.api_url = 'https://api.monday.com/v2'
        self.headers = {"Authorization": self.token, "API-Version": "2023-04"}
        self.query_data = ''
        self.row_data = ''
        self.data = ''

    def _create_board_mutation_query(self, tag_id, email):
        create_board = Query(
            name="create_board",
            arguments=[
                # Argument(name="template_id", value=6240196911),
                Argument(name="template_id", value=TAG_BOARD_IDS[tag_id]['template']),
                Argument(name="board_name", value=f'"{datetime.date.today()}-{email}"'),
                Argument(name="board_kind", value="public"),
                Argument(name="folder_id", value=TAG_BOARD_IDS[tag_id]['folder']),
            ],
            fields=["id"]
        )

        operation = Operation(
            type="mutation",
            name="CreateBorderForTemplate",
            queries=[create_board],
        )
        # print(operation.render())
        self.query_data = operation.render()
        """
        mutation CreateNewBoard{
  create_board (template_id: 6240196911, board_name: "test", board_kind: public, folder_id: 13660600) {
    id
  }
}

        :return:
        """



    def _get_board_items(self, board_id):
        board_ids = Argument(name="ids", value=[board_id])

        board_info = Query(
            name='boards',
            arguments=[board_ids],
            fields=[
                Field(
                    name='items_page',
                    fields=[
                        Field(
                            name='items',
                            fields=[
                                'id',
                                'name',
                                Field(
                                    name='column_values',
                                    fields=[
                                        'id',
                                        'text',
                                        'value'
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ])
        operation = Operation(type='query', queries=[board_info])
        print(operation.render())
        self.query_data = operation.render()


    """
        query GetBoardItems{  
  boards(ids: 6371424160) {  
    items_page {  
      items {  
        id  
        name  
        column_values {  
          id  
          value  
        }  
      }  
    }  
  }  
}
    """

    def _get_query(self):
        self.data = {'query': self.query_data}
        return requests.post(url=self.api_url, json=self.data, headers=self.headers)

    def run(self, tag_id, email):
        self._create_board_mutation_query(tag_id, email)
        board_id = self._get_query().json()
        print(board_id)
        time.sleep(2)
        self._get_board_items(board_id['data']['create_board']['id'])
        data = self._get_query().json()
        # print('hello')
        # print(data)
        items = data['data']['boards'][0]['items_page']['items']
        print(items)
        # for item in items:
        #     print(item)
        names = []
        result_item = {}
        for item in items:
            # print(item['name'])
            result_item['id'] = item['id']
            result_item['name'] = item['name']
            print(item['column_values'])
            if str(tag_id) == str(EMPLOYEES['COLDLINE']) or str(tag_id) == str(EMPLOYEES['HOTLINE']):
                for value in item['column_values']:
                    if value['id'] == 'text__1':
                        result_item['arab'] = value['text']
                    if value['id'] == 'numbers2__1':
                        result_item['missing'] = value['value']
                    if value['id'] == 'numbers__1':
                        result_item['standard'] = value['text']
                    if value['id'] == 'numeric__1':
                        result_item['morning'] = value['text']
                    if value['id'] == 'numeric2__1':
                        result_item['evening'] = value['text']
                    if value['id'] == 'long_text__1':
                        result_item['cause'] = value['text']

            else:
                for value in item['column_values']:
                    if value['id'] == 'hour':
                        if value['value']:
                            data_obj = json.loads(value['value'])
                            result_item['time'] = f"{data_obj['hour']}:{data_obj['minute']}"
                        else:
                            result_item['time'] = value['text']
                    if value['id'] == 'status':
                        result_item['status'] = value['text']
                    if value['id'] == 'long_text':
                        result_item['comment'] = value['text']
            names.append(result_item)
            result_item = {}
        result = {
            'id': board_id['data']['create_board'],
            'items': names
        }
        return result


class CreateBoardMondayWorker:
    def __init__(self):
        pass


class ChangeBoardMondayBackend:
    def __init__(self):
        self.token = os.getenv('MONDAY_API_TOKEN')
        self.api_url = 'https://api.monday.com/v2'
        self.headers = {"Authorization": self.token, "API-Version": "2023-04"}
        self.query_data = ''
        self.row_data = ''
        self.data = ''

    # mutation
    # UpdateColumnValue
    # {
    #     change_simple_column_value(board_id: {{target_board_id}}, item_id: {{target_item_id}}, column_id: "status",
    #     value: "Done") {
    #     id
    # }
    # }

    def _change_board_mutation_query(self, board_id, item_id, status):
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(board_id)
        print(item_id)
        print(board_id)

        change_simple_column_value= Query(
            name="change_simple_column_value",
            arguments=[
                Argument(name="board_id", value=board_id),
                Argument(name="item_id", value=item_id),
                Argument(name="column_id", value='"status"'),
                Argument(name="value", value=f'\"{status}\"'),
            ],
            fields=["id"]
        )

        operation = Operation(
            type="mutation",
            name="UpdateColumnValue",
            queries=[change_simple_column_value],
        )
        # query = '''
        # mutation {
        #   change_multiple_column_values(item_id: ''' + item_id + ''',
        #   board_id: ''' + board_id + ''',
        #   column_values: \"''' + json.dumps({"status": {"index": "2" if status == "בוצע" else "3"}}) + '''\")
        # }
        # '''
        print(operation.render())
        # print(query)
        self.query_data = operation.render()
        # self.query_data = query

    def _change_comment_mutation_query(self, board_id, item_id, comment=''):
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(board_id)
        print(item_id)
        print(board_id)

        change_simple_column_value = Query(
            name="change_simple_column_value",
            arguments=[
                Argument(name="board_id", value=board_id),
                Argument(name="item_id", value=item_id),
                Argument(name="column_id", value='"long_text"'),
                Argument(name="value", value=f'\"{comment}\"'),
            ],
            fields=["id"]
        )

        operation = Operation(
            type="mutation",
            name="UpdateColumnValue",
            queries=[change_simple_column_value],
        )
        # query = '''
        # mutation {
        #   change_multiple_column_values(item_id: ''' + item_id + ''',
        #   board_id: ''' + board_id + ''',
        #   column_values: \"''' + json.dumps({"status": {"index": "2" if status == "בוצע" else "3"}}) + '''\")
        # }
        # '''
        print(operation.render())
        # print(query)
        self.query_data = operation.render()
        # self.query_data = query



    def _get_board_items(self, board_id):
        board_ids = Argument(name="ids", value=[str(board_id)])

        board_info = Query(
            name='boards',
            arguments=[board_ids],
            fields=[
                Field(
                    name='items_page',
                    fields=[
                        Field(
                            name='items',
                            fields=[
                                'id',
                                'name',
                                Field(
                                    name='column_values',
                                    fields=[
                                        'id',
                                        'text',
                                        'value'
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ])
        operation = Operation(type='query', queries=[board_info])
        # print(operation.render())
        self.query_data = operation.render()

    """
        query GetBoardItems{  
  boards(ids: 6371424160) {  
    items_page {  
      items {  
        id  
        name  
        column_values {  
          id  
          value  
        }  
      }  
    }  
  }  
}
    """

    def _get_query(self):
        self.data = {'query': self.query_data}
        return requests.post(url=self.api_url, json=self.data, headers=self.headers)

    def run(self, board_id, item_id, status, comment=' '):

        self._change_board_mutation_query(board_id, item_id, status)
        result = self._get_query().json()
        self._change_comment_mutation_query(board_id, item_id, comment)
        result = self._get_query().json()
        print(result)        # print(board_id)

        return result




class LinesBoardMondayBackend:
    def __init__(self):
        self.token = os.getenv('MONDAY_API_TOKEN')
        self.api_url = 'https://api.monday.com/v2'
        self.headers = {"Authorization": self.token, "API-Version": "2023-04"}
        self.query_data = ''
        self.row_data = ''
        self.data = ''

    def get_prev_board_id(self, tag_id):
        self._get_folder_last_board(tag_id)
        result = self._get_query().json()
        prev_board_id = result.get('data').get('folders')[0].get('children')[-1].get('id')
        print(prev_board_id)
        return prev_board_id

    def _get_folder_last_board(self,  tag_id):
        folder_ids = Argument(name="ids", value=[TAG_BOARD_IDS[tag_id]['folder']])
        folder_info = Query(
            name='folders',
            arguments=[folder_ids],
            fields=[
                Field(
                    name='children',
                    fields=[
                        'id',
                        'name'
                    ]
                )
            ])
        operation = Operation(type='query', queries=[folder_info])
        # print(operation.render())
        self.query_data = operation.render()


    def _get_board_items(self, board_id):
        board_ids = Argument(name="ids", value=[str(board_id)])

        board_info = Query(
            name='boards',
            arguments=[board_ids],
            fields=[
                Field(
                    name='items_page',
                    fields=[
                        Field(
                            name='items',
                            fields=[
                                'id',
                                'name',
                                Field(
                                    name='column_values',
                                    fields=[
                                        'id',
                                        'text',
                                        'value'
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ])
        operation = Operation(type='query', queries=[board_info])
        # print(operation.render())
        self.query_data = operation.render()

    def _create_board_mutation_query(self, tag_id, email):
        create_board = Query(
            name="create_board",
            arguments=[
                # Argument(name="template_id", value=6240196911),
                Argument(name="template_id", value=TAG_BOARD_IDS[tag_id]['template']),
                Argument(name="board_name", value=f'"{datetime.date.today()}-{email}"'),
                Argument(name="board_kind", value="public"),
                Argument(name="folder_id", value=TAG_BOARD_IDS[tag_id]['folder']),
            ],
            fields=[
                "id"
            ]
        )

        operation = Operation(
            type="mutation",
            name="CreateBorderForTemplate",
            queries=[create_board],
        )
        # print(operation.render())
        self.query_data = operation.render()
        """
        mutation CreateNewBoard{
  create_board (template_id: 6240196911, board_name: "test", board_kind: public, folder_id: 13660600) {
    id
  }
}

        :return:
        """

    def _get_query(self):
        self.data = {'query': self.query_data}
        return requests.post(url=self.api_url, json=self.data, headers=self.headers)

    def run(self, tag_id, email):
        prev_board_id = self.get_prev_board_id(tag_id)
        self._create_board_mutation_query(tag_id, email)
        board_id = self._get_query().json()
        print(board_id)
        time.sleep(2)
        #prev data
        self._get_board_items(prev_board_id)
        prev_data = self._get_query().json()
        prev_items = prev_data['data']['boards'][0]['items_page']['items']

        #current data
        self._get_board_items(board_id['data']['create_board']['id'])
        data = self._get_query().json()
        items = data['data']['boards'][0]['items_page']['items']
        print(prev_items)
        # print()
        # # for item in items:
        # #     print(item)
        names = []
        result_item = {}
        temp_data = {}
        for i, item in enumerate(items):
            # print(item['name'])
            result_item['id'] = item['id']
            result_item['name'] = item['name']
            print(item['column_values'])
            if str(tag_id) == str(EMPLOYEES['COLDLINE']) or str(tag_id) == str(EMPLOYEES['HOTLINE']):
                for j, value in enumerate(item['column_values']):
                    if value['id'] == 'text__1':
                        result_item['arab'] = value['text']
                    if value['id'] == 'numbers2__1':
                        result_item['missing'] = value['value']
                    if value['id'] == 'numbers__1':
                        result_item['standard'] = value['text']
                    if value['id'] == 'numeric__1':
                        result_item['morning'] = value['text']
                        temp_data['morning'] = [
                            value['text'] for value in prev_items[i]['column_values'] if value['id'] == 'numeric__1'
                        ][0]
                        # temp_data['morning'] = prev_items[i]['column_values'].filter([j]['text']
                    if value['id'] == 'numeric2__1':
                        result_item['evening'] = value['text']
                        temp_data['evening'] = [
                            value['text'] for value in prev_items[i]['column_values'] if value['id'] == 'numeric2__1'
                        ][0]
                        # temp_data['evening'] = prev_items[i][j]['text']
                    if value['id'] == 'long_text__1':
                        result_item['cause'] = value['text']
                    if value['id'] == 'label__1' or value['id'] == 'color__1':
                        result_item['work_shift'] = value['text']
                        temp_data['work_shift'] = [
                            value['text']
                            for value in prev_items[i]['column_values']
                            if value['id'] == 'label__1' or value['id'] == 'color__1'
                        ][0]
                        # temp_data['work_shift'] = prev_items[i][j]['text']

            if temp_data['work_shift'] == WORK_SHIFTS['morning']:
                result_item['work_shift'] = WORK_SHIFTS['evening']
                result_item['morning'] = temp_data['morning']
            else:
                result_item['work_shift'] = WORK_SHIFTS['morning']
                result_item['evening'] = temp_data['evening']
            names.append(result_item)

            result_item = {}
        result = {
            'id': board_id['data']['create_board'],
            'items': names
        }
        return result


class ChangeCookMondayBackend:
    def __init__(self):
        self.token = os.getenv('MONDAY_API_TOKEN')
        self.api_url = 'https://api.monday.com/v2'
        self.headers = {"Authorization": self.token, "API-Version": "2023-04"}
        self.query_data = ''
        self.row_data = ''
        self.data = ''

    def _change_cook_values(self, board_id, item_id, empty, morning, evening, description, work_shift, role_id):
        if role_id == EMPLOYEES['COLDLINE']:
            work_shift_column_name = 'label__1'
        if role_id == EMPLOYEES['HOTLINE']:
            work_shift_column_name = 'color__1'

        result = 'mutation {'
        result += ' change_multiple_column_values('
        result += 'item_id: "' + str(item_id) + '",'
        result += ' board_id: "' + str(board_id) + '",'
        result += ' column_values: '
        result += r'  "{\"numbers2__1\": \"' + str(empty) + r'\",'
        result += r' \"numeric__1\": \"' + str(morning) + r'\",'
        result += r' \"numeric2__1\": \"' + str(evening) + r'\",'
        result += r'\"long_text__1\": \"' + str(description) + r'\",'
        result += r'\"' + work_shift_column_name + r'\": \"' + work_shift + r'\"}"'
        result += ' ) {'
        result += ' id '
        result += ' } '
        result += ' } '

        self.query_data = result

    def _get_query(self):
        self.data = {'query': self.query_data}
        return requests.post(url=self.api_url, json=self.data, headers=self.headers)

    def run(self, board_id, task_id, morning, evening, empty, description, work_shift, role_id):
        self._change_cook_values(board_id, task_id, empty, morning, evening, description, work_shift, role_id)
        print(self._get_query().json())


class CreateTaskMondayBackend:
    def __init__(self):
        self.token = os.getenv('MONDAY_API_TOKEN')
        self.api_url = 'https://api.monday.com/v2'
        self.headers = {"Authorization": self.token, "API-Version": "2023-04"}
        self.query_data = ''
        self.row_data = ''
        self.data = ''


    def _create_new_task(self, board_id, task_text):
        result = '''mutation {
          create_item (board_id: ''' + str(board_id) + ''', item_name: "''' + task_text +'''") {
            id
          }
        }'''

        self.query_data = result

    def _get_query(self):
        self.data = {'query': self.query_data}
        return requests.post(url=self.api_url, json=self.data, headers=self.headers)

    def run(self, board_id, task_text):
        self._create_new_task(board_id, task_text)
        result = self._get_query().json()
        return result


class GetTaskStatusBackend:
    def __init__(self):
        self.token = os.getenv('MONDAY_API_TOKEN')
        self.api_url = 'https://api.monday.com/v2'
        self.headers = {"Authorization": self.token, "API-Version": "2023-04"}
        self.query_data = ''
        self.row_data = ''
        self.data = ''

    def _get_task_status(self, board_id):
        result = '''query {  
                  boards(ids: ''' + str(board_id) + ''') {  
                    items_page {  
                      items {  
                        id  
                        name  
                        column_values {  
                          id  
                          text
                        }  
                      }  
                    }  
                  }  
                }'''

        self.query_data = result

    def _get_query(self):
        self.data = {'query': self.query_data}
        return requests.post(url=self.api_url, json=self.data, headers=self.headers)

    def run(self, board_id, task_id):
        self._get_task_status(board_id)
        result = self._get_query().json()
        status = ''
        for item in result['data']['boards'][0]['items_page']['items']:
            if item['id'] == task_id:
                for column in item['column_values']:
                    if column['id'] == 'status':
                        status = column['text']
        return status


if __name__ == '__main__':
    pass
    # ChangeCookMondayBackend().run(6627998362, 6627998849, "42", 30, 28,'test desciptioni', 'בוקר', 4)




    # timezone_offset = 3.0  # Pacific Standard Time (UTC−08:00)
    # tzinfo = datetime.timezone(datetime.timedelta(hours=timezone_offset))
    # print(datetime.datetime.now(tzinfo).time())
    #
    # заданное_время = datetime.datetime.strptime("14:00", "%H:%M").time()
    #
    # # Текущее время
    # текущее_время = datetime.datetime.now().time()
    # print(заданное_время < текущее_время)
