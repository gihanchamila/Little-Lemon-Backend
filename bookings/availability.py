# bookings/availability.py
from datetime import timedelta
from django.utils import timezone
from .models import Booking, Table

def find_available_table(booking_datetime, number_of_guests, seating_type_id):
    """
    Finds an available table that matches the criteria.
    Returns a Table object or None.
    """
    # Define the duration of a booking (e.g., 2 hours). This can be made more dynamic later.
    booking_duration = timedelta(hours=2)
    requested_start_time = booking_datetime
    requested_end_time = booking_datetime + booking_duration

    # Find all tables that are already booked during the requested time slot.
    # A booking overlaps if (new_start < old_end) AND (new_end > old_start).
    overlapping_bookings = Booking.objects.filter(
        booking_datetime__lt=requested_end_time,
        booking_datetime__gte=requested_start_time - booking_duration # A simple check to narrow down query
    )

    # A more precise check for overlap
    booked_table_ids = []
    for booking in overlapping_bookings:
        booking_start = booking.booking_datetime
        booking_end = booking_start + booking_duration
        if (requested_start_time < booking_end and requested_end_time > booking_start):
            booked_table_ids.append(booking.table.id)


    # Find a table that matches the criteria AND is not in the list of booked tables.
    available_table = Table.objects.filter(
        seating_type__id=seating_type_id,
        capacity__gte=number_of_guests
    ).exclude(
        id__in=booked_table_ids
    ).first() # Get the first one that fits

    return available_table