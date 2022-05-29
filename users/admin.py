from django.contrib import admin
from .models import Profile, Time,Present,Dataset

# Register your models here.
admin.site.register(Time)
admin.site.register(Present)
admin.site.register(Profile)
admin.site.register(Dataset)