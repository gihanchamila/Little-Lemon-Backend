from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.

"""
    CASCADE: deletes the object containing the ForeignKey
    PROTECT: Prevent deletion of the referenced object.
    RESTRICT: Prevent deletion of the referenced object by raising RestrictedError

"""

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    mobile_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_mobile_verified = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = ['first_name', 'last_name']

class Occasion(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class SeatingType(models.Model):
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    is_accessible = models.BooleanField(default=True)
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    location_note = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    number_of_guests = models.PositiveIntegerField()
    booking_datetime = models.DateTimeField()  # Instead of separate date/time
    occasion = models.ForeignKey('Occasion', on_delete=models.SET_NULL, null=True)
    seating_type = models.ForeignKey('SeatingType', on_delete=models.PROTECT)
    special_request = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('no_show', 'No Show'),
    ], default='pending')
    staff_note = models.TextField(blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=[
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ], default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        dt_format = self.booking_datetime.strftime('%Y-%m-%d @ %H:%M')
        return f"Booking for {self.user.username} on {dt_format}"
    

class Payment(models.Model):
    booking = models.OneToOneField('Booking', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, choices=[
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('local_bank', 'Local Bank Transfer'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ], default='pending')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    currency = models.CharField(max_length=10, default='LKR')
    paid_at = models.DateTimeField(null=True, blank=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} {self.currency} for Booking {self.booking.id}"

class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    label = models.CharField(max_length=50, blank=True)

    def __str__(self):
        time_format = '%H:%M'
        if self.label:
            return f"{self.label} ({self.start_time.strftime(time_format)} - {self.end_time.strftime(time_format)})"
        return f"{self.start_time.strftime(time_format)} - {self.end_time.strftime(time_format)}"