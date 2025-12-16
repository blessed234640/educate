"""
Redis utilities for tracking student progress.
"""
import redis
import logging

logger = logging.getLogger(__name__)

# Простое подключение
try:
    redis_client = redis.Redis(
        host='cache',
        port=6379,
        decode_responses=True,
        socket_timeout=5
    )
    redis_client.ping()
    logger.info("✅ Redis connected to cache:6379")
except Exception as e:
    logger.error(f"❌ Redis connection failed: {e}")
    redis_client = None


class CourseProgressTracker:
    @staticmethod
    def set_last_module(user_id, course_id, module_id):
        if not redis_client:
            logger.error("❌ Redis client is None!")
            return False
        
        try:
            key = f"educa:user:{user_id}:course:{course_id}:last_module"
            logger.info(f"🔑 Setting Redis key: {key} = {module_id}")
            result = redis_client.set(key, module_id)
            redis_client.expire(key, 86400)
            logger.info(f"✅ set_last_module result: {result}")
            return True
        except Exception as e:
            logger.error(f"❌ set_last_module error: {e}")
            return False
    
    @staticmethod
    def get_last_module(user_id, course_id):
        if not redis_client:
            logger.error("❌ Redis client is None!")
            return None
        
        try:
            key = f"educa:user:{user_id}:course:{course_id}:last_module"
            val = redis_client.get(key)
            logger.info(f"🔍 get_last_module: {key} = {val}")
            return int(val) if val else None
        except Exception as e:
            logger.error(f"❌ get_last_module error: {e}")
            return None
    
    @staticmethod
    def mark_module_completed(user_id, course_id, module_id, completed=True):
        if not redis_client:
            logger.error("❌ Redis client is None!")
            return False
        
        try:
            key = f"educa:user:{user_id}:course:{course_id}:completed"
            logger.info(f"🔑 mark_module_completed: {key}, module={module_id}, completed={completed}")
            if completed:
                result = redis_client.sadd(key, module_id)
                logger.info(f"✅ sadd result: {result}")
            else:
                result = redis_client.srem(key, module_id)
                logger.info(f"✅ srem result: {result}")
            redis_client.expire(key, 86400)
            return True
        except Exception as e:
            logger.error(f"❌ mark_module_completed error: {e}")
            return False
    
    @staticmethod
    def is_module_completed(user_id, course_id, module_id):
        if not redis_client:
            logger.error("❌ Redis client is None!")
            return False
        
        try:
            key = f"educa:user:{user_id}:course:{course_id}:completed"
            result = redis_client.sismember(key, module_id)
            logger.info(f"🔍 is_module_completed: {key}, module={module_id} = {result}")
            return result
        except Exception as e:
            logger.error(f"❌ is_module_completed error: {e}")
            return False
    
    @staticmethod
    def get_completed_modules(user_id, course_id):
        if not redis_client:
            logger.error("❌ Redis client is None!")
            return set()
        
        try:
            key = f"educa:user:{user_id}:course:{course_id}:completed"
            members = redis_client.smembers(key)
            logger.info(f"🔍 get_completed_modules: {key} = {members}")
            return {int(m) for m in members}
        except Exception as e:
            logger.error(f"❌ get_completed_modules error: {e}")
            return set()
    
    @staticmethod
    def get_course_progress_percentage(user_id, course_id, total_modules):
        if total_modules == 0:
            return 0
        
        completed = CourseProgressTracker.get_completed_modules(user_id, course_id)
        percentage = int((len(completed) / total_modules) * 100)
        logger.info(f"📊 Progress: user={user_id}, course={course_id}, completed={len(completed)}/{total_modules} = {percentage}%")
        return percentage