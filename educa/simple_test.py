import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educa.settings.prod')
import django
django.setup()

import redis
import logging
logging.basicConfig(level=logging.DEBUG)

print("=== Simple Redis Test ===")

# 1. Direct connection
r = redis.Redis(host='cache', port=6379, decode_responses=True)
print(f"Redis ping: {r.ping()}")

# 2. Test mark_module_completed manually
user_id = 1
course_id = 3
module_id = 6
key = f"educa:user:{user_id}:course:{course_id}:completed"

print(f"\nKey: {key}")

# Clear first
r.delete(key)
print(f"Deleted key")

# Add module 6
result = r.sadd(key, module_id)
print(f"sadd result: {result}")

# Check
members = r.smembers(key)
print(f"Members: {members}")

# Set expiry
r.expire(key, 86400)
print(f"Expiry set")

# Test is_module_completed
is_member = r.sismember(key, module_id)
print(f"Is module {module_id} completed? {is_member}")

# Check all educa keys
keys = r.keys("educa:*")
print(f"\nAll educa keys: {keys}")
for k in keys:
    if 'completed' in k:
        print(f"{k}: {r.smembers(k)}")
    else:
        print(f"{k}: {r.get(k)}")
