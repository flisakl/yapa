from django.utils.translation import gettext_lazy as _
from ninja import Router, ModelSchema, Form, Schema
from ninja.errors import ValidationError
from pydantic import (field_validator, ValidationInfo, EmailStr)

from . import models
from . import make_errors

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


class UserOutput(ModelSchema):
    class Meta:
        model = models.User
        fields = ['id', 'first_name', 'last_name', 'email', 'token', 'avatar']
        fields_optional = ['avatar']


@router.post('', response={201: UserOutput}, auth=None)
async def create_account(request, payload: Form[UserInput]):
    data = payload.dict()
    data['password'] = data['password1']
    del data['password1']
    del data['password2']

    if await models.User.objects.filter(email=data['email']).aexists():
        raise ValidationError(make_errors('form', 'email', _('Email already taken')))

    obj = await models.User.objects.acreate_user(**data)
    return 201, obj


class SignInSchema(Schema):
    email: EmailStr
    password: str


@router.post('login', response={200: UserOutput, 401: dict}, auth=None)
async def sign_in(request, payload: Form[SignInSchema]):
    data = payload.dict()
    try:
        user = await models.User.objects.aget(email=data['email'])
        if not user.check_password(data['password']):
            errors = make_errors('form', 'password', _('Invalid password'), True)
            return 401, errors
        return user

    except models.User.DoesNotExist:
        errors = make_errors('form', 'email', _('Invalid email address'), True)
        return 401, errors
