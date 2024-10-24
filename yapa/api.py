from ninja import NinjaAPI
from ninja.errors import ValidationError, _default_validation_error
from django.urls import reverse_lazy

from .users import router as auth_router

api = NinjaAPI()


@api.exception_handler(ValidationError)
def custom_validation_handler(request, exc):
    pages_with_401 = [
        reverse_lazy('api-1.0.0:sign_in')
    ]
    response = _default_validation_error(request, exc, api)
    if request.path in pages_with_401:
        response.status_code = 401
    return response


api.add_router('users/', auth_router, tags=['users'])
