from django.test import TestCase
from datetime import datetime, timedelta
import pytz

from ..models import CustomUser, SeatingType, Table, Booking
from ..availability import find_available_table, DEFAULT_BOOKING_DURATION

# Use a timezone-aware datetime object for all tests to avoid warnings
# and ensure consistency.
TZ = pytz.UTC

class AvailabilityTests(TestCase):
    """
    Test suite for the find_available_table function.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up non-modified objects used by all test methods.
        This runs once for the entire test class.
        """
        # Create a user to own the bookings
        cls.user = CustomUser.objects.create_user(
            email='testuser@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )

        # Create Seating Types
        cls.standard_seating = SeatingType.objects.create(name="Standard", price_multiplier=1.0)
        cls.vip_seating = SeatingType.objects.create(name="VIP", price_multiplier=1.5)

        # Create a variety of tables
        cls.table_std_2_seater = Table.objects.create(table_number='S1', seating_type=cls.standard_seating, capacity=2)
        cls.table_std_4_seater = Table.objects.create(table_number='S2', seating_type=cls.standard_seating, capacity=4)
        cls.table_vip_4_seater = Table.objects.create(table_number='V1', seating_type=cls.vip_seating, capacity=4)
        cls.table_inactive = Table.objects.create(table_number='D1', seating_type=cls.standard_seating, capacity=4, is_active=False)

        # Create a pre-existing booking to test conflicts
        # This booking is for the 4-seater standard table at 7 PM.
        cls.booking_time = TZ.localize(datetime(2025, 10, 10, 19, 0, 0))
        cls.existing_booking = Booking.objects.create(
            user=cls.user,
            number_of_guests=4,
            booking_datetime=cls.booking_time,
            table=cls.table_std_4_seater
        )

    def test_finds_smallest_available_table(self):
        """
        Test that when multiple tables are free, it picks the one with the
        smallest capacity that still fits the guests.
        """
        # Request a table for 2 guests at a time with no conflicts
        requested_time = TZ.localize(datetime(2025, 10, 10, 17, 0, 0))
        
        available_table = find_available_table(
            booking_datetime=requested_time,
            number_of_guests=2,
            seating_type_id=self.standard_seating.id
        )

        self.assertIsNotNone(available_table, "Should have found a table.")
        # It should choose the 2-seater over the 4-seater because it's a tighter fit.
        self.assertEqual(available_table.id, self.table_std_2_seater.id)

    def test_finds_larger_table_if_needed(self):
        """
        Test that it correctly finds a larger table if the smallest one is too small.
        """
        requested_time = TZ.localize(datetime(2025, 10, 10, 17, 0, 0))

        # Request for 3 guests; the 2-seater is too small.
        available_table = find_available_table(
            booking_datetime=requested_time,
            number_of_guests=3,
            seating_type_id=self.standard_seating.id
        )

        self.assertIsNotNone(available_table, "Should have found a table.")
        # It must select the 4-seater table.
        self.assertEqual(available_table.id, self.table_std_4_seater.id)

    def test_no_table_found_if_all_are_too_small(self):
        """
        Test that it returns None if no table has enough capacity.
        """
        requested_time = TZ.localize(datetime(2025, 10, 10, 17, 0, 0))

        # Request for 5 guests; the largest standard table has capacity 4.
        available_table = find_available_table(
            booking_datetime=requested_time,
            number_of_guests=5,
            seating_type_id=self.standard_seating.id
        )

        self.assertIsNone(available_table, "Should not find a table for 5 guests.")

    def test_no_table_found_if_inactive(self):
        """
        Test that inactive tables are never considered.
        """
        # We know an inactive table for 4 exists. Let's try to book it.
        # To force the check, let's book the *active* 4-seater table first.
        Booking.objects.create(
            user=self.user,
            number_of_guests=4,
            booking_datetime=self.booking_time, # Same time as the other booking
            table=self.table_std_4_seater
        )

        # Now, no *active* tables for 4 are available.
        available_table = find_available_table(
            booking_datetime=self.booking_time,
            number_of_guests=4,
            seating_type_id=self.standard_seating.id
        )

        self.assertIsNone(available_table, "Should not select an inactive table.")

    def test_avoids_direct_time_conflict(self):
        """
        Test that a table is not available at the exact time it is already booked.
        """
        # Try to book for 2 people at the same time the 4-seater is booked (7 PM).
        # The 2-seater should be available.
        available_table = find_available_table(
            booking_datetime=self.booking_time,
            number_of_guests=2,
            seating_type_id=self.standard_seating.id
        )
        self.assertEqual(available_table.id, self.table_std_2_seater.id)

        # Now, try to book for 4 people at 7 PM. The 4-seater is booked, so none should be found.
        available_table = find_available_table(
            booking_datetime=self.booking_time,
            number_of_guests=4,
            seating_type_id=self.standard_seating.id
        )
        self.assertIsNone(available_table, "Should not find a table due to direct conflict.")

    def test_avoids_overlap_conflict_new_booking_starts_during_old(self):
        """
        Test conflict where the new booking starts before the existing one ends.
        Existing booking: 19:00 - 21:00. New request: 20:00 - 22:00.
        """
        requested_time = self.booking_time + timedelta(hours=1) # 20:00

        available_table = find_available_table(
            booking_datetime=requested_time,
            number_of_guests=4,
            seating_type_id=self.standard_seating.id
        )
        self.assertIsNone(available_table, "Should not find a table due to overlap.")

    def test_avoids_overlap_conflict_new_booking_ends_during_old(self):
        """
        Test conflict where the new booking ends after the existing one starts.
        Existing booking: 19:00 - 21:00. New request: 18:00 - 20:00.
        """
        # Requested start time is 18:00, so it ends at 20:00, which overlaps with the 19:00 start.
        requested_time = self.booking_time - timedelta(hours=1) # 18:00

        available_table = find_available_table(
            booking_datetime=requested_time,
            number_of_guests=4,
            seating_type_id=self.standard_seating.id
        )
        self.assertIsNone(available_table, "Should not find a table due to overlap.")

    def test_allows_booking_immediately_after_another(self):
        """
        Test that a table is available right when another booking ends.
        Existing booking: 19:00 - 21:00. New request: 21:00 - 23:00.
        """
        # The existing booking ends at 19:00 + 2 hours = 21:00.
        requested_time = self.booking_time + DEFAULT_BOOKING_DURATION

        available_table = find_available_table(
            booking_datetime=requested_time,
            number_of_guests=4,
            seating_type_id=self.standard_seating.id
        )
        self.assertIsNotNone(available_table, "Should find a table immediately after another ends.")
        self.assertEqual(available_table.id, self.table_std_4_seater.id)

    def test_finds_table_for_update_by_excluding_own_booking(self):
        """
        Test the 'booking_to_exclude' argument, which is critical for updates.
        Without this, a user could never 'save' a booking without changing the time.
        """
        # Try to find a table for 4 at 7 PM, but exclude the existing booking at that time.
        available_table = find_available_table(
            booking_datetime=self.booking_time,
            number_of_guests=4,
            seating_type_id=self.standard_seating.id,
            booking_to_exclude=self.existing_booking
        )
        
        self.assertIsNotNone(available_table, "Should find the table when its own booking is excluded.")
        # It should find the very table that the booking belongs to.
        self.assertEqual(available_table.id, self.table_std_4_seater.id)