import datetime
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError

# Import all your models
from .models import (
    Occasion,
    SeatingType,
    Booking,
    Payment,
    TimeSlot,
)

# It's good practice to get the user model this way
User = get_user_model()


class ModelTests(TestCase):
    """
    A single TestCase class to set up common data for all model tests.
    setUpTestData runs once per class, which is efficient for read-only tests.
    """
    @classmethod
    def setUpTestData(cls):
        # Create a user that can be used across multiple tests
        cls.user = User.objects.create_user(
            first_name='test',
            last_name='user',
            password='password123',
            email='test@example.com'
        )

        # Create sample instances of related models
        cls.occasion = Occasion.objects.create(name='Birthday Party', description='A special birthday event.')
        cls.seating = SeatingType.objects.create(
            name='Rooftop',
            capacity=4,
            price_multiplier=Decimal('1.50')
        )

    def test_custom_user_model(self):
        """Test the CustomUser model fields and defaults."""
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.first_name, 'test')
        self.assertEqual(user.last_name, 'user')
        self.assertFalse(user.is_email_verified)
        self.assertFalse(user.is_mobile_verified)
        self.assertFalse(user.is_admin)
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.created_at)
        self.assertEqual(str(user), 'test@example.com')

    def test_occasion_model(self):
        """Test the Occasion model fields and defaults."""
        occasion = Occasion.objects.get(name='Birthday Party')
        self.assertEqual(occasion.name, 'Birthday Party')
        self.assertTrue(occasion.is_active)
        self.assertIsNotNone(occasion.created_at)
        self.assertEqual(str(occasion), 'Birthday Party')

    def test_seating_type_model(self):
        """Test the SeatingType model fields and defaults."""
        seating = SeatingType.objects.get(name='Rooftop')
        self.assertEqual(seating.name, 'Rooftop')
        self.assertTrue(seating.is_accessible)
        self.assertEqual(seating.price_multiplier, Decimal('1.50'))
        self.assertTrue(seating.is_active)
        self.assertEqual(str(seating), 'Rooftop')

    def test_timeslot_model(self):
        """Test the TimeSlot model's __str__ method."""
        slot = TimeSlot.objects.create(
            start_time=datetime.time(18, 0),
            end_time=datetime.time(20, 0),
            label="Dinner"
        )
        self.assertEqual(slot.start_time, datetime.time(18, 0))
        self.assertEqual(str(slot), "Dinner (18:00 - 20:00)")

        slot_no_label = TimeSlot.objects.create(
            start_time=datetime.time(12, 0),
            end_time=datetime.time(14, 0)
        )
        self.assertEqual(str(slot_no_label), "12:00 - 14:00")


class BookingRelationshipTests(TestCase):
    """Tests focusing on the Booking model and its relationships."""

    def setUp(self):
        """
        Setup runs before each test function to ensure a clean state,
        which is ideal for testing deletion behavior.
        """
        self.user = User.objects.create_user(email='test-booking@example.com', first_name='book', last_name='er', password='password123')
        self.occasion = Occasion.objects.create(name='Anniversary')
        self.seating = SeatingType.objects.create(name='Window Seat')
        self.booking = Booking.objects.create(
            user=self.user,
            number_of_guests=2,
            booking_datetime=timezone.now() + timezone.timedelta(days=5),
            occasion=self.occasion,
            seating_type=self.seating
        )

    def test_booking_creation_and_defaults(self):
        """Test that a booking can be created with correct defaults."""
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(self.booking.user.email, 'test-booking@example.com')
        self.assertEqual(self.booking.status, 'pending')
        self.assertEqual(self.booking.payment_status, 'unpaid')
        self.assertIsNotNone(self.booking.created_at)
        self.assertIn('Booking for test-booking@example.com', str(self.booking))

    def test_user_deletion_cascades_to_booking(self):
        """Test that deleting a User also deletes their Bookings (CASCADE)."""
        self.user.delete()
        self.assertEqual(Booking.objects.count(), 0)

    def test_occasion_deletion_sets_booking_field_to_null(self):
        """Test that deleting an Occasion sets the booking's occasion to NULL (SET_NULL)."""
        self.occasion.delete()
        self.booking.refresh_from_db()  # Reload the object from the database
        self.assertIsNone(self.booking.occasion)

    def test_seating_type_deletion_is_protected(self):
        """Test that deleting a SeatingType in use raises a ProtectedError."""
        with self.assertRaises(ProtectedError):
            self.seating.delete()

        # Verify the booking and seating type still exist
        self.assertTrue(Booking.objects.filter(id=self.booking.id).exists())
        self.assertTrue(SeatingType.objects.filter(id=self.seating.id).exists())


class PaymentRelationshipTests(TestCase):
    """Tests focusing on the Payment model and its relationships."""

    def setUp(self):
        self.user = User.objects.create_user(email='test-payment@example.com', first_name='pay', last_name='er', password='password123')
        seating = SeatingType.objects.create(name='Standard Table')
        self.booking = Booking.objects.create(
            user=self.user,
            number_of_guests=4,
            booking_datetime=timezone.now(),
            seating_type=seating
        )

    def test_payment_creation_and_defaults(self):
        """Test that a payment can be created with correct defaults."""
        payment = Payment.objects.create(
            booking=self.booking,
            user=self.user,
            amount=Decimal('50.00'),
            method='stripe'
        )
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.currency, 'LKR')
        self.assertFalse(payment.verified)
        self.assertEqual(str(payment), f"Payment of 50.00 LKR for Booking {self.booking.id}")

    def test_booking_deletion_cascades_to_payment(self):
        """Test that deleting a Booking also deletes its Payment (CASCADE)."""
        Payment.objects.create(booking=self.booking, user=self.user, amount=Decimal('1.00'), method='stripe')
        self.assertEqual(Payment.objects.count(), 1)
        self.booking.delete()
        self.assertEqual(Payment.objects.count(), 0)

    def test_onetoone_booking_constraint(self):
        """Test that a Booking can only have one Payment (OneToOneField)."""
        # Create the first, valid payment
        Payment.objects.create(booking=self.booking, user=self.user, amount=Decimal('50.00'), method='stripe')

        # Attempting to create a second payment for the same booking should fail
        with self.assertRaises(IntegrityError):
            Payment.objects.create(
                booking=self.booking,  # Same booking
                user=self.user,
                amount=Decimal('25.00'),
                method='paypal'
            )