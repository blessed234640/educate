from django.db.models import Count
from rest_framework import serializers

from courses.models import Content, Course, Module, Subject
from django.contrib.auth.models import User


class ItemRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        return value.render()


class ContentSerializer(serializers.ModelSerializer):
    item = ItemRelatedField(read_only=True)

    class Meta:
        model = Content
        fields = ["order", "item"]


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ["order", "title", "description"]


class UserSimpleSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор пользователя"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    total_students = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    students = UserSimpleSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "subject",
            "title",
            "slug",
            "overview",
            "created",
            "owner",
            "modules",
            "students",
            "total_students",
            "is_enrolled",
        ]
    
    def get_total_students(self, obj):
        return obj.students.count()
    
    def get_is_enrolled(self, obj):
        """Проверяет, записан ли текущий пользователь на курс"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.students.filter(id=request.user.id).exists()
        return False


class SubjectSerializer(serializers.ModelSerializer):
    total_courses = serializers.IntegerField()
    popular_courses = serializers.SerializerMethodField()

    def get_popular_courses(self, obj):
        courses = obj.courses.annotate(total_students=Count("students")).order_by(
            "total_students"
        )[:3]
        return [f"{c.title} ({c.total_students})" for c in courses]

    class Meta:
        model = Subject
        fields = ["id", "title", "slug", "total_courses", "popular_courses"]


class ModuleWithContentsSerializer(serializers.ModelSerializer):
    contents = ContentSerializer(many=True)

    class Meta:
        model = Module
        fields = ["order", "title", "description", "contents"]


class CourseWithContentsSerializer(serializers.ModelSerializer):
    modules = ModuleWithContentsSerializer(many=True)
    total_students = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "subject",
            "title",
            "slug",
            "overview",
            "created",
            "owner",
            "modules",
            "total_students",
            "is_enrolled",
        ]
    
    def get_total_students(self, obj):
        return obj.students.count()
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.students.filter(id=request.user.id).exists()
        return False