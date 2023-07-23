from rest_framework.authentication import BaseAuthentication

from .models import CustomUser, RangeIpAddress
from .services import get_client_ip


class IPAddressAuthentication(BaseAuthentication):
    def authenticate(self, request):
        ipaddress = get_client_ip(request)
        if not ipaddress:
            return None

        try:
            first_part_ipaddress = ipaddress[:ipaddress.rindex('.')]
            last_part_ipaddress = int(ipaddress[ipaddress.rindex('.') + 1:])
            if not RangeIpAddress.objects.filter(
                    first_part_ipaddress=first_part_ipaddress,
                    start__lte=last_part_ipaddress,
                    end__gte=last_part_ipaddress,
            ).exists():
                return None
        except Exception as e:
            print(e)
            return None
        return (CustomUser.default_client_user(), None)
