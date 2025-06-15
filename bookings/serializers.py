from djoser.serializers import UserCreateSerializer, UserSerializer
from .models import CustomUser, Occasion, SeatingType, Booking, Payment, TimeSlot, Table, PaymentStatus, BookingStatus
from rest_framework import serializers
from django.utils import timezone
from .pricing import calculate_booking_price
from .availability import find_available_table


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying user information.
    Read-only, used for nesting in other serializers.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'mobile_number']
        read_only_fields = fields

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    Handles password validation and creation.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'mobile_number', 'password']

    def create(self, validated_data):
        # Use the custom manager's create_user method to handle password hashing
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            mobile_number=validated_data.get('mobile_number'),
            password=validated_data['password']
        )
        return user
    
    def validate(self, data):
        mobile_number = data.get('mobile_number')

        if not mobile_number:
            raise serializers.ValidationError({
                'mobile_number': 'This field is required.'
            })
        
        return data
    
class OccasionSerializer(serializers.ModelSerializer):
    """ Simple serializer for listing Occasions. """
    class Meta:
        model = Occasion
        fields = ['id', 'name', 'description']

class SeatingTypeSerializer(serializers.ModelSerializer):
    """ Simple serializer for listing Seating Types. """
    capacity = serializers.IntegerField(required=True)
    is_accessible = serializers.BooleanField(required=True)
    class Meta:
        model = SeatingType
        fields = ['id', 'name', 'capacity', 'is_accessible', 'price_multiplier', 'location_note']

class TimeSlotSerializer(serializers.ModelSerializer):
    """ Serializer for available time slots. """

    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time', 'label', 'base_price_per_guest']

class PriceCalculationSerializer(serializers.Serializer):
    """
    Serializer to validate inputs for the price calculation endpoint.
    """
    number_of_guests = serializers.IntegerField(min_value=1)
    booking_datetime = serializers.DateTimeField()
    seating_type_id = serializers.PrimaryKeyRelatedField(
        queryset=SeatingType.objects.filter(is_active=True),
        write_only=True
    )

    class Meta:
        fields = ['number_of_guests', 'booking_datetime', 'seating_type_id']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['user', 'verified', 'created_at', 'updated_at']

    def validate(self, data):
        if Payment.objects.filter(booking=data['booking']).exists():
            raise serializers.ValidationError("This booking already has a payment.")
        return data
    
    def validate_booking(self, booking):
        request = self.context['request']
        user = request.user

        # Ensure the booking belongs to the logged-in user
        if booking.user != user:
            raise serializers.ValidationError("You can only make payments for your own bookings.")

        # Optional: Prevent double payment
        if hasattr(booking, 'payment'):
            raise serializers.ValidationError("Payment has already been made for this booking.")

        return booking
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user

        # Create the payment first
        payment = super().create(validated_data)

        # Update the booking if payment status is "paid"
        if payment.status == PaymentStatus.PAID:
            booking = payment.booking
            booking.status = BookingStatus.CONFIRMED
            booking.payment_status = PaymentStatus.PAID
            booking.save()

        return payment

class TableSerializer(serializers.ModelSerializer):
    seating_type = SeatingTypeSerializer(read_only=True)
    seating_type_id = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all(), required=True)
    class Meta:
        model = Table
        fields = ['id', 'table_number', 'capacity', 'seating_type', 'seating_type_id']
    
class BookingSerializer(serializers.ModelSerializer):
    """
    The main serializer for handling bookings.
    Handles both creation (write) and retrieval (read) with different representations.
    """
    # --- Read-only Nested Representations for GET requests ---
    # To show detailed info instead of just IDs
    user = UserSerializer(read_only=True)
    occasion = OccasionSerializer(read_only=True)
    table = TableSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    # --- Write-only fields for POST/PUT requests ---
    # The frontend will send the ID of the related object
    occasion_id = serializers.PrimaryKeyRelatedField(
        queryset=Occasion.objects.filter(is_active=True), 
        source='occasion', 
        write_only=True,
        required=False,
        allow_null=True
    )

    seating_type_id = serializers.PrimaryKeyRelatedField(
        queryset=SeatingType.objects.filter(is_active=True), 
        write_only=True,
    )

    class Meta:
        model = Booking
        fields = [
            'id', 'number_of_guests', 'booking_datetime', 'special_request', 
            'user', 'occasion', 'table',
            'occasion_id', 'seating_type_id',
            'status', 'payment_status', 'staff_note', 'total_price', 'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'payment_status', 'staff_note', 'total_price']

    def validate_booking_datetime(self, value):
        """
        Check that the booking is not in the past.
        """
        if value < timezone.now():
            raise serializers.ValidationError("Booking date and time cannot be in the past.")
        return value

    def validate(self, data):
        """
        Object-level validation.
        Check that the number of guests does not exceed the capacity of the seating type.
        """
        # On creation, 'seating_type' is in data because of the `source` argument
        seating_type_id = data.get('seating_type_id').id
        number_of_guests = data.get('number_of_guests')

        booking_datetime = data.get('booking_datetime')

        if not (seating_type_id and number_of_guests and booking_datetime):
            raise serializers.ValidationError("Seating type, number of guests, and booking datetime are required.")

        available_table = find_available_table(
            booking_datetime=booking_datetime,
            number_of_guests=number_of_guests,
            seating_type_id=seating_type_id
        )

        if not available_table:
            raise serializers.ValidationError(
                "Sorry, no tables are available for the selected time, number of guests, and seating preference."
            )

        # If we found a table, attach it to the validated data to use in the create() method.
        data['table'] = available_table
        return data
    
    def create(self, validated_data):
        """
        Create the booking using the available table found during validation.
        """
        # We no longer need 'seating_type_id' for creation, so we pop it.
        validated_data.pop('seating_type_id')
        
        # The table object is already in validated_data from our validate() method.
        table = validated_data.get('table')
        
        # Recalculate price based on the actual table's seating type
        price = calculate_booking_price(
            number_of_guests=validated_data['number_of_guests'],
            booking_datetime=validated_data['booking_datetime'],
            seating_type=table.seating_type # Use seating_type from the found table
        )
        validated_data['total_price'] = price
        
        booking = Booking.objects.create(**validated_data)
        return booking

    def update(self, instance, validated_data):
        """
        Recalculate the price if relevant fields are changed.
        """
        # If any of the price-affecting fields are in the update data, recalculate
        recalculate = any(key in validated_data for key in ['number_of_guests', 'booking_datetime', 'seating_type'])

        if recalculate:
            # Use existing instance data as default and override with new data
            number_of_guests = validated_data.get('number_of_guests', instance.number_of_guests)
            booking_datetime = validated_data.get('booking_datetime', instance.booking_datetime)
            seating_type = validated_data.get('seating_type', instance.seating_type)
            
            price = calculate_booking_price(
                number_of_guests=number_of_guests,
                booking_datetime=booking_datetime,
                seating_type=seating_type
            )
            validated_data['total_price'] = price
            
        return super().update(instance, validated_data)