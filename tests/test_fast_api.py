from http import HTTPStatus

import pytest
import requests

from app.database.users import get_max_user_id
from data import users_data


@pytest.fixture(scope='function')
def create_user_id(users_endpoint: str) -> str:
    """Фикстура для создания временного пользователя"""

    new_user = {"name": "tmp user", "job": "PM"}
    response = requests.post(users_endpoint, json=new_user)
    assert response.status_code == HTTPStatus.CREATED, 'Не удалось создать пользователя'
    current_id = response.json()['id']
    return current_id


class TestGetUser:

    @pytest.mark.parametrize('user_id', [1, 2, 3, 4, 5])
    def test_user_data(self, users_endpoint, user_id):
        response = requests.get(f"{users_endpoint}/{user_id}")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        data = body["data"]

        assert data["email"] == users_data[user_id].email
        assert data["first_name"] == users_data[user_id].first_name
        assert data["last_name"] == users_data[user_id].last_name

    def test_response_when_user_not_exist(self, users_endpoint):
        user_id = get_max_user_id() + 1
        response = requests.get(f"{users_endpoint}/{user_id}")
        assert response.status_code == HTTPStatus.NOT_FOUND
        body = response.json()
        assert not body

    @pytest.mark.parametrize('user_id', ('0', '-1'))
    def test_not_valid_value_ids(self, users_endpoint, user_id):
        response = requests.get(f"{users_endpoint}/{user_id}")
        assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
        body = response.json()
        assert body['detail'] == 'Invalid user id'


class TestCRUD:

    @pytest.mark.parametrize('user_dict', [
        {"name": "Max", "job": "qa-manual"},
        {'name': 'Alisa', 'job': 'qa-auto'}
    ])
    def test_create_user_post_request(self, users_endpoint, user_dict):
        response = requests.post(users_endpoint, json=user_dict)
        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert body['name'] == user_dict['name']
        assert body['job'] == user_dict['job']

    def test_update_exist_user(self, users_endpoint, create_user_id):
        """Обновление существующего пользователя"""
        new_data_user = {"name": "Nikolay", "job": "Super PM"}

        response_update = requests.patch(f"{users_endpoint}/{create_user_id}", json=new_data_user)
        assert response_update.status_code == HTTPStatus.OK
        body = response_update.json()
        assert body['name'] == new_data_user['name']
        assert body['job'] == new_data_user['job']

        response_updated_user = requests.get(f"{users_endpoint}/{create_user_id}")
        assert response_updated_user.status_code == HTTPStatus.OK
        new_body = response_updated_user.json()
        data = new_body["data"]
        assert data['first_name'] == new_data_user["name"]
        assert data['job'] == new_data_user["job"]

    def test_update_not_exist_user(self, users_endpoint):
        """Обновление не существующего пользователя"""
        new_data_user = {"name": "Maxim", "job": "driver"}
        user_id = get_max_user_id() + 1

        response_update = requests.patch(f"{users_endpoint}/{user_id}", json=new_data_user)
        assert response_update.status_code == HTTPStatus.NOT_FOUND
        assert response_update.json()['detail'] == 'User not found'

    def test_delete_user(self, users_endpoint, create_user_id):
        """Удаление существующего пользователя"""

        delete_response = requests.delete(f'{users_endpoint}/{create_user_id}')
        assert delete_response.status_code == HTTPStatus.NO_CONTENT
        assert requests.get(f'{users_endpoint}/{create_user_id}').status_code == HTTPStatus.NOT_FOUND

    def test_delete_not_exist_user(self, users_endpoint):
        """Удаление не существующего пользователя"""
        user_id = get_max_user_id() + 1

        delete_response = requests.delete(f"{users_endpoint}/{user_id}")
        assert delete_response.status_code == HTTPStatus.NOT_FOUND
