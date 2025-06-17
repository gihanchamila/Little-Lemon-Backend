from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.conf import settings

# Create your models here.

"""
    CASCADE: deletes the object containing the ForeignKey
    PROTECT: Prevent deletion of the referenced object.
    RESTRICT: Prevent deletion of the referenced object by raising RestrictedError

"""

class CustomUserManager(BaseUserManager):
    """
    Custom manager for CustomUser.

    Responsibilities:
    - Use email instead of username for authentication.
    - Automatically set sensible defaults for user creation.
    - Apply email verification logic by default for regular users.

    Methods:
        create_user: Creates and returns a regular user.
        create_superuser: Creates and returns a superuser.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with the given email and password.

        Required:
            - email
            - password

        Optional (via extra_fields):
            - first_name
            - last_name
            - mobile_number
            - is_email_verified
            - is_mobile_verified

        Notes:
            - is_email_verified defaults to False.
            - is_active is automatically set to False unless is_email_verified is True.
            - username field is removed and email is used for login.
        """
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        if not extra_fields.get('is_superuser', False):
            extra_fields.setdefault('is_email_verified', True)
            extra_fields['is_active'] = extra_fields['is_email_verified']

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with the given email and password.

        Superusers must have:
            - is_staff = True
            - is_superuser = True
            - is_active = True
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that replaces the default Django User model.

    Authentication uses email instead of username.

    Fields:
        - email (unique)
        - first_name
        - last_name
        - mobile_number (optional, unique)
        - is_email_verified: indicates whether email has been verified
        - is_mobile_verified: reserved for future mobile verification
        - is_staff: allows access to Django admin
        - is_active: account activation status
        - created_at: timestamp for user creation

    Meta:
        - USERNAME_FIELD is set to 'email'
        - REQUIRED_FIELDS include 'first_name' and 'last_name'
    """

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    mobile_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_mobile_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

class Occasion(models.Model):
    """
    Represents a special occasion for which a user might make a reservation or booking.
    
    Fields:
        name (CharField): The name/title of the occasion (e.g., Birthday, Anniversary).
        description (TextField): Optional detailed description of the occasion.
        is_active (BooleanField): Indicates whether the occasion is currently available.
        created_at (DateTimeField): Timestamp of when the occasion was created.
        updated_at (DateTimeField): Timestamp of the last update to the occasion.
    """

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        String representation of the occasion.

        Returns:
            str: The name of the occasion.
        """
        return self.name

class SeatingType(models.Model):
    """
    Represents a type of seating configuration available for booking or reservation.

    Fields:
        name (CharField): The name of the seating type (e.g., "Table for Two", "Window Seat").
        capacity (PositiveIntegerField): The maximum number of guests this seating type can accommodate.
        is_accessible (BooleanField): Indicates whether this seating is accessible (e.g., wheelchair accessible).
        price_multiplier (DecimalField): Multiplier used to adjust the base price based on the seating type.
        location_note (CharField): Optional note about where the seating is located (e.g., "near window").
        is_active (BooleanField): Indicates whether this seating type is currently in use or selectable.
    """

    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    is_accessible = models.BooleanField(default=True)
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    location_note = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """
        String representation of the seating type.

        Returns:
            str: A readable identifier with ID and name.
        """
        return f"Id : {self.id} | Name : {self.name}"

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Seating Types"
    
class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    CANCELLED = 'cancelled', 'Cancelled'
    EXPIRED = 'expired', 'Expired'
    NO_SHOW = 'no_show', 'No Show'

class PaymentStatus(models.TextChoices):
    UNPAID = 'unpaid', 'Unpaid'
    PAID = 'paid', 'Paid'
    REFUNDED = 'refunded', 'Refunded'

class PaymentMethod(models.TextChoices):
    STRIPE = 'stripe', 'Stripe'
    PAYPAL = 'paypal', 'PayPal'
    LOCAL_BANK = 'local_bank', 'Local Bank Transfer'

class Table(models.Model):
    """
    Represents an individual table in the venue that guests can be assigned to.

    Fields:
        table_number (CharField): A unique identifier for the table (e.g., "V1", "P5", "12").
        seating_type (ForeignKey): The type of seating this table belongs to, linked to SeatingType.
        capacity (PositiveIntegerField): The maximum number of guests the table can hold.
        is_active (BooleanField): Indicates if the table is currently available for use.
    """

    table_number = models.CharField(
        max_length=10,
        unique=True,
        help_text="e.g., 'V1', 'P5', '12'"
    )
    seating_type = models.ForeignKey('SeatingType', on_delete=models.PROTECT)
    capacity = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """
        String representation of the table.

        Returns:
            str: A human-readable identifier showing the table number, type, and capacity.
        """
        return f"Table id : {self.id} | Table {self.table_number} ({self.seating_type.name} - seats {self.capacity})"

    class Meta:
        ordering = ['table_number']

class Booking(models.Model):
    """
    Represents a reservation made by a user for a specific table, time, and occasion.

    Fields:
        user (ForeignKey): The user who made the booking.
        number_of_guests (PositiveIntegerField): Number of guests for the reservation.
        booking_datetime (DateTimeField): Date and time of the booking.
        occasion (ForeignKey): Optional special occasion (e.g., Birthday, Anniversary).
        table (ForeignKey): Table assigned for the booking.
        special_request (TextField): Any user-entered special requests (e.g., "Gluten-free meal").
        status (CharField): Current status of the booking (e.g., Pending, Confirmed, Cancelled).
        staff_note (TextField): Internal notes visible only to staff.
        payment_status (CharField): Indicates whether the booking has been paid.
        created_at (DateTimeField): Timestamp when the booking was created.
        updated_at (DateTimeField): Timestamp of the latest update.
        base_price_per_guest (DecimalField): Base price applied per guest.
        total_price (DecimalField): Final calculated total cost of the booking.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    number_of_guests = models.PositiveIntegerField()
    booking_datetime = models.DateTimeField()
    occasion = models.ForeignKey('Occasion', on_delete=models.SET_NULL, null=True)
    table = models.ForeignKey('Table', on_delete=models.PROTECT)
    special_request = models.TextField(blank=True, null=True)
    
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    staff_note = models.TextField(blank=True, null=True)
    
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    base_price_per_guest = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        """
        String representation of the booking instance.

        Returns:
            str: A summary of the booking with user ID, name, email, and date-time.
        """
        dt_format = self.booking_datetime.strftime('%Y-%m-%d @ %H:%M')
        return f"Booking for Id : {self.user.id} | Name : {self.user.first_name + self.user.last_name} | Email : {self.user.email} on {dt_format}"

    class Meta:
        ordering = ['-booking_datetime']
        verbose_name_plural = "Bookings"

class Payment(models.Model):
    """
    Represents a payment transaction linked to a booking.

    Fields:
        booking (OneToOneField): The booking this payment is associated with.
        user (ForeignKey): The user who made the payment.
        amount (DecimalField): Total amount paid.
        method (CharField): Payment method used (e.g., Card, Cash).
        status (CharField): Current status of the payment (e.g., Paid, Unpaid).
        transaction_id (CharField): Optional transaction/reference ID from the payment gateway.
        currency (CharField): Currency used for payment, default is 'LKR'.
        paid_at (DateTimeField): Timestamp when payment was completed.
        verified (BooleanField): Whether the payment has been verified manually or automatically.
        created_at (DateTimeField): Timestamp when the payment record was created.
        updated_at (DateTimeField): Timestamp of the last update to the payment record.
    """

    booking = models.OneToOneField('Booking', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    paid_at = models.DateTimeField(null=True, blank=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        String representation of the payment.

        Returns:
            str: A brief summary of the payment with amount, currency, and booking ID.
        """
        return f"Payment of {self.amount} {self.currency} for Booking {self.booking.id}"

class TimeSlot(models.Model):
    """
    Represents a specific time interval during which bookings can be made,
    optionally labeled and associated with a base price per guest.

    Fields:
        start_time (TimeField): Start time of the slot.
        end_time (TimeField): End time of the slot; must be after start_time.
        label (CharField): Optional descriptive label for the slot (e.g., "Lunch", "Dinner").
        base_price_per_guest (DecimalField): Base price applied per guest during this slot.
    """

    start_time = models.TimeField()
    end_time = models.TimeField()
    label = models.CharField(max_length=50, blank=True)
    base_price_per_guest = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def clean(self):
        """
        Validates the model before saving.

        Raises:
            ValidationError: If end_time is not strictly after start_time.
        """
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")

    def save(self, *args, **kwargs):
        """
        Override save to run full_clean() to ensure validation
        before actually saving the instance.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Provides a human-readable string representation of the time slot.

        Returns:
            str: The label with formatted start and end times, or just the times if no label is set.
        """
        time_format = '%H:%M'
        if self.label:
            return f"{self.label} ({self.start_time.strftime(time_format)} - {self.end_time.strftime(time_format)})"
        return f"{self.start_time.strftime(time_format)} - {self.end_time.strftime(time_format)}"

    