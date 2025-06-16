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

# ===============================================================
# Authentication Views
# ===============================================================

class UserRegistrationView(generics.CreateAPIView):
    """
    Public endpoint for new user registration.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny] 

# ===============================================================
# Admin Management ViewSets (Full C.R.U.D. for Admins)
# ===============================================================

class UserAdminViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class OccasionAdminViewSet(viewsets.ModelViewSet):
    """
    Admin endpoint for full C.R.U.D. operations on Occasions.
    """
    queryset = Occasion.objects.all()
    serializer_class = OccasionSerializer
    permission_classes = [IsAdminUser | IsManager] 

class SeatingTypeAdminViewSet(viewsets.ModelViewSet):
    """
    Admin endpoint for full C.R.U.D. operations on Seating Types.
    """
    queryset = SeatingType.objects.all()
    serializer_class = SeatingTypeSerializer
    permission_classes = [IsAdminUser] 

class TimeSlotAdminViewSet(viewsets.ModelViewSet):
    """
    Admin endpoint for full C.R.U.D. operations on Time Slots.
    """
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAdminUser] 

class BookingAdminViewSet(viewsets.ModelViewSet):
     
    """
    Admin endpoint for full C.R.U.D. operations on Bookings.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAdminUser | IsManager]

class TableAdminviewSet(viewsets.ModelViewSet):
    """
    Admin endpoint for full C.R.U.D. operations on Tables.
    """

    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAdminUser | IsManager]

class PaymentAdminViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminUser | IsManager]
# ===============================================================
# Public Lookup Views (for frontend dropdowns, etc.)
# ===============================================================

class OccasionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Provides a read-only list of available occasions.
    """
    queryset = Occasion.objects.filter(is_active=True)
    serializer_class = OccasionSerializer
    permission_classes = [AllowAny] 

class SeatingTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Provides a read-only list of available seating types.
    """
    queryset = SeatingType.objects.filter(is_active=True)
    serializer_class = SeatingTypeSerializer
    permission_classes = [AllowAny] 

class TimeSlotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Provides a read-only list of available time slots.
    This could be expanded to show only available slots for a given day.
    """
    queryset = TimeSlot.objects.all().order_by('start_time')
    serializer_class = TimeSlotSerializer
    permission_classes = [AllowAny] 

class TableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [AllowAny]

# ===============================================================
# Core Application Views
# ===============================================================

class BookingViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing, creating, and editing bookings.
    - Users can only see and manage their own bookings.
    - Staff members can see all bookings but cannot modify them via this API.
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookingFilter 

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def calculate_price(self, request):
        """
        An endpoint to preview the booking price without creating a booking.
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
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        """
        This view should return a list of all the bookings
        for the currently authenticated user.
        Staff users can see all bookings.

        PERFORMANCE NOTE: We use `select_related` to perform a single,
        efficient JOIN query to fetch related objects, preventing the N+1 problem.
        """
        user = self.request.user
        if user.is_staff:
            # Staff can see all bookings, ordered for clarity
            return Booking.objects.all().select_related('user', 'occasion', 'table__seating_type')
        
        # Normal users see only their own bookings
        return Booking.objects.filter(user=user).select_related('user', 'occasion', 'table__seating_type')

    def perform_create(self, serializer):
        """
        SECURITY NOTE: Automatically assign the logged-in user to the booking.
        This prevents a user from creating a booking for someone else.
        The `user` field is made read-only in the serializer, but this is a
        stronger, backend-enforced guarantee.
        """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Can be used to add logic before an update, e.g., preventing edits
        to bookings that are too close to their start time.
        """
        # Example: Prevent changes within 24 hours of the booking
        # booking = self.get_object()
        # if booking.booking_datetime - timezone.now() < timedelta(hours=24):
        #     raise PermissionDenied("Cannot modify a booking less than 24 hours in advance.")
        serializer.save(user=self.request.user)

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']  # disallow PATCH/PUT/DELETE

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)