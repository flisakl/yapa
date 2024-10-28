from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password
from django.conf import settings
import jwt


def generate_token(first_name, last_name, email):
    return jwt.encode({
            "first_name": first_name,
            "last_name": last_name,
            "email": email
    }, settings.SECRET_KEY)


class UserManager(BaseUserManager):
    def _create_user_object(self, first_name, last_name, email, password):
        if not first_name:
            raise ValueError('First name must be provided')
        if not last_name:
            raise ValueError('Last name must be provided')
        email = self.normalize_email(email)

        user = self.model(first_name=first_name, last_name=last_name, email=email)
        user.token = generate_token(first_name, last_name, email)
        user.password = make_password(password)
        return user

    def create_user(self, first_name, last_name, email, password):
        """
        Create and save a user with the given first and last name, email and password.
        """
        user = self._create_user_object(first_name, last_name, email, password)
        user.save(using=self._db)
        return user

    async def acreate_user(self, first_name, last_name, email, password):
        """
        Create and save a user with the given first and last name, email and password.
        """
        user = self._create_user_object(first_name, last_name, email, password)
        await user.asave(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, password):
        """
        Create and save a user with the given first and last name, email and password.
        """
        user = self._create_user_object(first_name, last_name, email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    async def acreate_superuser(self, first_name, last_name, email, password):
        """
        Create and save a user with the given first and last name, email and password.
        """
        user = self._create_user_object(first_name, last_name, email, password)
        user.is_staff = True
        user.is_superuser = True
        await user.asave(using=self._db)
        return user


class User(AbstractUser):
    username = None
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=False, null=False)
    last_name = models.CharField(_("last name"), max_length=150, blank=False, null=False)
    email = models.EmailField(unique=True)
    token = models.CharField(max_length=1000)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()
