from ninja import NinjaAPI
from ninja.errors import ValidationError, _default_validation_error
from django.urls import reverse_lazy

from .users import router as auth_router
from .tasks import router as task_router
from .models import User


async def jwt_auth(request):
    header = request.headers.get('Authorization')
    if header:
        _, token = header.split(' ')
        try:
            user = await User.objects.aget(token=token)
            return user
        except User.DoesNotExist:
            pass


async def jwt_auth_staff(request):
    user = await jwt_auth(request)
    if user and (user.is_staff or user.is_superuser):
        return user


async def jwt_auth_superuser(request):
    user = await jwt_auth(request)
    if user and user.is_superuser:
        return user

api = NinjaAPI(auth=jwt_auth)


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
api.add_router('tasks/', task_router, tags=['tasks'])
