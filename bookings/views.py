from rest_framework import generics, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch
from .filters import BookingFilter
from .pricing import calculate_booking_price
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .permissions import IsManager
from .availability import find_available_table
from rest_framework.decorators import api_view
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError
from datetime import datetime



from .models import CustomUser, Occasion, SeatingType, Booking, TimeSlot, Table, Payment
from .serializers import (
    UserRegistrationSerializer,
    OccasionSerializer,
    SeatingTypeSerializer,
    BookingSerializer,
    TimeSlotSerializer,
    PriceCalculationSerializer,
    UserSerializer,
    TableSerializer,
    PaymentSerializer
)

class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.

    Allows anyone (unauthenticated users) to create a new user account.
    Uses the UserRegistrationSerializer to validate and create users.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class UserAdminViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for managing users.

    Provides full CRUD operations on CustomUser instances.
    Access is restricted to users with admin privileges (is_staff=True).
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class OccasionAdminViewSet(viewsets.ModelViewSet):
    """
    Admin and Manager endpoint for full CRUD operations on Occasion instances.
    
    Permissions:
        - Accessible by admin users (`is_staff=True`)
        - Accessible by users in the 'Manager' group
    
    Provides:
        - List all occasions
        - Retrieve a single occasion
        - Create new occasions
        - Update existing occasions
        - Delete occasions
    """
    queryset = Occasion.objects.all()
    serializer_class = OccasionSerializer
    permission_classes = [IsAdminUser | IsManager]

class SeatingTypeAdminViewSet(viewsets.ModelViewSet):
    """
    Admin-only endpoint for full CRUD operations on SeatingType instances.
    
    Permissions:
        - Only accessible by admin users (is_staff=True)
    
    Features:
        - List all seating types
        - Retrieve a single seating type
        - Create new seating types
        - Update existing seating types
        - Delete seating types
    """
    queryset = SeatingType.objects.all()
    serializer_class = SeatingTypeSerializer
    permission_classes = [IsAdminUser]

class TimeSlotAdminViewSet(viewsets.ModelViewSet):
    """
    Admin-only endpoint for full CRUD operations on TimeSlot instances.
    
    Permissions:
        - Only accessible by admin users (is_staff=True)
    
    Features:
        - List all time slots
        - Retrieve a single time slot
        - Create new time slots
        - Update existing time slots
        - Delete time slots
    """
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAdminUser]

class BookingAdminViewSet(viewsets.ModelViewSet):
    """
    Admin and Manager endpoint for full CRUD operations on Booking instances.
    
    Permissions:
        - Accessible by admin users (is_staff=True)
        - Accessible by users in the 'Manager' group
    
    Features:
        - List all bookings
        - Retrieve a single booking
        - Create new bookings
        - Update existing bookings
        - Delete bookings
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAdminUser | IsManager]

class TableAdminViewSet(viewsets.ModelViewSet):
    """
    Admin and Manager endpoint for full CRUD operations on Table instances.

    Permissions:
        - Accessible by admin users (is_staff=True)
        - Accessible by users in the 'Manager' group
    
    Features:
        - List all tables
        - Retrieve a single table
        - Create new tables
        - Update existing tables
        - Delete tables
    """
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAdminUser | IsManager]

class PaymentAdminViewSet(viewsets.ModelViewSet):
    """
    Admin and Manager endpoint for full CRUD operations on Payment records.

    Permissions:
        - Accessible by admin users (is_staff=True)
        - Accessible by users in the 'Manager' group
    
    Features:
        - List all payments
        - Retrieve a single payment
        - Create new payments
        - Update existing payments
        - Delete payments
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminUser | IsManager]

class OccasionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public endpoint to list and retrieve active occasions.
    Read-only: no creation, update, or delete allowed.

    Permissions:
        - Allow any user (authenticated or not) to view the list/details.

    Queryset:
        - Only occasions marked as active (`is_active=True`) are included.
    """
    queryset = Occasion.objects.filter(is_active=True)
    serializer_class = OccasionSerializer
    permission_classes = [AllowAny]

class SeatingTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public endpoint to list and retrieve active seating types.
    Read-only: no create, update, or delete allowed.

    Permissions:
        - Accessible by any user (authenticated or anonymous).

    Queryset:
        - Only seating types marked as active (`is_active=True`) are included.
    """
    queryset = SeatingType.objects.filter(is_active=True)
    serializer_class = SeatingTypeSerializer
    permission_classes = [AllowAny]

class TimeSlotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public endpoint to list available time slots.
    Currently returns all time slots ordered by start time.
    
    Can be extended to filter slots by date or availability.
    
    Permissions:
        - Accessible by any user (authenticated or anonymous).
    """
    queryset = TimeSlot.objects.all().order_by('start_time')
    serializer_class = TimeSlotSerializer
    permission_classes = [AllowAny]

    # Optional example: filter by date query param to show slots on a specific date
    def get_queryset(self):
        queryset = super().get_queryset()
        date = self.request.query_params.get('date')
        if date:
            # Assuming you have a date field on TimeSlot or related model to filter by
            # Adjust this filtering logic based on your model's date fields
            queryset = queryset.filter(start_time__date=date)
        return queryset

class TableViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public endpoint to list all tables.
    Read-only access for all users.
    """
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [AllowAny]

class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bookings.
    - Users can see and manage their own bookings.
    - Staff can see all bookings but should not modify via this API.
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookingFilter 

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def calculate_price(self, request):
        """
        Preview booking price without creating a booking.
        """
        serializer = PriceCalculationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                seating_type = SeatingType.objects.get(id=data['seating_type_id'].id)
                price = calculate_booking_price(
                    number_of_guests=data['number_of_guests'],
                    booking_datetime=data['booking_datetime'],
                    seating_type=seating_type
                )
                return Response({'total_price': price}, status=status.HTTP_200_OK)
            except SeatingType.DoesNotExist:
                return Response({'error': 'Invalid seating type.'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all().select_related('user', 'occasion', 'table__seating_type').order_by('-booking_datetime')
        return Booking.objects.filter(user=user).select_related('user', 'occasion', 'table__seating_type').order_by('-booking_datetime')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        booking = self.get_object()
        # Example restriction (optional)
        # if booking.booking_datetime - timezone.now() < timedelta(hours=24):
        #     raise PermissionDenied("Cannot modify a booking less than 24 hours in advance.")
        serializer.save(user=self.request.user)

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']  # disables PATCH, PUT, DELETE

    def get_queryset(self):
        # Users can only see their own payments
        return Payment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign the logged-in user to the payment
        serializer.save(user=self.request.user)


@api_view(["POST"])
def check_availability(request):
    try:
        seating_type_id = request.data.get('seating_type_id')
        number_of_guests = request.data.get('number_of_guests')
        booking_datetime = request.data.get('booking_datetime')

        if not booking_datetime or not number_of_guests or not seating_type_id:
            return Response({"detail": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        booking_datetime = parse_datetime(booking_datetime)

        if booking_datetime is None:
            return Response({"detail": "Invalid date format."}, status=status.HTTP_400_BAD_REQUEST)

        available_table = find_available_table(
            booking_datetime=booking_datetime,
            number_of_guests=number_of_guests,
            seating_type_id=seating_type_id,
        )

        if available_table:
            return Response({
                "available": True,
                "table_id": available_table.id,
                "capacity": available_table.capacity,
            })
        else:
            return Response({
                "available": False,
                "detail": "No available table for the selected time and criteria."
            })

    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def get_total_price(request):
    try:
        number_of_guests = int(request.data.get('number_of_guests'))
        booking_datetime = request.data.get('booking_datetime')
        seating_type_id = request.data.get('seating_type_id')

        if not (number_of_guests and booking_datetime and seating_type_id):
            raise ValidationError("Missing required fields.")

        booking_dt = datetime.fromisoformat(booking_datetime)
        seating_type = SeatingType.objects.get(pk=seating_type_id)

        total = calculate_booking_price(number_of_guests, booking_dt, seating_type)
        return Response({"total_price": total})
    except SeatingType.DoesNotExist:
        raise ValidationError("Invalid seating type.")
    except Exception as e:
        raise ValidationError(str(e))