from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template.loader import render_to_string
from tinymce.models import HTMLField
from .fields import OrderField
from django.utils import timezone
import json

class Subject(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Course(models.Model):
    owner = models.ForeignKey(
        User,
        related_name='courses_created',
        on_delete=models.CASCADE
    )
    subject = models.ForeignKey(
        Subject,
        related_name='courses',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    overview = HTMLField()
    created = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(
        User,
        related_name='courses_joined',
        blank=True
    )

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(
        Course,
        related_name='modules',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = OrderField(blank=True, for_fields=['course'])

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.order}. {self.title}'


class Content(models.Model):
    module = models.ForeignKey(
        Module,
        related_name='contents',
        on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            'model__in': ('text', 'video', 'image', 'file')
        },
    )
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['module'])

    class Meta:
        ordering = ['order']


class ItemBase(models.Model):
    owner = models.ForeignKey(
        User,
        related_name='%(class)s_related',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    def render(self):
        return render_to_string(
            f'courses/content/{self._meta.model_name}.html',
            {'item': self},
        )


class Text(ItemBase):
    content = models.TextField()


class File(ItemBase):
    file = models.FileField(upload_to='files')


class Image(ItemBase):
    file = models.FileField(upload_to='images')


class Video(ItemBase):
    url = models.URLField()

class Wishlist(models.Model):
    user = models.ForeignKey(
        User,
        related_name='wishlists',
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        related_name='wishlisted_by',
        on_delete=models.CASCADE
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'course']
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.user.username} - {self.course.title}'
    
class StudentProgress(models.Model):
    """
    Database model to track student progress as backup to Redis.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='course_progress'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='student_progress'
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='student_progress'
    )
    last_accessed = models.DateTimeField(default=timezone.now)
    time_spent_seconds = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['user', 'course', 'module']
        ordering = ['-last_accessed']
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['last_accessed']),
            models.Index(fields=['completed']),
        ]
        verbose_name = 'Student Progress'
        verbose_name_plural = 'Student Progress Records'
    
    def __str__(self):
        status = "✓" if self.completed else "→"
        return f'{self.user.username} - {self.course.title} - Module {self.module.order} {status}'
    
    def save(self, *args, **kwargs):
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)
    
    @classmethod
    def update_progress(cls, user, course, module, completed=False, time_spent=0):
        """Update or create progress record."""
        from utils.redis_utils import CourseProgressTracker
        
        # Update Redis
        CourseProgressTracker.set_last_module(user.id, course.id, module.id)
        if completed:
            CourseProgressTracker.mark_module_completed(user.id, course.id, module.id, True)
        
        # Update database
        progress, created = cls.objects.update_or_create(
            user=user,
            course=course,
            module=module,
            defaults={
                'completed': completed,
                'time_spent_seconds': models.F('time_spent_seconds') + time_spent,
                'last_accessed': timezone.now(),
            }
        )
        
        return progress