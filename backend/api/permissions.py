"""Permissions for API."""
from rest_framework import permissions


class AdminOnlyPermission(permissions.BasePermission):
    """Права администратора и суперюзера Django."""

    def has_permission(self, request, view):
        """Has_permission method for AdminOnlyPermission."""
        return request.user.is_authenticated and request.user.is_admin


class AdminAuthorPermission(permissions.BasePermission):
    """Права на изменение объекта.

    (суперюзер, автор).
    """

    def has_permission(self, request, view):
        """Has_permission method for AdminAuthorPermission."""
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        """Has_object_permission for AdminModeratorAuthorPermission."""
        return (
            request.user.is_superuser
            or obj.author == request.user
        )


class AdminOrReadOnlyPermission(permissions.BasePermission):
    """Права администратора, суперюзера и пользователя на чтение."""

    def has_permission(self, request, view):
        """Has_permission method for AdminModeratorAuthorPermission."""
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated and request.user.is_admin
        )


class UserSafeOrUpdatePermission(permissions.BasePermission):
    """Разрешения для разного уровня досутпа.

    Распределеине прав доступа и изменения объектов,
    в зависимости от статуса токена.
    """

    def has_permission(self, request, view):
        """Has_permissions for UserSafeOrUpdatePermission."""
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
            or request.method in ('PATCH', 'DELETE')
        )

    def has_object_permission(self, request, view, obj):
        """Has_object_permissions for UserSafeOrUpdatePermission."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_admin
            or request.user.is_moderator
            or obj.author == request.user
        )
