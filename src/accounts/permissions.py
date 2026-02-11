from rest_framework.permissions import BasePermission


class IsAllowedIP(BasePermission):
    def has_permission(self, request, view):
        return True
