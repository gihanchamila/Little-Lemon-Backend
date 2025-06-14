import django_filters
from .models import Booking

class BookingFilter(django_filters.FilterSet):
    # Define a custom filter field name (like "booking_date")
    booking_date = django_filters.DateFilter(
        field_name='booking_datetime',
        lookup_expr='date'
    )

    class Meta:
        model = Booking
        fields = ['booking_date']  # NOT booking_datetime__date!
