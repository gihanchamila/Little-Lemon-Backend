# bookings/views.py
from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import UserCreationSerializer
from .models import CustomUser

class UserCreateView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserCreationSerializer