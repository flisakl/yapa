from ninja.testing import TestAsyncClient

from yapa.models import User
from yapa.tasks import router
from . import TestHelper


class UserRouterClient(TestAsyncClient):
    def __init__(self, *args, **kwargs):
        super().__init__(router)


class TestTaskEndpoints(TestHelper):
    client_class = UserRouterClient

    # All endpoint require authorization, so user will be needed in all tests
    @classmethod
    def setUpTestData(cls):
        cls.data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@doe.com',
            'password': 'test1234'
        }

        cls.task_data = {
            'name': 'Finish the app',
            'description': 'Create CRUD endpoints for all models.'
        }

        cls.user = User.objects.create_user(**cls.data)

    # Creating task
    async def test_guest_can_not_create_task(self):
        # It does not matter that request body is empty because authorization
        # kicks in before schema validation
        response = await self.client.post('', {})

        self.assertEqual(response.status_code, 401)

    async def test_user_can_create_task(self):
        kwargs = {'headers': self.get_auth_header()}

        response = await self.client.post('', self.task_data, **kwargs)
        json = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(json['name'], self.task_data['name'])
        self.assertEqual(json['description'], self.task_data['description'])
        self.assertEqual(json['status'], 0)
        self.assertEqual(json['priority'], 0)
        self.assertEqual(json['completed_at'], None)
        self.assertEqual(json['completed_by'], None)
        self.assertEqual(json['created_by']['id'], self.user.pk)
