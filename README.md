# Cydonia-Smart Attendance
---
**Cydonia** is an online attendance management system for office staffs using Face Recognition.

## [See the video demo here](https://youtu.be/idAOdibLhJE)

# Tech Stack:
---
**1. Backend:** Python Django's Web Framework.

**2. Frontend:** HTML, CSS, Bootstrap, Javascript, chartJs.

**3. Face Recognition:** openCV and its LBPHFaceRecognizer.

**4. Face Detection:** openCV and its Haar Cascades.

**5. Database:** Django Administration Database

---
# How to run this project?
---
**Step1:** 
---
clone this repository or download the zip file and unzip it in a folder(make that folder manually beforehand in your system in any preferable location) in your system and open that folder in your preferable code editor.

**Step2:** 
---
create a separate [python's virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/) in that folder and activate it.

**Step3:** 
---
install packages using **``` pip install package-name ```**

replace the **package name** by **Django**, **opencv-contrib-python**, **numpy**, **django-crispy-forms**, **pillow** .

Also, make sure you are using **python version 3.10 or onwards.**

**Step4:** 
---
make a folder named **faceRecognition_data** in the project directory and inside that make a folder named **training_dataset**. If you already find a folder named **faceRecognition_data** inside the folder downloaded from github, then just make a folder named **training_dataset** inside it.

**Step5:** 
---
run **``` cd faceRecognition_project ```** . Replace **faceRecognition_project** by the **name of the folder which was downloaded from github repo inside the folder you manually made.** 

run **``` python manage.py createsuperuser ```** and give username and password. (You will need this username and password to login as an admin)

run  **``` python manage.py makemigrations ```** and then  **``` python manage.py migrate ```**

**Step6:** 
---
inside **settings.py** of **faceRecognition_project** folder, change **EMAIL_HOST_USER** and **EMAIL_HOST_PASSWORD** by a existing email account and password of yours.

**Step7:** 
---

Finally run   **``` python manage.py runserver ```** to see your website live on your default browser.





