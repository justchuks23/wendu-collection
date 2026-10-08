from rest_framework.permissions import BasePermission


class HasNamedPermission(BasePermission):
    required_permission = None

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and self.required_permission
            and request.user.has_perm(self.required_permission)
        )
