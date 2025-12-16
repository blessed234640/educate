from courses.models import Course
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import ListView

from .forms import CourseEnrollForm
from utils.redis_utils import CourseProgressTracker


class StudentRegistrationView(CreateView):
    template_name = 'students/student/registration.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('student_course_list')

    def form_valid(self, form):
        result = super().form_valid(form)
        cd = form.cleaned_data
        user = authenticate(
            username=cd['username'], password=cd['password1']
        )
        login(self.request, user)
        return result


class StudentEnrollCourseView(LoginRequiredMixin, FormView):
    course = None
    form_class = CourseEnrollForm

    def form_valid(self, form):
        self.course = form.cleaned_data['course']
        self.course.students.add(self.request.user)
        
        # Initialize progress for newly enrolled course
        if self.course.modules.exists():
            first_module = self.course.modules.first()
            CourseProgressTracker.set_last_module(
                self.request.user.id,
                self.course.id,
                first_module.id
            )
        
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'student_course_detail', args=[self.course.id]
        )


class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'students/course/list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add progress information for each course
        courses_with_progress = []
        for course in context['object_list']:
            total_modules = course.modules.count()
            progress_percentage = CourseProgressTracker.get_course_progress_percentage(
                self.request.user.id,
                course.id,
                total_modules
            )
            
            last_module_id = CourseProgressTracker.get_last_module(
                self.request.user.id,
                course.id
            )
            
            courses_with_progress.append({
                'course': course,
                'progress_percentage': progress_percentage,
                'last_module_id': last_module_id,
                'total_modules': total_modules,
                'completed_modules': len(CourseProgressTracker.get_completed_modules(
                    self.request.user.id,
                    course.id
                ))
            })
        
        context['courses_with_progress'] = courses_with_progress
        return context


class StudentCourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'students/course/detail.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        # Get or determine the current module
        module = self._get_current_module(course)
        
        # Add module to context
        context['module'] = module
        
        # Add progress information to context
        context['progress_data'] = self._get_progress_data(course, module) if module else {}
        
        # Add navigation information
        if module:
            context['previous_module'] = self._get_previous_module(course, module)
            context['next_module'] = self._get_next_module(course, module)
        
        return context
    
    def _get_current_module(self, course):
        """Determine which module to show."""
        # Case 1: Module specified in URL
        if 'module_id' in self.kwargs:
            module = get_object_or_404(
                course.modules,
                id=self.kwargs['module_id']
            )
            
            # Track this module access
            CourseProgressTracker.set_last_module(
                self.request.user.id,
                course.id,
                module.id
            )
            
            return module
        
        # Case 2: Try to get last accessed module
        last_module_id = CourseProgressTracker.get_last_module(
            self.request.user.id,
            course.id
        )
        
        if last_module_id:
            try:
                last_module = course.modules.get(id=last_module_id)
                return last_module
            except:
                # Module was deleted or doesn't exist
                pass
        
        # Case 3: Default to first module
        if course.modules.exists():
            first_module = course.modules.first()
            
            # Initialize tracking
            CourseProgressTracker.set_last_module(
                self.request.user.id,
                course.id,
                first_module.id
            )
            
            return first_module
        
        # Case 4: No modules
        return None
    
    def _get_progress_data(self, course, module):
        """Get progress-related data."""
        return {
            'is_completed': CourseProgressTracker.is_module_completed(
                self.request.user.id,
                course.id,
                module.id
            ),
            'course_progress_percentage': CourseProgressTracker.get_course_progress_percentage(
                self.request.user.id,
                course.id,
                course.modules.count()
            ),
            'completed_modules_count': len(CourseProgressTracker.get_completed_modules(
                self.request.user.id,
                course.id
            )),
            'total_modules': course.modules.count(),
            'current_module_number': module.order + 1,
        }
    
    def _get_previous_module(self, course, current_module):
        """Get previous module."""
        previous_modules = course.modules.filter(order__lt=current_module.order)
        return previous_modules.last() if previous_modules.exists() else None
    
    def _get_next_module(self, course, current_module):
        """Get next module."""
        next_modules = course.modules.filter(order__gt=current_module.order)
        return next_modules.first() if next_modules.exists() else None
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests with redirect to last module."""
        self.object = self.get_object()
        
        # Redirect to last module if no module_id specified
        if 'module_id' not in self.kwargs:
            last_module_id = CourseProgressTracker.get_last_module(
                request.user.id,
                self.object.id
            )
            
            if last_module_id and self.object.modules.filter(id=last_module_id).exists():
                return redirect(
                    'student_course_detail_module',
                    pk=self.object.id,
                    module_id=last_module_id
                )
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Handle marking modules as completed."""
        if 'mark_completed' in request.POST:
            course = self.get_object()
            module_id = request.POST.get('module_id')
            
            if module_id:
                try:
                    module = course.modules.get(id=module_id)
                    CourseProgressTracker.mark_module_completed(
                        request.user.id,
                        course.id,
                        module.id,
                        completed=True
                    )
                except:
                    pass
        
        return self.get(request, *args, **kwargs)