# your_app/pricing.py

from .models import TimeSlot
from rest_framework.exceptions import ValidationError

def calculate_booking_price(number_of_guests: int, booking_datetime, seating_type):
    """
    Calculate the total price for a booking based on the number of guests,
    the booking time, and the seating type.

    Pricing formula:
        (TimeSlot.base_price_per_guest * number_of_guests) * SeatingType.price_multiplier

    Args:
        number_of_guests (int): Number of guests for the booking. Must be > 0.
        booking_datetime (datetime): The datetime of the booking.
        seating_type (SeatingType): SeatingType model instance with a price_multiplier attribute.

    Returns:
        float: Total price rounded to 2 decimal places.

    Raises:
        ValidationError: If the booking time doesn't fall into any time slot,
                         or if overlapping time slots are configured,
                         or if number_of_guests is not positive.
    """
    booking_time = booking_datetime.time()

    try:
        # Find the TimeSlot where the booking time fits between start_time and end_time
        time_slot = TimeSlot.objects.get(start_time__lte=booking_time, end_time__gte=booking_time)
    except TimeSlot.DoesNotExist:
        # No matching time slot found; this should ideally be validated earlier
        raise ValidationError({"booking_datetime": "The selected time is not within any available booking slots."})
    except TimeSlot.MultipleObjectsReturned:
        # Overlapping time slots indicate a configuration error
        raise ValidationError({"error": "A configuration error occurred. Please contact support."})

    if number_of_guests <= 0:
        raise ValidationError({"number_of_guests": "Number of guests must be positive."})

    base_price = time_slot.base_price_per_guest * number_of_guests
    total_price = base_price * seating_type.price_multiplier

    return round(total_price, 2)