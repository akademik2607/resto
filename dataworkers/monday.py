import json
import os
import time

from graphql_query import Query, Operation, Argument, Field

from models.forms import LoginFormModel, AuthUserModel
import requests
from dotenv import load_dotenv
import datetime

load_dotenv()

TAG_BOARD_IDS = {
    3: '6491006289',   #Бар
    4: '6435726538',   #Горячая полоса
    5: '6491000334',         #Холодная полоса
    6: '6491020502',           #см
    7: '6491013724',              #Директор
    8: '6240196911',              #Офицант
    9: '6491025411',    #Чекер
    10: '6491028745',             #Уборщик
    11: '6491030859',             #Хостес
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
        column_values = Argument(name="ids", value=['"id"', '"email"', '"text"', '"dropdown"'])

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
            for column in item.get('column_values'):
                if column.get('id') == 'email':
                    user.email = column.get('text')
                elif column.get('id') == 'text':
                    user.password = column.get('value')
                elif column.get('id') == 'dropdown':
                    user.tags = column.get('value')
                elif column.get('id') == 'id':
                    user.id = column.get('value')
            if not user.email or not user.password or not user.tags:
                continue
            users.append(user)
            # print(user)
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
            if data.email == user.email and data.password == user.password.strip('"'):
                return json.dumps({'message': 'success', 'tags': user.tags, 'id': user.id})
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
                Argument(name="template_id", value=TAG_BOARD_IDS[tag_id]),
                Argument(name="board_name", value=f'"{datetime.date.today()}-{email}"'),
                Argument(name="board_kind", value="public"),
                Argument(name="folder_id", value=13660600),
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
        print()
        # for item in items:
        #     print(item)
        names = []
        result_item = {}
        for item in items:
            # print(item['name'])
            result_item['id'] = item['id']
            result_item['name'] = item['name']
            for  value in item['column_values']:

                if value['id'] == 'hour':
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
        print(operation.render())
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

    def run(self, board_id, item_id, status):
        # self._get_board_items(board_id)
        # data = self._get_query().json()
        # print(data)
        # print(data['data']['boards'][0]['items_page']['items'][index])
        # item_id = data['data']['boards'][0]['items_page']['items'][index]
        # for item in data['data']['boards'][0]['items_page']['items']:
        #     if item.id ==
        self._change_board_mutation_query(board_id, item_id, status)
        result = self._get_query().json()
        print(result)        # print(board_id)
        # self._get_board_items(board_id['data']['create_board']['id'])
        # data = self._get_query().json()
        # items = data['data']['boards'][0]['items_page']['items']
        # names = []
        # result_item = {}
        # for item in items:
        #     # print(item['name'])
        #     result_item['name'] = item['name']
        #     for value in item['column_values']:
        #         if value['id'] == 'hour':
        #             result_item['time'] = value['text']
        #         if value['id'] == 'status':
        #             result_item['status'] = value['text']
        #         if value['id'] == 'long_text':
        #             result_item['comment'] = value['text']
        #     names.append(result_item)
        #     result_item = {}
        # result = {
        #     'id': board_id['data']['create_board'],
        #     'items': names
        # }
        return result











if __name__ == '__main__':
    CreateBoardMondayBackend().run(1)
