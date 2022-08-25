# TODOs

- sp_app/utils.py:
  - set_approved: test for malformatted input
  - get_last_change_response: Sending changes triggers more frequent updates
- sp_app/views.py:
  - was wenn in der session keine department_ids sind?

## Redis einsetzen

- Welche Daten sollen in Redis gecachet werden?
  - last_change_pk

import redis
from django_redis import get_redis_connection
con = get_redis_connection("default")
try:
    con.ping()
except redis.exceptions.RedisError:
    # No redis
    pass
