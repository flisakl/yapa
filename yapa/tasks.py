from ninja import Router, Schema, ModelSchema, Form, Field
from typing import Optional

from .users import UserOutput
from .models import Task

router = Router()


class TaskInput(ModelSchema):
    class Meta:
        model = Task
        fields = ['name', 'description', 'status', 'priority']


class TaskOutput(ModelSchema):
    created_by: Optional[UserOutput] = Field(None)
    completed_by: Optional[UserOutput] = Field(None)

    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'created_at',
                  'completed_at', 'status', 'priority']


@router.post('', response={201: TaskOutput})
async def create_task(request, payload: Form[TaskInput]):
    user = request.auth
    data = payload.dict(exclude_unset=True)
    data['created_by'] = user
    task = await Task.objects.acreate(**data)
    task = await Task.objects.select_related('created_by', 'completed_by').aget(pk=task.pk)
    return 201, task
