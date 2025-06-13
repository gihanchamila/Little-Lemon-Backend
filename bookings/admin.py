from django.contrib import admin
from .models import CustomUser, Occasion, SeatingType, Booking, Payment, TimeSlot

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Occasion)
admin.site.register(SeatingType)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(TimeSlot)