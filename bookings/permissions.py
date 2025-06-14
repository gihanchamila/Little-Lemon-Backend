from rest_framework import permissions

class IsOwnerOrAdminReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it,
    while allowing admins to have read-only access.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True # Anyone can view (queryset logic already filters)
        
        # Admin users can also view, but for safety, we restrict their write access
        # in this view. They should use the Django Admin for critical changes.
        if request.user and request.user.is_staff and request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the booking.
        return obj.user == request.user