# bookings/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OccasionViewSet,
    SeatingTypeViewSet,
    TimeSlotViewSet,
    BookingViewSet,
    OccasionAdminViewSet,
    SeatingTypeAdminViewSet,
    TimeSlotAdminViewSet,
)

# DefaultRouter automatically handles the URL routing for ViewSets.
# It creates the standard list, create, retrieve, update, destroy routes.
router = DefaultRouter()

# Register your ViewSets with the router
# The first argument is the URL prefix, e.g., 'bookings' -> /api/bookings/
# The second argument is the ViewSet class.
# The 'basename' is used for generating URL names. It's good practice to set it.
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'occasions', OccasionViewSet, basename='occasion')
router.register(r'seating-types', SeatingTypeViewSet, basename='seatingtype')
router.register(r'time-slots', TimeSlotViewSet, basename='timeslot')

admin_router = DefaultRouter()
admin_router.register(r'occasions', OccasionAdminViewSet, basename='admin-occasion')
admin_router.register(r'seating-types', SeatingTypeAdminViewSet, basename='admin-seatingtype')
admin_router.register(r'time-slots', TimeSlotAdminViewSet, basename='admin-timeslot')

# The API URLs are now determined automatically by the router.
# The 'urlpatterns' list is what Django's include() function will use.
urlpatterns = [
    path('', include(router.urls)),
    path('admin/', include(admin_router.urls)),
]