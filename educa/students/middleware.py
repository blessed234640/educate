"""
Middleware for tracking student course progress.
"""
import logging

logger = logging.getLogger(__name__)


class TrackStudentProgressMiddleware:
    """
    Automatically track when students access course modules.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Track module access
        if request.user.is_authenticated:
            self._track_module_access(request)
        
        return response
    
    def _track_module_access(self, request):
        """Track module access if applicable."""
        try:
            # Check if we're on a course module page
            resolver_match = request.resolver_match
            if not resolver_match:
                return
            
            url_name = resolver_match.url_name
            
            if url_name == 'student_course_detail_module':
                course_id = resolver_match.kwargs.get('pk')
                module_id = resolver_match.kwargs.get('module_id')
                
                if course_id and module_id:
                    from utils.redis_utils import CourseProgressTracker
                    CourseProgressTracker.set_last_module(
                        request.user.id,
                        course_id,
                        module_id
                    )
                    
        except Exception as e:
            logger.error(f"Progress tracking error: {e}")