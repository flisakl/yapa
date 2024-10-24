from django.utils.translation import gettext_lazy as _
from ninja import Router, ModelSchema, Form
from pydantic import (field_validator, ValidationInfo, EmailStr)

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


@router.post('', response={201: UserOutput})
def create_account(request, payload: Form[UserInput]):
    data = payload.dict()
    data['password'] = data['password1']
    del data['password1']
    del data['password2']
    obj = models.User.objects.create_user(**data)
    return 201, obj
