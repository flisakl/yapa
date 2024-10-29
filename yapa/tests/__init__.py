from django.core.files.base import ContentFile
from django.test import TestCase
from PIL import Image
import tempfile

from yapa.models import User


class TestHelper(TestCase):

    async def create_user(self, fname='John', lname='Doe', mail='john@doe.com'):
        self.user = await User.objects.acreate_user(
                fname, lname, mail, 'test1234')
        self.headers = self.get_auth_header()

    def get_auth_header(self, user: User = None):
        if not user:
            user = self.user
        return {'Authorization': f'Bearer {user.token}'}

    def create_image(self, name='image.jpg'):
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, delete_on_close=False)
        size = (10, 10)
        color = (255, 0, 0, 0)
        image = Image.new("RGB", size, color)
        image.save(temp_file, 'jpeg')
        return ContentFile(temp_file.name, name=name)
