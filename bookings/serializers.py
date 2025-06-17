from djoser.serializers import UserCreateSerializer, UserSerializer
from .models import CustomUser, Occasion, SeatingType, Booking, Payment, TimeSlot, Table, PaymentStatus, BookingStatus
from rest_framework import serializers
from django.utils import timezone
from .pricing import calculate_booking_price
from .availability import find_available_table
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the CustomUser model, primarily for read-only purposes.
    
    This serializer is designed to output user information in a controlled way,
    typically for nesting inside other serializers or for displaying user data.
    
    Fields:
        - id: Unique identifier of the user.
        - email: User's email address (used as username).
        - first_name: User's first name.
        - last_name: User's last name.
        - mobile_number: User's mobile phone number (optional).
    
    Note:
        All fields are read-only, meaning this serializer does not support
        creating or updating user instances.
    """

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'mobile_number']
        read_only_fields = fields

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering new users.

    Handles:
    - Validation of required fields including email, names, mobile number, and password.
    - Password input is write-only and styled for password fields.
    - Creation of user instances using the custom user manager to ensure password hashing.

    Fields:
        - email (EmailField): User's email address, used as username.
        - first_name (CharField): User's first name.
        - last_name (CharField): User's last name.
        - mobile_number (CharField): User's mobile number (required).
        - password (CharField): Write-only password field.

    Validation:
        - Ensures mobile_number is provided, raising a ValidationError if missing.

    Creation:
        - Uses `CustomUser.objects.create_user` to handle user creation and password hashing.
    """

    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'mobile_number', 'password']

    def create(self, validated_data):
        """
        Creates a new CustomUser instance with hashed password.

        Args:
            validated_data (dict): Validated data from the serializer.

        Returns:
            CustomUser: Newly created user instance.
        """
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            mobile_number=validated_data.get('mobile_number'),
            password=validated_data['password']
        )
        return user

    def validate(self, data):
        """
        Validates that the mobile_number field is provided.

        Args:
            data (dict): Input data to validate.

        Raises:
            serializers.ValidationError: If mobile_number is missing.

        Returns:
            dict: Validated data.
        """
        mobile_number = data.get('mobile_number')

        if not mobile_number:
            raise serializers.ValidationError({
                'mobile_number': 'This field is required.'
            })

        return data
    
class OccasionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Occasion model.

    Used primarily for listing occasion instances with basic details.

    Fields:
        - id (Integer): Unique identifier of the occasion.
        - name (CharField): Name/title of the occasion.
        - description (TextField): Optional description providing more details about the occasion.
    """

    class Meta:
        model = Occasion
        fields = ['id', 'name', 'description']

class SeatingTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for the SeatingType model.

    Used to list seating type details with validation for required fields.

    Fields:
        - id (Integer): Unique identifier of the seating type.
        - name (CharField): Name of the seating type.
        - capacity (Integer): Maximum number of guests the seating type can accommodate. Required.
        - is_accessible (Boolean): Indicates if the seating type is accessible. Required.
        - price_multiplier (Decimal): Multiplier applied to base prices for this seating type.
        - location_note (CharField): Additional notes about the seating location.
    """

    capacity = serializers.IntegerField(required=True)
    is_accessible = serializers.BooleanField(required=True)

    class Meta:
        model = SeatingType
        fields = ['id', 'name', 'capacity', 'is_accessible', 'price_multiplier', 'location_note']

class TimeSlotSerializer(serializers.ModelSerializer):
    """
    Serializer for the TimeSlot model.

    Used to represent available booking time slots including pricing information.

    Fields:
        - id (Integer): Unique identifier of the time slot.
        - start_time (TimeField): Start time of the slot.
        - end_time (TimeField): End time of the slot.
        - label (CharField): Optional label or name for the time slot (e.g., "Lunch", "Dinner").
        - base_price_per_guest (Decimal): Base price charged per guest during this time slot.
    """

    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time', 'label', 'base_price_per_guest']

class PriceCalculationSerializer(serializers.Serializer):
    """
    Serializer for validating input data for the price calculation endpoint.

    This serializer is not tied to a model but is used to ensure the required inputs
    for calculating booking prices are valid and complete.

    Fields:
        - number_of_guests (IntegerField): The number of guests for the booking. Must be at least 1.
        - booking_datetime (DateTimeField): The date and time of the booking.
        - seating_type_id (PrimaryKeyRelatedField): ID of an active SeatingType. Must reference an active seating type.

    Notes:
        - seating_type_id is write-only as it is expected as input but not returned.
        - The serializer performs validation such as ensuring the seating type is active.
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
    """
    Serializer for the Payment model.

    Handles creation and validation of payment records associated with bookings.

    Meta:
        - Uses all fields from Payment model.
        - Read-only fields: 'user', 'verified', 'created_at', 'updated_at' to prevent client-side modification.

    Validations:
        - Ensures only one payment exists per booking.
        - Validates that the booking belongs to the logged-in user.
        - Prevents duplicate payments on the same booking.

    Creation:
        - Assigns the current logged-in user as the payment user.
        - If the payment status is 'paid', updates the related booking's status to 'confirmed' and payment status to 'paid'.
    """

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

        # Optional: Prevent duplicate payments
        if hasattr(booking, 'payment'):
            raise serializers.ValidationError("Payment has already been made for this booking.")

        return booking

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user

        # Create the payment record
        payment = super().create(validated_data)

        # Update booking status if payment is successful
        if payment.status == PaymentStatus.PAID:
            booking = payment.booking
            booking.status = BookingStatus.CONFIRMED
            booking.payment_status = PaymentStatus.PAID
            booking.save()

        return payment

class TableSerializer(serializers.ModelSerializer):
    """
    Serializer for the Table model.

    Fields:
        - id: Primary key of the table.
        - table_number: Unique identifier string for the table (e.g., "V1", "P5").
        - capacity: Number of guests the table can accommodate.
        - seating_type: Nested read-only serializer showing details of the related SeatingType.
        - seating_type_id: Writeable field to specify the SeatingType by its primary key when creating or updating a Table.

    Notes:
        - `seating_type` is read-only and used for displaying related SeatingType details.
        - `seating_type_id` is required when creating or updating a Table, and expects a valid SeatingType instance.
    """

    seating_type = SeatingTypeSerializer(read_only=True)
    seating_type_id = serializers.PrimaryKeyRelatedField(
        queryset=SeatingType.objects.filter(is_active=True),  # corrected queryset for seating types, assuming intended
        required=True
    )

    class Meta:
        model = Table
        fields = ['id', 'table_number', 'capacity', 'seating_type', 'seating_type_id']
    
class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for managing Booking objects.

    Features:
    - Handles both reading (GET) and writing (POST/PUT) bookings with different representations.
    - Uses nested serializers for user, occasion, and table details on read.
    - Accepts related object IDs for occasion and seating type on write.
    - Validates booking datetime is not in the past.
    - Validates availability of tables based on seating type, guest count, and datetime.
    - Calculates and sets the total price during creation and updates.
    
    Fields:
        - id: Booking primary key.
        - number_of_guests: Number of guests for the booking.
        - booking_datetime: Date and time of the booking.
        - special_request: Optional special requests.
        - user: Nested user details (read-only).
        - occasion: Nested occasion details (read-only).
        - table: Nested table details (read-only).
        - occasion_id: Occasion primary key for write operations (optional).
        - seating_type_id: SeatingType primary key for write operations (required).
        - status: Booking status (read-only).
        - payment_status: Payment status (read-only).
        - staff_note: Staff notes (read-only).
        - total_price: Calculated total booking price (read-only).
        - created_at, updated_at: Timestamps (read-only).
    
    Validation:
        - Booking datetime must be in the future.
        - Number of guests, booking datetime, and seating type must be provided.
        - A suitable available table must exist for the booking parameters.
    
    Methods:
        - validate_booking_datetime: Ensures booking datetime is not in the past.
        - validate: Object-level validation to check table availability.
        - create: Creates a booking after confirming table availability and calculates total price.
        - update: Recalculates price if relevant fields change.
    """

    user = UserSerializer(read_only=True)
    occasion = OccasionSerializer(read_only=True)
    table = TableSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    base_price_per_guest = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

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
            'status', 'payment_status', 'staff_note', 'total_price', 'base_price_per_guest', 'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'payment_status', 'staff_note', 'total_price']

    def validate_booking_datetime(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Booking date and time cannot be in the past.")
        return value

    def validate(self, data):
        seating_type_id = data.get('seating_type_id')
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

        data['table'] = available_table
        return data
    
    def get_base_price(self, booking_datetime):
        from bookings.models import TimeSlot
        booking_time = booking_datetime.time()
        try:
            timeslot = TimeSlot.objects.get(start_time__lte=booking_time, end_time__gte=booking_time)
        except TimeSlot.DoesNotExist:
            raise ValidationError({"booking_datetime": "No valid time slot found for the selected time."})
        except TimeSlot.MultipleObjectsReturned:
            raise ValidationError({"error": "Overlapping time slots configured. Contact support."})
        return timeslot.base_price_per_guest

    def create(self, validated_data):
        validated_data.pop('seating_type_id')  # No longer needed after validation

        table = validated_data['table']
        seating_type = table.seating_type
        number_of_guests = validated_data['number_of_guests']
        booking_datetime = validated_data['booking_datetime']

        base_price_per_guest = self.get_base_price(booking_datetime)
        if table.capacity < number_of_guests:
            raise serializers.ValidationError({
                "non_field_errors": [
                    f"A system error occurred: The selected table (capacity: {table.capacity}) "
                    f"cannot accommodate the number of guests ({number_of_guests}). Please try again."
                ]
            })

        total_price = calculate_booking_price(
            number_of_guests=number_of_guests,
            booking_datetime=validated_data['booking_datetime'],
            seating_type=table.seating_type
        )

        validated_data['base_price_per_guest'] = base_price_per_guest
        validated_data['total_price'] = total_price

        booking = Booking.objects.create(**validated_data)
        return booking

    def update(self, instance, validated_data):
        recalculate = any(key in validated_data for key in ['number_of_guests', 'booking_datetime', 'seating_type'])

        if recalculate:
            number_of_guests = validated_data.get('number_of_guests', instance.number_of_guests)
            booking_datetime = validated_data.get('booking_datetime', instance.booking_datetime)
            seating_type = validated_data.get('seating_type', instance.seating_type)
            number_of_guests = validated_data.get('number_of_guests', instance.number_of_guests)

            base_price_per_guest = self.get_base_price(booking_datetime)

            price = calculate_booking_price(
                number_of_guests=number_of_guests,
                booking_datetime=booking_datetime,
                seating_type=seating_type
            )
            validated_data['base_price_per_guest'] = base_price_per_guest
            validated_data['total_price'] = price

        return super().update(instance, validated_data)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer extending Simple JWT's TokenObtainPairSerializer.

    Purpose:
    - Customize JWT token payload by adding extra user claims (email, username).
    - Include serialized user information in the token response payload upon login.

    Methods:
    - get_token(cls, user):
        Overrides the default method to add custom claims to the token payload.
        Adds 'email' and 'username' from the user model to the JWT.

    - validate(self, attrs):
        Called during login to validate credentials.
        Calls super() to get the default token response (access and refresh tokens).
        Adds the serialized user data (via UserSerializer) to the response under 'user' key.
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['username'] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user_data = UserSerializer(self.user).data
        data['user'] = user_data
        return data