# bookings/availability.py
from datetime import timedelta
from django.db.models import F, ExpressionWrapper, Q, DateTimeField
from .models import Booking, Table

# It's better practice to define constants at the top level or in settings.
# In the future, this could come from the TimeSlot model or a global setting.
DEFAULT_BOOKING_DURATION = timedelta(hours=2)

def find_available_table(booking_datetime, number_of_guests, seating_type_id, booking_to_exclude=None):
    """
    Finds an available table that matches the criteria using an efficient database query.

    Args:
        booking_datetime (datetime): The requested start time for the booking.
        number_of_guests (int): The number of guests.
        seating_type_id (int): The primary key of the desired SeatingType.
        booking_to_exclude (Booking, optional): A booking instance to exclude from the
                                                 conflict check. Used for updates. Defaults to None.

    Returns:
        Table: An available Table object or None if no table is available.
    """
    requested_start_time = booking_datetime
    requested_end_time = requested_start_time + DEFAULT_BOOKING_DURATION

    # --- Step 1: Find all tables that are already booked during the requested time slot. ---
    
    # This is the core logic for finding an overlap:
    # An existing booking conflicts if:
    # (Its start time is before the new booking ends) AND (Its end time is after the new booking starts)
    
    # We use ExpressionWrapper to calculate the end_time of each booking in the database.
    conflicting_bookings = Booking.objects.annotate(
        booking_end_time=ExpressionWrapper(
            F('booking_datetime') + DEFAULT_BOOKING_DURATION,
            output_field=DateTimeField()
        )
    ).filter(
        booking_datetime__lt=requested_end_time,  # existing_start < new_end
        booking_end_time__gt=requested_start_time # existing_end > new_start
    )

    # If we are checking for an update, exclude the booking being updated from the conflict list.
    if booking_to_exclude:
        conflicting_bookings = conflicting_bookings.exclude(pk=booking_to_exclude.pk)

    # Get the IDs of tables that are occupied during the requested slot.
    # .values_list('table_id', flat=True) is very efficient for getting just one column.
    booked_table_ids = conflicting_bookings.values_list('table_id', flat=True)

    # --- Step 2: Find a table that meets the criteria and is not in the booked list. ---
    
    available_table = Table.objects.filter(
        seating_type_id=seating_type_id,
        capacity__gte=number_of_guests,
        is_active=True # Good practice: only consider active tables
    ).exclude(
        id__in=booked_table_ids
    ).order_by('capacity', 'table_number').first() # Optional: prioritize smaller tables first
    
    return available_table