# from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from courses.api.pagination import StandartPagination
from courses.api.permissions import IsEnrolled
from courses.api.serializers import (
    CourseSerializer,
    CourseWithContentsSerializer,
    SubjectSerializer,
    UserSimpleSerializer,
)
from courses.models import Course, Subject
from utils.redis_utils import CourseProgressTracker


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.annotate(total_courses=Count("courses"))
    serializer_class = SubjectSerializer
    pagination_class = StandartPagination


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.prefetch_related("modules").prefetch_related("students")
    serializer_class = CourseSerializer
    pagination_class = StandartPagination
    
    def get_serializer_context(self):
        """Добавляем request в контекст сериализатора"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(
        detail=True,
        methods=["post"],
        authentication_classes=[BasicAuthentication],
        permission_classes=[IsAuthenticated],
    )
    def enroll(self, request, *args, **kwargs):
        course = self.get_object()
        course.students.add(request.user)
        return Response({"enrolled": True})

    @action(
        detail=True,
        methods=["get"],
        serializer_class=CourseWithContentsSerializer,
        authentication_classes=[BasicAuthentication],
        permission_classes=[IsAuthenticated, IsEnrolled],
    )
    def contents(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    @action(
        detail=False,
        methods=["get"],
        authentication_classes=[BasicAuthentication],
        permission_classes=[IsAuthenticated],
        url_path="my-courses"
    )
    def my_courses(self, request):
        """Курсы, на которые записан текущий пользователь"""
        courses = Course.objects.filter(students=request.user).prefetch_related("modules")
        
        page = self.paginate_queryset(courses)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)


class CourseProgressAPIView(APIView):
    """
    API for course progress tracking.
    """
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id=None):
        """Get progress data."""
        if course_id:
            # Single course progress
            course = get_object_or_404(Course, id=course_id)
            
            # Check enrollment
            if not course.students.filter(id=request.user.id).exists():
                return Response(
                    {'error': 'Not enrolled in this course'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            progress_data = {
                'course_id': course.id,
                'course_title': course.title,
                'last_module': CourseProgressTracker.get_last_module(
                    request.user.id, 
                    course.id
                ),
                'completed_modules': list(CourseProgressTracker.get_completed_modules(
                    request.user.id, 
                    course.id
                )),
                'progress_percentage': CourseProgressTracker.get_course_progress_percentage(
                    request.user.id,
                    course.id,
                    course.modules.count()
                ),
                'total_modules': course.modules.count(),
            }
            
            return Response(progress_data)
        else:
            # All courses progress
            enrolled_courses = Course.objects.filter(students=request.user)
            
            progress_list = []
            for course in enrolled_courses:
                progress_list.append({
                    'course_id': course.id,
                    'course_title': course.title,
                    'progress_percentage': CourseProgressTracker.get_course_progress_percentage(
                        request.user.id,
                        course.id,
                        course.modules.count()
                    ),
                    'last_module': CourseProgressTracker.get_last_module(
                        request.user.id, 
                        course.id
                    ),
                    'completed_modules_count': len(CourseProgressTracker.get_completed_modules(
                        request.user.id, 
                        course.id
                    )),
                    'total_modules': course.modules.count(),
                })
            
            return Response({'courses': progress_list})
    
    def post(self, request, course_id):
        """Update progress."""
        course = get_object_or_404(Course, id=course_id)
        
        # Check enrollment
        if not course.students.filter(id=request.user.id).exists():
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        module_id = request.data.get('module_id')
        completed = request.data.get('completed', False)
        
        if not module_id:
            return Response(
                {'error': 'module_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate module
        if not course.modules.filter(id=module_id).exists():
            return Response(
                {'error': 'Module not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update progress
        if completed:
            CourseProgressTracker.mark_module_completed(
                request.user.id,
                course.id,
                module_id,
                completed=True
            )
        else:
            CourseProgressTracker.set_last_module(
                request.user.id,
                course.id,
                module_id
            )
        
        return Response({
            'status': 'success',
            'course_id': course.id,
            'module_id': module_id,
            'completed': completed
        })


class UserProfileAPIView(APIView):
    """
    API для получения профиля пользователя
    """
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Получить профиль пользователя"""
        user = request.user
        
        # Получаем статистику
        enrolled_courses_count = Course.objects.filter(students=user).count()
        completed_courses_count = 0  # Нужно добавить логику подсчета завершенных курсов
        
        # Получаем прогресс по всем курсам
        enrolled_courses = Course.objects.filter(students=user)
        total_progress = 0
        
        for course in enrolled_courses:
            progress = CourseProgressTracker.get_course_progress_percentage(
                user.id,
                course.id,
                course.modules.count()
            )
            total_progress += progress
        
        avg_progress = total_progress / enrolled_courses_count if enrolled_courses_count > 0 else 0
        
        profile_data = {
            'user': UserSimpleSerializer(user).data,
            'statistics': {
                'enrolled_courses': enrolled_courses_count,
                'completed_courses': completed_courses_count,
                'average_progress': round(avg_progress, 2),
                'total_courses_available': Course.objects.count(),
            },
            'enrolled_courses': [
                {
                    'id': course.id,
                    'title': course.title,
                    'progress': CourseProgressTracker.get_course_progress_percentage(
                        user.id,
                        course.id,
                        course.modules.count()
                    )
                }
                for course in enrolled_courses
            ]
        }
        
        return Response(profile_data)
    """
    API for course progress tracking.
    """
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id=None):
        """Get progress data."""
        if course_id:
            # Single course progress
            course = get_object_or_404(Course, id=course_id)
            
            # Check enrollment
            if not course.students.filter(id=request.user.id).exists():
                return Response(
                    {'error': 'Not enrolled in this course'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            progress_data = {
                'course_id': course.id,
                'course_title': course.title,
                'last_module': CourseProgressTracker.get_last_module(
                    request.user.id, 
                    course.id
                ),
                'completed_modules': list(CourseProgressTracker.get_completed_modules(
                    request.user.id, 
                    course.id
                )),
                'progress_percentage': CourseProgressTracker.get_course_progress_percentage(
                    request.user.id,
                    course.id,
                    course.modules.count()
                ),
                'total_modules': course.modules.count(),
            }
            
            return Response(progress_data)
        else:
            # All courses progress
            enrolled_courses = Course.objects.filter(students=request.user)
            
            progress_list = []
            for course in enrolled_courses:
                progress_list.append({
                    'course_id': course.id,
                    'course_title': course.title,
                    'progress_percentage': CourseProgressTracker.get_course_progress_percentage(
                        request.user.id,
                        course.id,
                        course.modules.count()
                    ),
                    'last_module': CourseProgressTracker.get_last_module(
                        request.user.id, 
                        course.id
                    ),
                    'completed_modules_count': len(CourseProgressTracker.get_completed_modules(
                        request.user.id, 
                        course.id
                    )),
                    'total_modules': course.modules.count(),
                })
            
            return Response({'courses': progress_list})
    
    def post(self, request, course_id):
        """Update progress."""
        course = get_object_or_404(Course, id=course_id)
        
        # Check enrollment
        if not course.students.filter(id=request.user.id).exists():
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        module_id = request.data.get('module_id')
        completed = request.data.get('completed', False)
        
        if not module_id:
            return Response(
                {'error': 'module_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate module
        if not course.modules.filter(id=module_id).exists():
            return Response(
                {'error': 'Module not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update progress
        if completed:
            CourseProgressTracker.mark_module_completed(
                request.user.id,
                course.id,
                module_id,
                completed=True
            )
        else:
            CourseProgressTracker.set_last_module(
                request.user.id,
                course.id,
                module_id
            )
        
        return Response({
            'status': 'success',
            'course_id': course.id,
            'module_id': module_id,
            'completed': completed
        })
    
# class CourseEnrollView(APIView):
#     authentication_classes = [BasicAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk, format=None):
#         course = get_object_or_404(Course, pk=pk)
#         course.students.add(request.user)
#         return Response({"enrolled": True})


# class SubjectListView(generics.ListAPIView):
#     queryset = Subject.objects.annotate(total_courses=Count('courses'))
#     serializer_class = SubjectSerializer
#     pagination_class = StandartPagination


# class SubjectDetailView(generics.RetrieveAPIView):
#     queryset = Subject.objects.annotate(total_courses=Count('courses'))
#     serializer_class = SubjectSerializer
