from courses.models import Course
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render


@login_required
def course_chat_room(request, course_id):
    try:
        # мзвлечь курс с заданным id к которому
        # присоединился текущий пользователь
        course = request.user.courses_joined.get(id=course_id)
    except Course.DoesNotExist:
        # пользователь не является слушателем курса или курс не существует
        return HttpResponseForbidden
        # восстановить историю чата
        latest_messages = course.chat_messages.select_related("user").order_by("-id")[
            :5
        ]
        latest_messages = reversed(latest_messages)
        return render(
            request,
            "chat/room.html",
            {"course": course, "latest_messages": latest_messages},
        )
