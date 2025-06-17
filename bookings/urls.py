# bookings/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OccasionViewSet,
    SeatingTypeViewSet,
    TimeSlotViewSet,
    BookingViewSet,
    TableViewSet,
    PaymentViewSet,
    OccasionAdminViewSet,
    SeatingTypeAdminViewSet,
    TimeSlotAdminViewSet,
    BookingAdminViewSet,
    TableAdminViewSet,
    PaymentAdminViewSet,
    check_availability
)

from .availability import find_available_table

# DefaultRouter automatically handles the URL routing for ViewSets.
# It creates the standard list, create, retrieve, update, destroy routes.

router = DefaultRouter()

# Register your ViewSets with the router
# The first argument is the URL prefix, e.g., 'bookings' -> /api/bookings/
# The second argument is the ViewSet class.
# The 'basename' is used for generating URL names. It's good practice to set it.

router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'occasions', OccasionViewSet, basename='occasion')
router.register(r'seating-types', SeatingTypeViewSet, basename='seatingtypes')
router.register(r'time-slots', TimeSlotViewSet, basename='timeslot')
router.register(r'tables', TableViewSet, basename='table')
router.register(r'payments', PaymentViewSet, basename='payment')

admin_router = DefaultRouter()
admin_router.register(r'occasions', OccasionAdminViewSet, basename='admin-occasion')
admin_router.register(r'seating-types', SeatingTypeAdminViewSet, basename='admin-seatingtypes')
admin_router.register(r'time-slots', TimeSlotAdminViewSet, basename='admin-timeslot')
admin_router.register(r'bookings', BookingAdminViewSet, basename='admin-booking')
admin_router.register(r'tables', TableAdminViewSet, basename='admin-tables')
admin_router.register(r'payments', PaymentAdminViewSet, basename='admin-payments')

# The API URLs are now determined automatically by the router.
# The 'urlpatterns' list is what Django's include() function will use.

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', include(admin_router.urls)),
    path("check-availability/", check_availability, name="find_available_table"),
]