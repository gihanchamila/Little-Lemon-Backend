from rest_framework import serializers
from .models import Menu, Booking

class menuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ['id', 'Title', 'Price', 'Inventory']

class bookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'Name', 'NoOfGuests', 'BookingDate']
