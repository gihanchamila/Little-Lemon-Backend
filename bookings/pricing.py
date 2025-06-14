# your_app/pricing.py

from .models import TimeSlot
from rest_framework.exceptions import ValidationError

def calculate_booking_price(number_of_guests: int, booking_datetime, seating_type):
    """
    Calculates the total price for a booking based on business rules.
    
    Formula:
    (TimeSlot.base_price_per_guest * number_of_guests) * SeatingType.price_multiplier
    """
    booking_time = booking_datetime.time()

    try:
        # Find the time slot that this booking falls into.
        time_slot = TimeSlot.objects.get(start_time__lte=booking_time, end_time__gte=booking_time)
    except TimeSlot.DoesNotExist:
        # This error should also be caught by the serializer validation, but it's good practice.
        raise ValidationError({"booking_datetime": "The selected time is not within any available booking slots."})
    except TimeSlot.MultipleObjectsReturned:
        # This indicates a configuration error (overlapping time slots).
        # Log this error for the admin.
        # logger.error(f"Overlapping time slots found for time {booking_time}")
        raise ValidationError({"error": "A configuration error occurred. Please contact support."})

    # Ensure all values are valid
    if number_of_guests <= 0:
        raise ValidationError({"number_of_guests": "Number of guests must be positive."})

    # Calculate the price using the formula
    base_price = time_slot.base_price_per_guest * number_of_guests
    total_price = base_price * seating_type.price_multiplier

    return round(total_price, 2)