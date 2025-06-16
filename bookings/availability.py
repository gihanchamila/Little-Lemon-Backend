# bookings/availability.py
from datetime import timedelta
from django.db.models import F, ExpressionWrapper, Q, DateTimeField
from .models import Booking, Table
import logging
logger = logging.getLogger(__name__)

DEFAULT_BOOKING_DURATION = timedelta(hours=2)

def find_available_table(booking_datetime, number_of_guests, seating_type_id, booking_to_exclude=None):
    """
    Find an available table matching the seating type and capacity that is free at the requested booking time.

    Args:
        booking_datetime (datetime): The requested start time for the booking.
        number_of_guests (int): The number of guests that need seating.
        seating_type_id (int): The primary key (ID) of the desired SeatingType.
        booking_to_exclude (Booking, optional): A booking instance to exclude from conflict checks.
                                                 Useful when updating an existing booking to avoid self-conflict.
                                                 Defaults to None.

    Returns:
        Table or None: Returns a Table instance if an available one is found matching the criteria,
                       otherwise returns None.

    Behavior:
    - Calculates the requested booking's end time by adding a fixed booking duration (default 2 hours).
    - Queries the Booking table to find any bookings overlapping with the requested time.
      Overlap logic: existing booking start < requested end AND existing booking end > requested start.
    - Excludes the booking being updated (if any) from conflict checks.
    - Identifies tables that are currently booked in the requested time frame.
    - Filters tables by seating type, minimum capacity, and active status.
    - Excludes booked tables from available options.
    - Returns the first table sorted by smallest capacity and table number to optimize usage.
    - Returns None if no suitable table is found.

    Notes:
    - Booking duration is set by DEFAULT_BOOKING_DURATION, ideally configurable or retrieved from the TimeSlot model.
    - The function uses database annotations and efficient queries to avoid loading unnecessary data into memory.
    - Logging debug info helps track the search process and outcomes.
    """

    requested_start_time = booking_datetime
    requested_end_time = requested_start_time + DEFAULT_BOOKING_DURATION

    logger.debug(
        f"Searching for table: guests={number_of_guests}, seating_type={seating_type_id}, time={booking_datetime}"
    )

    conflicting_bookings = Booking.objects.annotate(
        booking_end_time=ExpressionWrapper(
            F('booking_datetime') + DEFAULT_BOOKING_DURATION,
            output_field=DateTimeField()
        )
    ).filter(
        booking_datetime__lt=requested_end_time,  
        booking_end_time__gt=requested_start_time
    )

    if booking_to_exclude:
        conflicting_bookings = conflicting_bookings.exclude(pk=booking_to_exclude.pk)

    booked_table_ids = conflicting_bookings.values_list('table_id', flat=True)
    
    available_table = Table.objects.filter(
        seating_type_id=seating_type_id,
        capacity__gte=number_of_guests,
        is_active=True 
    ).exclude(
        id__in=booked_table_ids
    ).order_by('capacity', 'table_number').first()

    if available_table:
        logger.debug(f"Found available table: ID={available_table.id}, Capacity={available_table.capacity}")
    else:
        logger.debug("No available table found.")
    
    return available_table