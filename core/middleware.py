import time

from django.http import HttpResponseForbidden

RATE_LIMIT = {}  # {ip: [timestamps]}


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/contact"):
            ip = request.META.get("REMOTE_ADDR")
            now = time.time()
            window = 60  # seconds
            max_requests = 5

            timestamps = [t for t in RATE_LIMIT.get(ip, []) if now - t < window]
            if len(timestamps) >= max_requests:
                return HttpResponseForbidden("Rate limit exceeded. Try again later.")

            timestamps.append(now)
            RATE_LIMIT[ip] = timestamps

        return self.get_response(request)
