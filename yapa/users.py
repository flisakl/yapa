from django.utils.translation import gettext_lazy as _
from ninja import Router, ModelSchema, Form, Schema
from ninja.errors import ValidationError
from pydantic import (field_validator, model_validator, ValidationInfo, EmailStr)
from typing import Self

from . import models

router = Router()


class UserInput(ModelSchema):
    password1: str
    password2: str
    email: EmailStr

    class Meta:
        model = models.User
        fields = ['first_name', 'last_name', 'email']

    @field_validator('password2')
    @classmethod
    def passwords_are_matching(cls, v: str, info: ValidationInfo):
        p1 = v
        p2 = info.data['password1']
        if not p1 or p1 != p2:
            raise ValueError(_('password confirmation does not match'))
        return p1

    @field_validator('email')
    @classmethod
    def email_is_not_taken(cls, v: str, info: ValidationInfo):
        if models.User.objects.filter(email=v).exists():
            raise ValueError(_('email address is already taken'))
        return v


class UserOutput(ModelSchema):
    class Meta:
        model = models.User
        fields = ['id', 'first_name', 'last_name', 'email', 'token', 'avatar']
        fields_optional = ['avatar']


@router.post('', response={201: UserOutput}, auth=None)
def create_account(request, payload: Form[UserInput]):
    data = payload.dict()
    data['password'] = data['password1']
    del data['password1']
    del data['password2']
    obj = models.User.objects.create_user(**data)
    return 201, obj


class SignInSchema(Schema):
    email: EmailStr
    password: str
    _user: models.User = None

    # This allows to set models.User as annotation for schema
    class Config:
        arbitrary_types_allowed = True

    # To keep error messages consistent I'll use Pydantic's validator to check
    # if user exists in database and store it inside `user` field so it can be
    # easily retrieved inside view
    @model_validator(mode='after')
    def check_if_user_exists(self) -> Self:
        try:
            user = models.User.objects.get(email=self.email)
            if not user.check_password(self.password):
                raise ValueError(_('invalid password'))
            else:
                self._user = user
                return self

        except models.User.DoesNotExist:
            raise ValueError(_('invalid email address'))

# TODO: Change response status code to 401
@router.post('login', response=UserOutput, auth=None)
def sign_in(request, generic: Form[SignInSchema]):
    # `generic` will be the name of the field in `loc` table, it makes sense
    # because either email or password will be invalid
    return generic._user
