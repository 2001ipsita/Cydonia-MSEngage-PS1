from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [

    path('index/',views.index, name='index'),
    path('staff/',views.staff,name='staff'),
    path('staff-staff/',views.staff_staff,name='staff-staff'),
    path('attendance-admin/',views.view_attendance_admin,name='attendance-admin'),
    path('attendance-admin-username/',views.attendance_admin_username,name='attendance-admin-username'),
    path('attendance-admin-date/',views.attendance_admin_date,name='attendance-admin-date'),
    path('view-staff/<str:staff>/',views.staff_profile_view,name='view-profile'),
    path('view-attendance/<str:staff>/',views.view_attendance_staff,name='view-attendance'),
    path('update-staff/<str:staff>/',views.staff_profile_update,name='profile-update-admin'),
    path('delete-staff/<str:staff>/',views.staff_profile_delete,name='delete-profile'),
    path('attendance-delete/<str:user>/<str:date>/',views.attendance_delete,name='attendance-delete'),
    path('add-photo/',views.add_photo,name='add-photo'),
    path('delete-photo/',views.delete_photo,name='delete-photo'),
    path('train/',views.train,name='train'),
    path('train-data/',views.train_data,name='train-data'),
    path('attendance-in/',views.attendance_in,name='attendance-in'),
    path('attendance-out/',views.attendance_out,name='attendance-out'),
    path('attendance-staff-date/',views.attendance_staff_date,name='attendance-staff-date'),
    path('view-month-chart/',views.attendance_month_user,name='view-month-chart'),
    
    
]