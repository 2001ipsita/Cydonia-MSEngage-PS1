# importing required modules
import datetime
import calendar
from datetime import date
import math
import shutil
from PIL import Image
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import os
import cv2
from users.forms import ProfileUpdateForm, UserUpdateForm
import numpy as np
from django.contrib.auth.models import User
from users.models import Present, Time, Dataset
from .forms import DateForm_2, UsernameAndDateForm,DateForm
from json import dumps
# Create your views here.

@login_required
def index(request):    
    user=request.user
    msg=[]
    if not user.is_superuser:
        qs=Dataset.objects.get(user=user)
        if(qs.is_deleted==True):
            qs.is_sampleUploaded=False
            qs.is_trained=False
            qs.save(update_fields=['is_sampleUploaded','is_trained'])
        if qs.is_sampleUploaded==False:
            msg.append('You need to upload and train Sample')
    attendance_week=attendance_this_month()
    attendance=attendance_week[0]
    weeks=attendance_week[1]
    context1=dumps([attendance_week,attendance])
    attendance_this_week=staff_present_this_week()
    present=attendance_this_week[0]
    absent=attendance_this_week[1]
    days_week=attendance_this_week[2]
    context2=dumps([days_week,present,absent])
    return render(request,'index.html',{'attendance':attendance,'weeks':weeks,'present_week':present,'absent_week':absent,'week_days':days_week,'message':msg,'data1':context1,'data2':context2})
@login_required
def staff(request):
    workers=User.objects.all().exclude(is_superuser=True)
    emails=[]
    names=[]
    for worker in workers:
        emails.append(worker.email)
        names.append(worker.username)
    qs=None
    if request.method == 'POST':
        name_email=request.POST['name_email']
        if name_email in names:
            qs=User.objects.get(username=name_email)
            return render(request, 'staff.html',{'qs':qs})
        elif name_email in emails:
            qs=User.objects.get(email=name_email)
            return render(request, 'staff.html',{'qs':qs})
        else:
            if name_email=='':
                return render(request, 'staff.html',{'workers':workers})
            else:
                msg='No Such User Exists'
                return render(request, 'staff.html',{'workers':workers,'message':msg})
        
    else:
        return render(request, 'staff.html',{'workers':workers})
@login_required
def staff_staff(request):
    
    u=User.objects.get(username=request.user.username)
    time_qs=Time.objects.filter(user=u)
    present_qs=Present.objects.filter(user=u)
    date_from=date.today().replace(day=1)
    next_month=date.today().replace(day=28)+datetime.timedelta(days=4)
    date_to=next_month-datetime.timedelta(days=next_month.day)

    time_qs=time_qs.filter(date__gte=date_from).filter(date__lte=date_to).order_by('-date')
    present_qs=present_qs.filter(date__gte=date_from).filter(date__lte=date_to).order_by('-date')
    
    if (len(time_qs)>0 or len(present_qs)>0):
        qs=hours_vs_date_given_employee(present_qs,time_qs)
        return render(request,'staff_staff.html', { 'qs1' :qs})
    else:
        return render(request,'index')
    
@login_required
def view_attendance_admin(request):
    today=datetime.date.today()
    qs=Present.objects.filter(date=today)
    time_qs=Time.objects.filter(date=today)
    for obj in qs:
        user=obj.user
        times_in=time_qs.filter(user=user).filter(out=False)
        times_out=time_qs.filter(user=user).filter(out=True)
        obj.time_in=None
        obj.time_out=None
        obj.hours=0
        if (len(times_in)>0):			
            obj.time_in=times_in.first().time
        if (len(times_out)>0):
            obj.time_out=times_out.last().time
        if(obj.time_in is not None and obj.time_out is not None):
            ti=obj.time_in
            to=obj.time_out
            hours=((to-ti).total_seconds())/3600
            obj.hours=hours
            obj.hours=convert_hours_to_hours_mins(obj.hours)
        else:
            obj.hours=0
    context={'staffs':qs}
    return render(request, 'view_attendance_admin.html',context)

def username_present(username):     #to know if a particular staff is registered or not
	if User.objects.filter(username=username).exists():
		return True
	
	return False

def hours_vs_date_given_employee(present_qs,time_qs): #returns 
    qs=present_qs

    for obj in qs:
        date=obj.date
        times_in=time_qs.filter(date=date).filter(out=False).order_by('time')
        times_out=time_qs.filter(date=date).filter(out=True).order_by('time')
        times_all=time_qs.filter(date=date).order_by('time')
        obj.time_in=None
        obj.time_out=None
        obj.hours=0
        obj.break_hours=0
        if (len(times_in)>0):			
            obj.time_in=times_in.first().time
            
        if (len(times_out)>0):
            obj.time_out=times_out.last().time

        if(obj.time_in is not None and obj.time_out is not None):
            ti=obj.time_in
            to=obj.time_out
            hours=((to-ti).total_seconds())/3600
            obj.hours=hours
        
        else:
            obj.hours=0

        obj.hours=convert_hours_to_hours_mins(obj.hours)
    return qs

@login_required
def attendance_admin_username(request):
    active=None
    if total_no_of_staff_present()>0:
        active=total_no_of_staff_present()
    triggered=True
    time_qs=None
    present_qs=None
    qs=None

    if request.method=='POST':
        form=UsernameAndDateForm(request.POST)
        if form.is_valid():
            username=form.cleaned_data.get('username')
            if username_present(username):
                
                u=User.objects.get(username=username)
                
                time_qs=Time.objects.filter(user=u)
                present_qs=Present.objects.filter(user=u)
                date_from=form.cleaned_data.get('date_from')
                date_to=form.cleaned_data.get('date_to')
                
                if date_to < date_from:
                    msg='Invalid date selection.'
                    return render(request,'view_attendance_admin.html', {'message':msg,'triggered':triggered,'active':active})
                else:
                    

                    time_qs=time_qs.filter(date__gte=date_from).filter(date__lte=date_to).order_by('-date')
                    present_qs=present_qs.filter(date__gte=date_from).filter(date__lte=date_to).order_by('-date')
                    
                    if (len(time_qs)>0 or len(present_qs)>0):
                        qs=hours_vs_date_given_employee(present_qs,time_qs)
                        return render(request,'view_attendance_admin.html', {'form' : form, 'qs' :qs,'triggered':triggered})
                    else:
                        msg='No records for selected duration.'
                        return render(request,'view_attendance_admin.html', {'message':msg,'triggered':triggered,'active':active})

            else:
                print("invalid username")
                msg='No such username found.'
                return render(request,'view_attendance_admin.html', {'message':msg,'triggered':triggered,'active':active})
    else:
        form=UsernameAndDateForm()
        return render(request,'view_attendance_admin.html', {'form' : form, 'qs' :qs,'triggered':triggered})

@login_required
def attendance_admin_date(request):
    triggered=True
    qs=None
    time_qs=None
    present_qs=None
    active=None
    if total_no_of_staff_present()>0:
        active=total_no_of_staff_present()

    if request.method=='POST':
        form=DateForm(request.POST)
        if form.is_valid():
            date=form.cleaned_data.get('date')
            print("date:"+ str(date))
            time_qs=Time.objects.filter(date=date)
            present_qs=Present.objects.filter(date=date)
            if(len(time_qs)>0 or len(present_qs)>0):
                qs=hours_vs_employee_given_date(present_qs,time_qs)
                return render(request,'view_attendance_admin.html', {'form' : form,'qs' : qs,'triggered':triggered })
            else:
                msg='No records for selected date.'
                return render(request,'view_attendance_admin.html', {'message':msg,'triggered':triggered,'active':active})
    else:
        form=DateForm()
        return render(request,'view_attendance_admin.html', {'form' : form, 'qs' : qs,'triggered':triggered})

def hours_vs_employee_given_date(present_qs,time_qs): #returns
    qs=present_qs

    for obj in qs:
        user=obj.user
        times_in=time_qs.filter(user=user).filter(out=False)
        times_out=time_qs.filter(user=user).filter(out=True)
        times_all=time_qs.filter(user=user)
        obj.time_in=None
        obj.time_out=None
        obj.hours=0
        obj.hours=0
        if (len(times_in)>0):			
            obj.time_in=times_in.first().time
        if (len(times_out)>0):
            obj.time_out=times_out.last().time
        if(obj.time_in is not None and obj.time_out is not None):
            ti=obj.time_in
            to=obj.time_out
            hours=((to-ti).total_seconds())/3600
            obj.hours=hours
        else:
            obj.hours=0
        obj.hours=convert_hours_to_hours_mins(obj.hours)
    return qs

    
def convert_hours_to_hours_mins(hours):  #converts hours to hours-mins
	h=int(hours)
	hours-=h
	m=hours*60
	m=math.ceil(m)
	return str(str(h)+ " hrs " + str(m) + "  mins")
@login_required
def add_photo(request):
    attendance_week=attendance_this_month()
    attendance=attendance_week[0]
    weeks=attendance_week[1]
    context1=dumps([attendance_week,attendance])
    attendance_this_week=staff_present_this_week()
    present=attendance_this_week[0]
    absent=attendance_this_week[1]
    days_week=attendance_this_week[2]
    context2=dumps([days_week,present,absent])
    context={'attendance':attendance,'weeks':weeks,'present_week':present,'absent_week':absent,'week_days':days_week,'data1':context1,'data2':context2}
    training_dir='faceRecognition_data/training_dataset'
    Name = request.user.username 
    ID=request.user.id
    user=User.objects.get(username=Name)
    qs=Dataset.objects.get(user=user)
    trained=True
    if(qs.is_sampleUploaded==True):
        messages='Sample photo already uploaded'
        context['messages_']=messages
        context['trained']=trained
        return render(request,'index.html',context)
    else:
        os.makedirs('faceRecognition_data/training_dataset/{}/'.format(Name))
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        
        sampleNum = 0
        while (True):
            ret, img = cam.read()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                # incrementing sample number
                sampleNum = sampleNum + 1
                # saving the captured face in the dataset folder
                cv2.imwrite("faceRecognition_data/training_dataset/" + Name + "/" + str(ID) + "." + str(sampleNum) + ".jpg",
                                    gray[y:y + h, x:x + w])
                winName="Collecting Sample"
                cv2.namedWindow(winName)
                cv2.moveWindow(winName,40,30)
                cv2.imshow(winName, img)
                cv2.setWindowProperty(winName,cv2.WND_PROP_TOPMOST,1)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            elif sampleNum > 200:
                break
        cam.release()
        cv2.destroyAllWindows()
        res = "Images Saved  : " + str(ID) + " Name : " + Name
        qs.is_sampleUploaded=True
        qs.sample=str(ID)
        qs.save(update_fields=['is_sampleUploaded','sample'])
        messages='Dataset Created'
        context['messages_']=messages
        context['trained']=trained
        return render(request,'index.html',context)
@login_required
def train(request):
    return render(request, 'train.html')
@login_required
def train_data(request):
    user=User.objects.get(username=request.user.username)
    qs=Dataset.objects.get(user=user)
    if qs.is_sampleUploaded==False:
        messages.warning(request,"Upload Sample")
        return redirect('index')
    else:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        global detector
        detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        faces, Id = getImagesAndLabels("faceRecognition_data/training_dataset")

        recognizer.train(faces, np.array(Id)) 
        try:
            recognizer.save("model/trained_model2.yml")
        except Exception as e:
            q='Please make "model" folder'
            messages.warning(request,q)
            return redirect('index')
        res = "Model Trained" 
        messages.success(request,res)
        qs.is_trained=True
        qs.save(update_fields=['is_trained'])
        return redirect('index')
    
def getImagesAndLabels(path): #returns images and labels for each user
    faceSamples = []
    Ids = []
    imagePaths=[]
    for dir in os.listdir(path):
        dir_n=os.path.join(path, dir)
        for f in os.listdir(dir_n):
            imagePaths.append(os.path.join(dir_n, f))
    for imagePath in imagePaths:
        pilImage = Image.open(imagePath).convert('L')
        imageNp = np.array(pilImage, 'uint8')
        Id = int(os.path.split(imagePath)[-1].split(".")[0])
        faces = detector.detectMultiScale(imageNp)
        for (x, y, w, h) in faces:
            faceSamples.append(imageNp[y:y + h, x:x + w])
            Ids.append(Id)
    print(Ids)
    return faceSamples, Ids
    
@login_required
def delete_photo(request):
    training_dir='faceRecognition_data/training_dataset'
    Name = request.user.username 
    user=User.objects.get(username=Name)
    qs=Dataset.objects.get(user=user)
    if(qs.is_sampleUploaded==True):
        if(os.path.exists('faceRecognition_data/training_dataset/{}/'.format(Name))==True):
            shutil.rmtree('faceRecognition_data/training_dataset/{}/'.format(Name))
            qs.is_sampleUploaded=False
            qs.is_trained=False
            qs.sample="0"
            qs.save(update_fields=['is_sampleUploaded','sample','is_trained'])
            messages.success(request,"Sample has been deleted")
            return redirect('index')
            
        else:
            qs.is_sampleUploaded=False
            qs.is_trained=False
            qs.sample="0"
            qs.save(update_fields=['is_sampleUploaded','sample','is_trained'])
            
            messages.warning(request,"Sample has already been deleted")
            return redirect('index')
        
    else:
        messages.warning(request,'Sample photo not uploaded yet')
        return redirect('index')

@login_required
def attendance_in(request):
    today=datetime.date.today()
    to_be_excluded=Present.objects.filter(date=today).filter(present=True)
    to_be_excluded_l=[]
    for user in to_be_excluded:
        to_be_excluded_l.append(user.user.username)
    to_be_marked=User.objects.exclude(username__in=to_be_excluded_l).exclude(username='ipsi')
    present={}
    for staffs in to_be_marked:
        present[staffs.username]=False
    no_of_students=len(os.listdir('faceRecognition_data/training_dataset'))
    for i in range(no_of_students):
        present[os.listdir('faceRecognition_data/training_dataset')[i]]=False
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('model/trained_model2.yml')
    cascadePath = "haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascadePath)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cam = cv2.VideoCapture(0,cv2.CAP_DSHOW)
    while True:
        ret, img =cam.read()
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale( 
            gray,
            scaleFactor = 1.1,
            minNeighbors = 10
        )
        for(x,y,w,h) in faces:
            cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
            id, pred = recognizer.predict(gray[y:y+h,x:x+w])
            confidence=int(100*(1-pred/300))
            # If confidence is less them 100 ==> "0" : perfect match 
            if (confidence >77):
                # Idl=Ids
                qs=Dataset.objects.get(sample=str(id))
                id_ = qs.user.username
                confidence = "  {0}%".format(round(100 - confidence))
                present[id_]=True
                
            else:
                id_ = "unknown"
                confidence = "  {0}%".format(round(100 - confidence))
#             font_=''
#             if id_ != "unknown":
#                 font_=id_
            cv2.putText(
                        img, 
                        id_, 
                        (x+5,y-5), 
                        font, 
                        1, 
                        (255,255,255), 
                        2
                    )
            
        winName="Taking Attendance - In"
        cv2.namedWindow(winName)
        cv2.moveWindow(winName,40,30)
        cv2.imshow(winName, img)
        cv2.setWindowProperty(winName,cv2.WND_PROP_TOPMOST,1)
        # cv2.imshow('camera',img) 
        k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
        if k == 27:
            break
    # Do a bit of cleanup
    print("\n [INFO] Exiting Program and cleanup stuff")
    cam.release()
    cv2.destroyAllWindows()
    update_attendance_in_db_in(present)
    return redirect('index')

def update_attendance_in_db_in(present):   #update staff's attendance in database
    today=datetime.date.today()
    time=datetime.datetime.now()
    for person in present:
        user=User.objects.get(username=person)
        try:
            qs=Present.objects.get(user=user,date=today)
        except:
            qs= None
        if qs is None:
            if present[person]==True:
                        a=Present(user=user,date=today,present=True)
                        a.save()
            else:
                a=Present(user=user,date=today,present=False)
                a.save()
        else:
            if present[person]==True:
                qs.present=True
                qs.save(update_fields=['present'])
        if present[person]==True:
            
            if not (Time.objects.filter(user=user).filter(date=today).filter(out=False).exists()):
                
                a=Time(user=user,date=today,time=time, out=False)
                a.save()

def total_no_of_staff_present(): #return the total number of staff present today
    today=datetime.date.today()
    qs=Present.objects.filter(date=today).filter(present=True)
    return len(qs)
    
@login_required
def attendance_out(request):
    present={}
    no_of_students=len(os.listdir('faceRecognition_data/training_dataset'))
    for i in range(no_of_students):
        present[os.listdir('faceRecognition_data/training_dataset')[i]]=False
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('model/trained_model2.yml')
    cascadePath = "haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascadePath)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cam = cv2.VideoCapture(0,cv2.CAP_DSHOW)

    while True:
        ret, img =cam.read()
        #img = cv2.flip(img, -1) # Flip vertically
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale( 
            gray,
            scaleFactor = 1.1,
            minNeighbors = 10
        )
        for(x,y,w,h) in faces:
            cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
            id, pred = recognizer.predict(gray[y:y+h,x:x+w])
            confidence=int(100*(1-pred/300))
            # If confidence is less them 100 ==> "0" : perfect match 
            if (confidence > 77):
                # Idl=Ids
                qs=Dataset.objects.get(sample=str(id))
                id_ = qs.user.username
                confidence = "  {0}%".format(round(100 - confidence))
                present[id_]=True
            
            else:
                id_ = "unknown"
                confidence = "  {0}%".format(round(100 - confidence))
#             font_=''
#             if id_ != "unknown":
#                 font_=id_
            cv2.putText(
                        img, 
                        id_, 
                        (x+5,y-5), 
                        font, 
                        1, 
                        (255,255,255), 
                        2
                    )
        winName="Taking Attendance - Out"
        cv2.namedWindow(winName)
        cv2.moveWindow(winName,40,30)
        cv2.imshow(winName, img)
        cv2.setWindowProperty(winName,cv2.WND_PROP_TOPMOST,1)
        k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
        if k == 27:
            break
    # Do a bit of cleanup
    print("\n [INFO] Exiting Program and cleanup stuff")
    cam.release()
    cv2.destroyAllWindows()
    update_attendance_in_db_out(present)
    return redirect('index')

def update_attendance_in_db_out(present):  #update attenndance-out in database
    today=datetime.date.today()
    time=datetime.datetime.now()
    for person in present:
        user=User.objects.get(username=person)
        if present[person]==True:
            if (Present.objects.filter(user=user).filter(date=today).filter(present=True).exists()) or (Time.objects.filter(user=user).filter(date=today).filter(out=False).exists()):
                if not (Time.objects.filter(user=user).filter(date=today).filter(out=True).exists()):
                    a=Time(user=user,date=today,time=time, out=True)
                    a.save()
      
@login_required
def attendance_delete(request,user,date):
    staff=User.objects.get(username=user)
    delete_item1=Present.objects.filter(user=staff).filter(date=date)
    delete_item2=Time.objects.filter(user=staff).filter(date=date)
    if request.method == 'POST':
        for obj in delete_item1:
            obj.present=False
            obj.save(update_fields=['present'])
        for objs in delete_item2:
            objs.delete()
        return redirect('attendance-admin')
    return render(request,'attendance_delete.html')

@login_required
def staff_profile_view(request,staff):
    msg=[]
    user=User.objects.get(username=staff)
    attendance_percentage_week=staff_attendance_percentage_this_week(user)
    attendance_percentage_month=staff_attendance_percentage_this_month(user)
    msg1="Staff's Attendance percentage of this week: {}%".format(attendance_percentage_week)
    msg.append(msg1)
    msg2="Staff's Attendance percentage of this month: {}%".format(attendance_percentage_month)
    msg.append(msg2)
    
    qs=Dataset.objects.get(user=user)
    if qs.is_sampleUploaded==False:
        msg.append("Sample not collected")
    else:
        if qs.is_trained==False:
            msg.append("Dataset not trained with staff's sample")
    return render(request,'staff_profile.html',{'user':user,'message_profile':msg})
@login_required
def staff_profile_update(request,staff):
    user=User.objects.get(username=staff)
    if request.method == "POST":
        user_form=UserUpdateForm(request.POST,instance=user)
        profile_form=ProfileUpdateForm(request.POST,request.FILES,instance=user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('view-profile',staff)
    else:
        user_form=UserUpdateForm(instance=user)
        profile_form=ProfileUpdateForm(instance=user.profile)
    context={
        'user_form':user_form,
        'profile_form':profile_form
    }
    return render(request,'staff_profile_update.html',context)
@login_required
def staff_profile_delete(request,staff):
    delete_item=User.objects.get(username=staff)
    if request.method == 'POST':
        delete_item.delete()
        return redirect('staff')
    return render(request,'staff_delete.html')

@login_required
def view_attendance_staff(request,staff):
    u=User.objects.get(username=staff)
    time_qs=Time.objects.filter(user=u)
    present_qs=Present.objects.filter(user=u)
    date_from=date.today().replace(day=1)
    next_month=date.today().replace(day=28)+datetime.timedelta(days=4)
    date_to=next_month-datetime.timedelta(days=next_month.day)  
    time_qs=time_qs.filter(date__gte=date_from).filter(date__lte=date_to).order_by('-date')
    present_qs=present_qs.filter(date__gte=date_from).filter(date__lte=date_to).order_by('-date')
    
    if (len(time_qs)>0 or len(present_qs)>0):
        qs=hours_vs_date_given_employee(present_qs,time_qs)
        return render(request,'staff_profile_attendance.html', { 'qs' :qs})
    else:
        #print("inside qs is None")
        msg='No records for selected duration.'
        return render(request,'staff_profile.html', {'user':u,'message':msg})
    
@login_required
def attendance_staff_date(request):
    triggered=True
    qs=None
    time_qs=None
    present_qs=None
    if request.method=='POST':
        form=DateForm_2(request.POST)
        if form.is_valid():
            u=request.user
            time_qs=Time.objects.filter(user=u)
            present_qs=Present.objects.filter(user=u)
            date_from=form.cleaned_data.get('date_from')
            date_to=form.cleaned_data.get('date_to')
            if date_to < date_from:
                    msg='Invalid date selection.'
                    return render(request,'staff_staff.html',{'message':msg,'triggered':triggered})
            else:
                    time_qs=time_qs.filter(date__gte=date_from).filter(date__lte=date_to).order_by('-date')
                    present_qs=present_qs.filter(date__gte=date_from).filter(date__lte=date_to).order_by('-date')
                
                    if (len(time_qs)>0 or len(present_qs)>0):
                        qs=hours_vs_date_given_employee(present_qs,time_qs)
                        return render(request,'staff_staff.html', {'form' : form, 'qs2' :qs,'triggered':triggered})
                    else:
                        
                        msg='No Record for selected Duration.'
                        return render(request,'staff_staff.html',{'message':msg,'triggered':triggered})
    else:
        form=DateForm_2()
        return render(request,'staff_staff.html', {'form' : form, 'qs2' :qs,'triggered':triggered})


def staff_present_this_week(): #returns Number of Staffs Present and Absent on each day of this week
    today=datetime.date.today()
    some_day_last_week=today-datetime.timedelta(days=7)
    monday_of_last_week=some_day_last_week-  datetime.timedelta(days=(some_day_last_week.isocalendar()[2] - 1))
    monday_of_this_week = monday_of_last_week + datetime.timedelta(days=7)
    qs=Present.objects.filter(date__gte=monday_of_this_week).filter(date__lte=today)
    str_dates=[]
    emp_count=[]
    emp_count_ab=[]
    str_dates_all=[]
    emp_cnt_all=[]
    emp_cnt_all_ab=[]
    cnt=0
    noted=[]
    for obj in qs:
        date=obj.date
        if date not in noted:
            str_dates.append(str(date))
            qs1=Present.objects.filter(date=date).filter(present=True)
            qs2=Present.objects.filter(date=date).filter(present=False)
            emp_count.append(len(qs1))
            emp_count_ab.append(len(qs2))
            noted.append(date)
    while(cnt<7):
        date=str(monday_of_this_week+datetime.timedelta(days=cnt))
        cnt+=1
        str_dates_all.append(date)
        if(str_dates.count(date))>0:
            idx=str_dates.index(date)

            emp_cnt_all.append(emp_count[idx])
            emp_cnt_all_ab.append(emp_count_ab[idx])
        else:
            emp_cnt_all.append(0)
            emp_cnt_all_ab.append(0)

    return (emp_cnt_all,emp_cnt_all_ab,str_dates_all)
    
def staff_present_week(first_day): #returns the number of days in a week with high attendance
    last_day = first_day + datetime.timedelta(days=7)
    qs=Present.objects.filter(date__gte=first_day).filter(date__lte=last_day)
    str_dates=[]
    emp_count=[]
    noted=[]
    for obj in qs:
        date=obj.date
        if date not in noted:
            qs1=Present.objects.filter(date=date).filter(present=True)
            qs2=Present.objects.filter(date=date).filter(present=False)
            if len(qs1)>=len(qs2):
                emp_count.append(len(qs1))
                str_dates.append(str(date))
            noted.append(date)
    return len(emp_count)

def day_present_week(first_day,staff):  #returns the number of days present and absent in a week for a particular stuff
    last_day = first_day + datetime.timedelta(days=7)
    qs1=Present.objects.filter(date__gte=first_day).filter(date__lte=last_day).filter(user=staff).filter(present=True)
    qs2=Present.objects.filter(date__gte=first_day).filter(date__lte=last_day).filter(user=staff).filter(present=False)
    return len(qs1),len(qs2)

def attendance_this_month():             #returns the number of days with high attendance in each week of this month
    current_month=date.today().month
    current_year=date.today().year
    d=datetime.datetime(current_year,current_month,28)
    no_of_weeks=(d.day-1)//7+1
    first_day=date.today().replace(day=1)
    present_per_week=[]
    week_list=[]
    cnt=0
    while(cnt<no_of_weeks):
        day=first_day + datetime.timedelta(days=(7*cnt))
        present_per_week.append(staff_present_week(day))
        cnt+=1
        
    for i in range(no_of_weeks):
        num=i+1
        week_list.append('week'+str(num))
    return (present_per_week,week_list)       

def attendance_this_month_user(staff):   #for each week in present month, returns the number of days present and absent for a staff
    current_month=date.today().month
    current_year=date.today().year
    d=datetime.datetime(current_year,current_month,28)
    no_of_weeks=(d.day-1)//7+1
    first_day=date.today().replace(day=1)
    present_per_week=[]
    absent_per_week=[]
    week_list=[]
    cnt=0
    while(cnt<no_of_weeks):
        day=first_day + datetime.timedelta(days=(7*cnt))
        present_absent=day_present_week(day,staff)
        present_per_week.append(present_absent[0])
        absent_per_week.append(present_absent[1])
        cnt+=1
    for i in range(no_of_weeks):
        num=i+1
        week_list.append('week'+str(num))
    return (present_per_week,absent_per_week,week_list)

def attendance_any_month_user(date,staff):   #for each week in a selected month, returns the number of days present and absent for a staff
    current_month=date.month
    current_year=date.year
    d=datetime.datetime(current_year,current_month,28)
    no_of_weeks=(d.day-1)//7+1
    first_day=date.replace(day=1)
    present_per_week=[]
    absent_per_week=[]
    week_list=[]
    cnt=0
    while(cnt<no_of_weeks):
        day=first_day + datetime.timedelta(days=(7*cnt))
        present_absent=day_present_week(day,staff)
        present_per_week.append(present_absent[0])
        absent_per_week.append(present_absent[1])
        cnt+=1
    for i in range(no_of_weeks):
        num=i+1
        week_list.append('week'+str(num))
    return (present_per_week,absent_per_week,week_list)
        
@login_required
def attendance_month_user(request):
    u=request.user
    if request.method=="POST":
        form=DateForm(request.POST)
        if form.is_valid():
            
            date=form.cleaned_data.get('date')
            attendance_weeks=attendance_any_month_user(date,u)
            present_any=attendance_weeks[0]
            absent_any=attendance_weeks[1]
            weeks_any=attendance_weeks[2]
            context1={'present_any':present_any,'absent_any':absent_any,'weeks_any':weeks_any}
            contextjson1=dumps([present_any,absent_any,weeks_any])
            return render(request,'staff_attendance_chart.html',{'data1_':context1,'data1':contextjson1,'form':form})
    else:
        form=DateForm()
        attendance_weeks_this=attendance_this_month_user(u)
        present=attendance_weeks_this[0]
        absent=attendance_weeks_this[1]
        weeks_this=attendance_weeks_this[2]
        context2={'present':present,'absent':absent,'weeks':weeks_this}
        contextjson2=dumps([present,absent,weeks_this])
        return render(request,'staff_attendance_chart.html',{'data2_':context2,'data2':contextjson2,'form':form})

def staff_attendance_percentage_this_week(staff):   #give attendance percentage of a staff in present week
    today=datetime.date.today()
    some_day_last_week=today-datetime.timedelta(days=7)
    monday_of_last_week=some_day_last_week-  datetime.timedelta(days=(some_day_last_week.isocalendar()[2] - 1))
    first_day = monday_of_last_week + datetime.timedelta(days=7)
    last_day = first_day + datetime.timedelta(days=7)
    qs1=Present.objects.filter(date__gte=first_day).filter(date__lte=last_day).filter(user=staff).filter(present=True)
    qs2=Present.objects.filter(date__gte=first_day).filter(date__lte=last_day).filter(user=staff)
    if len(qs2)==0:
        return 0
    else:
	return(round((len(qs1)/len(qs2))*100,2))
def staff_attendance_percentage_this_month(staff):    #give attendance percentage of a staff in present week
    first_day=date.today().replace(day=1)
    current_year=date.today().year
    current_month=date.today().month
    no_of_total_days=calendar.monthrange(current_year,current_month)[1]
    last_day = first_day + datetime.timedelta(days=(no_of_total_days-1))
    qs1=Present.objects.filter(date__gte=first_day).filter(date__lte=last_day).filter(user=staff).filter(present=True)
    qs2=Present.objects.filter(date__gte=first_day).filter(date__lte=last_day).filter(user=staff)
    if len(qs2)==0:
        return 0
    else:
	return(round((len(qs1)/len(qs2))*100,2))
    
