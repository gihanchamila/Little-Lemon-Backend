from rest_framework import permissions

class IsSuperUser(permissions.BasePermission):
    """
    Grants full access to Django superusers.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_superuser
    
class IsManager(permissions.BasePermission):
    """
    Allows access to users in the 'Manager' group 
    """
    
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and (
            user.groups.filter(name="Manager").exists()
        )

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.groups.filter(name="Manager").exists():
            return request.method in ['GET', 'PUT', 'PATCH', 'DELETE']
        return False