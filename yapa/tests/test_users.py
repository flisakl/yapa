from django.test import TestCase, override_settings
from django.conf import settings
from ninja.testing import TestAsyncClient
from ninja import UploadedFile
from asgiref.sync import sync_to_async
import tempfile
import shutil
import os

from yapa.models import User
from yapa.users import UserInput, router
from . import TestHelper


HERE = os.path.dirname(__file__)


class TestUserInputSchema(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@doe.com',
            'password': 'test1234'
        }

        cls.user = User.objects.create_user(**cls.data)

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


class UserRouterClient(TestAsyncClient):
    def __init__(self, *args, **kwargs):
        super().__init__(router)


class TestUsersEndpoints(TestHelper):
    client_class = UserRouterClient

    # REGISTRATION
    async def test_email_address_must_be_unique(self):
        await self.create_user()
        data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'password1': 'test1234',
            'password2': 'test1234',
        }

        response = await self.client.post('', data)
        json = response.json()

        self.assertEqual(response.status_code, 422)
        self.assertIn('email', json['detail'][0]['loc'])
        self.assertIn('taken', json['detail'][0]['msg'])

    async def test_guest_can_create_account(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@doe.com',
            'password1': 'test1234',
            'password2': 'test1234',
        }

        response = await self.client.post('', data)
        json = response.json()

        self.assertEqual(json['first_name'], 'Jane')
        self.assertEqual(json['last_name'], 'Doe')
        self.assertEqual(json['email'], 'jane@doe.com')
        self.assertIsNotNone(json['token'])
        self.assertEqual(response.status_code, 201)

    async def test_422_is_returned_when_data_are_invalid(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@doe.com',
            'password1': 'test1234',
            'password2': 'test12345',  # password does not match
        }

        response = await self.client.post('', data)
        json = response.json()

        self.assertEqual(response.status_code, 422)
        self.assertIn('password2', json['detail'][0]['loc'])

    # LOGIN
    async def test_guest_can_sign_in(self):
        await self.create_user()
        body = {'email': self.user.email, 'password': 'test1234'}

        response = await self.client.post('login', body)
        json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['first_name'], 'John')
        self.assertEqual(json['last_name'], 'Doe')
        self.assertEqual(json['email'], 'john@doe.com')
        self.assertIsNotNone(json['token'])

    async def test_guest_can_not_login_with_invalid_data(self):
        body = {'email': 'cindy@gmail.com', 'password': 'junk'}

        response = await self.client.post('login', body)

        self.assertEqual(response.status_code, 401)

    # AVATAR UPLOAD
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    async def test_user_can_upload_avatar(self):
        await self.create_user()
        kwargs = {
            'FILES': {'avatar': UploadedFile(self.create_image())},
            'headers': self.headers
        }

        response = await self.client.post('avatar', **kwargs)
        json = response.json()

        shutil.rmtree(settings.MEDIA_ROOT)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(json['avatar'])

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    async def test_old_avatar_is_replaced(self):
        cf = self.create_image()
        await self.create_user()
        await sync_to_async(self.user.avatar.save)('old.jpg', cf)
        op = self.user.avatar.path
        self.assertEqual(self.user.avatar.name, 'avatars/old.jpg')
        kwargs = {
            'FILES': {
                'avatar': UploadedFile(self.create_image(), 'image.jpg')
            },
            'headers': self.headers
        }
        response = await self.client.post('avatar', **kwargs)
        json = response.json()

        new_path = os.path.join(settings.MEDIA_ROOT, 'avatars/image.jpg')
        self.assertFalse(os.path.exists(op))
        self.assertTrue(os.path.exists(new_path))
        shutil.rmtree(settings.MEDIA_ROOT)

        await self.user.arefresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['avatar'], '/avatars/image.jpg')
        self.assertEqual(self.user.avatar.name, 'avatars/image.jpg')

    async def test_user_has_to_be_logged_in(self):
        headers = {}
        response = await self.client.post('avatar', {}, headers=headers)

        self.assertEqual(response.status_code, 401)
