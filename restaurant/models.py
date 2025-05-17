from django.db import models

# Create your models here.
# Use snake_case for field names

class Booking(models.Model):
    name = models.CharField(max_length=255)
    no_of_guests = models.IntegerField(verbose_name="Number of Guests")
    booking_date = models.DateField()

    def __str__(self):
        return f"{self.name} - {self.no_of_guests} guests on {self.booking_date}"


class Menu(models.Model):
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    inventory = models.IntegerField(5)

    def __str__(self):
        return f"{self.title} - ${self.price} ({self.inventory} in stock)"

