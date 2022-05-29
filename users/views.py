from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm
from .forms import CreateUserForm,UserUpdateForm,ProfileUpdateForm
from .models import Dataset,Present,User
import calendar
import datetime
from datetime import date, timedelta
# Create your views here.
def register(request):
    if request.method == 'POST':
        form=CreateUserForm(request.POST)
        if form.is_valid():
            user_obj=form.save()
            model=Dataset(user=user_obj)
            model.save()
            return redirect('login')
    else:
        form=CreateUserForm()
    return render(request, 'register.html', {'form':form})

def profile(request):
    staff=request.user
    msg=None
    if not staff.is_superuser:
        msg=[]
        attendance_percentage_week=staff_attendance_percentage_this_week(staff)
        attendance_percentage_month=staff_attendance_percentage_this_month(staff)
        msg1="Your Attendance percentage of this week: {}%".format(attendance_percentage_week)
        msg.append(msg1)
        msg2="Your Attendance percentage of this month: {}%".format(attendance_percentage_month)
        msg.append(msg2)
        # user=User.objects.get(username=staff)
        qs=Dataset.objects.get(user=staff)
        if qs.is_sampleUploaded==False:
            msg.append("Sample not collected")
        else:
            if qs.is_trained==False:
                msg.append("Dataset not trained with staff's sample")
    return render(request,'profile.html',{'message_profile':msg})
def profile_update(request):
    if request.method == "POST":
        user_form=UserUpdateForm(request.POST,instance=request.user)
        profile_form=ProfileUpdateForm(request.POST,request.FILES,instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')
    else:
        user_form=UserUpdateForm(instance=request.user)
        profile_form=ProfileUpdateForm(instance=request.user.profile)
    context={
        'user_form':user_form,
        'profile_form':profile_form
    }
    return render(request,'profile_update.html',context)
def staff_attendance_percentage_this_week(staff):
    today=datetime.date.today()
    some_day_last_week=today-datetime.timedelta(days=7)
    monday_of_last_week=some_day_last_week-  datetime.timedelta(days=(some_day_last_week.isocalendar()[2] - 1))
    first_day = monday_of_last_week + datetime.timedelta(days=7)
    last_day = first_day + datetime.timedelta(days=7)
    qs1=Present.objects.filter(date__gte=first_day).filter(date__lte=last_day).filter(user=staff).filter(present=True)
    qs2=Present.objects.filter(date__gte=first_day).filter(date__lte=last_day).filter(user=staff)
    return(round((len(qs1)/len(qs2))*100,2))
def staff_attendance_percentage_this_month(staff):
    first_day=date.today().replace(day=1)
    current_year=date.today().year
    current_month=date.today().month
    no_of_total_days=calendar.monthrange(current_year,current_month)[1]
    last_day = first_day + datetime.timedelta(days=(no_of_total_days-1))
    qs1=Present.objects.filter(date__gte=first_day).filter(date__lte=last_day).filter(user=staff).filter(present=True)
    qs2=Present.objects.filter(date__gte=first_day).filter(date__lte=last_day).filter(user=staff)
    return(round((len(qs1)/len(qs2))*100,2))