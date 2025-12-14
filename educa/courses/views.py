from importlib.machinery import all_suffixes

from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.db.models import Count
from django.forms.models import modelform_factory
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from students.forms import CourseEnrollForm
from .forms import CourseForm, ModuleFormSet
from .models import Wishlist
from .forms import ModuleFormSet
from .models import Content, Course, Module, Subject
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


class OwnerMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)


class OwnerEditMixin:
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnerCourseMixin(OwnerMixin, LoginRequiredMixin, PermissionRequiredMixin):
    model = Course
    # УДАЛИТЕ ЭТУ СТРОКУ: fields = ["subject", "title", "slug", "overview"]
    success_url = reverse_lazy("manage_course_list")


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = "courses/manage/course/form.html"


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = "courses/manage/course/list.html"
    permission_required = "courses.view_course"


class CourseCreateView(OwnerCourseEditMixin, CreateView):
    permission_required = "courses.add_course"
    form_class = CourseForm


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = "courses.change_course"
    form_class = CourseForm


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = "courses/manage/course/delete.html"
    permission_required = "courses.delete_course"


class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name = "courses/manage/module/formset.html"
    course = None

    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)

    def dispatch(self, request, pk):
        self.course = get_object_or_404(Course, id=pk, owner=request.user)
        return super().dispatch(request, pk)

    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response({"course": self.course, "formset": formset})

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect("manage_course_list")
        return self.render_to_response({"course": self.course, "formset": formset})


class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None
    obj = None
    template_name = "courses/manage/content/form.html"

    def get_model(self, model_name):
        if model_name in ["text", "video", "image", "file"]:
            return apps.get_model(app_label="courses", model_name=model_name)
        return None

    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(
            model, exclude=["owner", "order", "created", "updated"]
        )
        return Form(*args, **kwargs)

    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(
            Module, id=module_id, course__owner=request.user
        )
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model, id=id, owner=request.user)
        return super().dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({"form": form, "object": self.obj})

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(
            self.model, instance=self.obj, data=request.POST, files=request.FILES
        )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                Content.objects.create(module=self.module, item=obj)
            return redirect("module_content_list", self.module.id)
        return self.render_to_response({"form": form, "object": self.obj})


class ContentDeleteView(View):
    def post(self, request, id):
        content = get_object_or_404(Content, id=id, module__course__owner=request.user)
        module = content.module
        content.item.delete()
        content.delete()
        return redirect("module_content_list", module.id)


class ModuleContentListView(TemplateResponseMixin, View):
    template_name = "courses/manage/module/content_list.html"

    def get(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        return self.render_to_response({"module": module})


class ModuleOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Module.objects.filter(id=id, course__owner=request.user).update(order=order)
        return self.render_json_response({"saved": "OK"})


class ContentOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(id=id, module__course__owner=request.user).update(
                order=order
            )
        return self.render_json_response({"saved": "OK"})


class CourseListView(TemplateResponseMixin, View):
    model = Course
    template_name = 'courses/course/list.html'

    def get(self, request, subject=None):
        subjects = cache.get('all_subjects')
        if not subjects:
            subjects = Subject.objects.annotate(
                total_courses=Count('courses')
            )
            cache.set('all_subjects', subjects)
        all_courses = Course.objects.annotate(
            total_modules=Count('modules')
        )
        if subject:
            subject = get_object_or_404(Subject, slug=subject)
            key = f'subject_{subject.id}_courses'
            courses = cache.get(key)
            if not courses:
                courses = all_courses.filter(subject=subject)
                cache.set(key, courses)
        else:
            courses = cache.get('all_courses')
            if not courses:
                courses = all_courses
                cache.set('all_courses', courses)
        return self.render_to_response(
            {
                'subjects': subjects,
                'subject': subject,
                'courses': courses,
            }
        )



class CourseDetailView(DetailView):
    model = Course
    template_name = "courses/course/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        request = self.request
        
        # Проверка, зачислен ли пользователь
        is_enrolled = False
        course_progress = 0
        if request.user.is_authenticated:
            is_enrolled = course.students.filter(id=request.user.id).exists()
            # Процент завершения курса (примерная логика)
            if is_enrolled:
                total_modules = course.modules.count()
                completed_modules = 0  # Здесь нужно ваша логика подсчета
                if total_modules > 0:
                    course_progress = (completed_modules / total_modules) * 100
        
        # Проверка, есть ли курс в вишлисте
        in_wishlist = False
        if request.user.is_authenticated:
            try:
                Wishlist.objects.get(user=request.user, course=course)
                in_wishlist = True
            except Wishlist.DoesNotExist:
                in_wishlist = False
        
        context["enroll_form"] = CourseEnrollForm(initial={"course": self.object})
        context["is_enrolled"] = is_enrolled
        context["in_wishlist"] = in_wishlist
        context["course_progress"] = round(course_progress)
        
        # Добавьте дополнительные данные для красивого отображения
        context["estimated_hours"] = course.modules.count() * 2
        
        total_contents = sum(module.contents.count() for module in course.modules.all())
        if total_contents < 10:
            context["difficulty_level"] = "Beginner"
        elif total_contents < 20:
            context["difficulty_level"] = "Intermediate"
        else:
            context["difficulty_level"] = "Advanced"
        
        instructor_courses = Course.objects.filter(owner=course.owner).count()
        total_students = sum(c.students.count() for c in Course.objects.filter(owner=course.owner))
        context["instructor_courses"] = instructor_courses
        context["total_students"] = total_students
        context["avg_rating"] = "4.8"
        
        return context
    
@method_decorator(csrf_exempt, name='dispatch')
class WishlistToggleView(View):
    def post(self, request, course_id):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/?next=' + request.path)
        
        course = get_object_or_404(Course, id=course_id)
        
        # Переключаем вишлист
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            course=course
        )
        
        if not created:  # Если уже существовал - удаляем
            wishlist_item.delete()
        
        # Перенаправляем обратно или на указанный next
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', 'wishlist_list'))
        return redirect(next_url)
    
@method_decorator(login_required, name='dispatch')
class WishlistListView(ListView):
    model = Wishlist
    template_name = 'courses/wishlist/list.html'
    context_object_name = 'wishlist_items'
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('course')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем ID курсов, на которые пользователь записан
        enrolled_courses = Course.objects.filter(students=self.request.user)
        context['enrolled_course_ids'] = [course.id for course in enrolled_courses]
        
        return context