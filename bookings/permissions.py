from rest_framework import permissions

class IsSuperUser(permissions.BasePermission):
    """
    Permission class that grants full access only to Django superusers.

    Permissions granted:
    - Any request from an authenticated superuser is allowed.
    - Object-level permission is granted exclusively to superusers.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_superuser
    
class IsManager(permissions.BasePermission):
    """
    Custom permission to allow access only to users who belong to the 'Manager' group.

    Permissions granted:
    - For any request, user must be authenticated and a member of the 'Manager' group.
    - Object-level permissions allow 'GET', 'PUT', 'PATCH', and 'DELETE' methods only for Managers.
    
    Methods:
    - has_permission: Checks if the requesting user is authenticated and is in the 'Manager' group.
    - has_object_permission: Further restricts object-level actions to only Managers,
                             allowing only safe and modifying HTTP methods.
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