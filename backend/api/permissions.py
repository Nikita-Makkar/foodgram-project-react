from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Кастомный пермишэн только для авторов.
    """
    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user and request.user.is_authenticated
                and obj.author == request.user)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Кастомный пермишэн только для админстраторов.
    """
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or (request.user and request.user.is_staff))
