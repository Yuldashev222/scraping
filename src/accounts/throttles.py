from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import Throttled
from rest_framework.throttling import BaseThrottle

MONTH_DAYS = 30


class IpRangeThrottle(BaseThrottle):
    def __init__(self):
        self._wait_seconds = None

    def allow_request(self, request, view):
        range_ip = request.auth
        if range_ip is None:
            return True

        if range_ip.rate_limit_per_minute == 0 or range_ip.rate_limit_per_month == 0:
            self._wait_seconds = 60
            return False

        now = timezone.now()
        current_minute = now.replace(second=0, microsecond=0)

        with transaction.atomic():
            range_ip = type(range_ip).objects.select_for_update().get(pk=range_ip.pk)

            if range_ip.month_started is None or now - range_ip.month_started >= timedelta(days=MONTH_DAYS):
                range_ip.month_started = now
                range_ip.month_requests = 0

            if range_ip.current_minute != current_minute:
                range_ip.current_minute = current_minute
                range_ip.minute_requests = 0

            if range_ip.month_requests >= range_ip.rate_limit_per_month:
                days_left = MONTH_DAYS - (now - range_ip.month_started).days
                raise Throttled(
                    wait=days_left * 86400,
                    detail=f'Monthly limit exceeded. Resets in {days_left} days.'
                )

            if range_ip.minute_requests >= range_ip.rate_limit_per_minute:
                self._wait_seconds = 60 - now.second
                return False

            range_ip.minute_requests += 1
            range_ip.month_requests += 1
            range_ip.save()

        return True

    def wait(self):
        return self._wait_seconds
