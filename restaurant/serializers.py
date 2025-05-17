from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Menu, Booking

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']

class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ['id', 'title', 'price', 'inventory']

class BookingSerializer(serializers.ModelSerializer):
    no_of_guests = serializers.IntegerField(min_value=1, max_value=6, error_messages={
        'min_value': 'Number of guests must be at least 1.',
        'max_value': 'Number of guests cannot exceed 6.'
    })
    class Meta:
        model = Booking
        fields = ['name', 'no_of_guests', 'booking_date']
