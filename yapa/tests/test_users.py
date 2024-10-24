from django.test import TestCase
from ninja.testing import TestClient

from yapa.models import User
from yapa.users import UserInput, router


class TestUserInputSchema(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('John', 'Doe', 'john@doe.com', 'test1234')

    def test_email_address_must_be_unique(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'john@doe.com',
            'password1': 'test1234',
            'password2': 'test1234',
        }
        with self.assertRaisesRegex(ValueError, 'taken'):
            UserInput.validate(data)

        data['email'] = 'jane@doe.com'
        UserInput.validate(data)

    def test_passwords_must_match(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@doe.com',
            'password1': 'test1234',
            'password2': 'test12345',
        }
        with self.assertRaisesRegex(ValueError, 'match'):
            UserInput.validate(data)

        data['password2'] = data['password1']
        UserInput.validate(data)


class UserRouterClient(TestClient):
    def __init__(self, *args, **kwargs):
        super().__init__(router)


class TestUsersEndpoints(TestCase):
    client_class = UserRouterClient

    # REGISTRATION
    def test_guest_can_create_account(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@doe.com',
            'password1': 'test1234',
            'password2': 'test1234',
        }

        response = self.client.post('', data)
        json = response.json()

        self.assertEqual(json['first_name'], 'Jane')
        self.assertEqual(json['last_name'], 'Doe')
        self.assertEqual(json['email'], 'jane@doe.com')
        self.assertIsNotNone(json['token'])
        self.assertEqual(response.status_code, 201)

    def test_422_is_returned_when_data_are_invalid(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@doe.com',
            'password1': 'test1234',
            'password2': 'test12345',  # password does not match
        }

        response = self.client.post('', data)
        json = response.json()

        self.assertEqual(response.status_code, 422)
        self.assertIn('password2', json['detail'][0]['loc'])

    # LOGIN
    def test_guest_can_sign_in(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@doe.com',
            'password': 'test1234',
        }
        user = User.objects.create_user(**data)

        response = self.client.post('login', {'email': user.email, 'password': data['password']})
        json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['first_name'], 'Jane')
        self.assertEqual(json['last_name'], 'Doe')
        self.assertEqual(json['email'], 'jane@doe.com')
        self.assertIsNotNone(json['token'])

    def test_guest_can_not_login_with_invalid_data(self):
        response = self.client.post('login', {'email': 'cindy@gmail.com', 'password': 'junk'})
        self.assertEqual(response.status_code, 422)
