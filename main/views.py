from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Prefetch
import requests
from datetime import timedelta
from django.db import transaction
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.contrib import messages
from django.http import JsonResponse  
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from django.db.models import Max
from django.utils import timezone
from django.db import IntegrityError
from .models import Login, TrainerCategory, Trainer, Session,Customer,Payment,Assessment,Booking,Record,Exercise,WorkoutPlan, ExerciseWeight,Diet,DailyIntake
from datetime import date
import logging
import json
import random
from django.conf import settings
import re  
from django.http import HttpResponse
from django.template.loader import render_to_string
import pdfkit
from django.template.loader import get_template
from xhtml2pdf import pisa

#Stand Alone Pages
def Home(request):
    storage = messages.get_messages(request)
    storage.used = True  # Marks messages as "read" so they don’t persist
    return render(request, 'index.html')
def CheckAvailability(request):
    value = request.GET.get("value")
    check_type = request.GET.get("type")

    if check_type == "email":
        exists = Customer.objects.filter(customer_email=value).exists()
    elif check_type == "username":
        exists = Login.objects.filter(username=value).exists()
    else:
        return JsonResponse({"error": "Invalid request"}, status=400)

    return JsonResponse({"exists": exists})

def Register(request):
    categories = TrainerCategory.objects.all()

    if request.method == "POST":
        customer_name = request.POST.get("customer_name")
        customer_email = request.POST.get("customer_email")
        customer_phone = request.POST.get("customer_phone")
        username = request.POST.get("username")
        password = request.POST.get("password")
        cat_id = request.POST.get("cat_id")  # Selected category ID

        # ✅ Check if email or username already exists
        if Customer.objects.filter(customer_email=customer_email).exists():
            messages.error(request, "Email already registered. Please use a different email.")
            return redirect("/Home/Register")

        if Login.objects.filter(username=username).exists():
            messages.error(request, "Username already taken. Please choose another username.")
            return redirect("/Home/Register")

        category = TrainerCategory.objects.get(cat_id=cat_id)
        category_payment = category.category_payment

        # Generate `customer_id` (CT01, CT02, ...)
        last_customer = Customer.objects.order_by('-customer_id').first()
        new_id = f"CT{(int(last_customer.customer_id[2:]) + 1):02d}" if last_customer else "CT01"

        # Store session data before redirecting to payment
        request.session['customer_data'] = {
            "customer_id": new_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "username": username,
            "password": password,
            "cat_id": cat_id,
            "amount": category_payment,
        }

        return redirect(f"/Home/Payment/?cust_id={new_id}&amount={category_payment}")

    return render(request, "register.html", {"categories": categories})

def Topup(request):
    # Fetch the logged-in customer's details
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "You must be logged in to access this page.")
        return redirect('/Home/Login/')

    customer = Customer.objects.get(customer_id=customer_id)
    categories = TrainerCategory.objects.all()  # Fetch available categories

    if request.method == "POST":
        # Retrieve form data
        customer_name = request.POST.get("customer_name")
        customer_email = request.POST.get("customer_email")
        customer_phone = request.POST.get("customer_phone")
        card_name = request.POST.get("card_name")
        card_number = request.POST.get("card_number")
        card_expiry = request.POST.get("card_expiry")
        cat_id = request.POST.get("cat_id")  # Selected category ID

        # Fetch the selected category and its payment amount
        category = TrainerCategory.objects.get(cat_id=cat_id)
        category_payment = category.category_payment

        # Update customer details
        customer.customer_name = customer_name
        customer.customer_email = customer_email
        customer.customer_phone = customer_phone
        customer.card_name = card_name
        customer.card_number = card_number
        customer.card_expiry = card_expiry
        customer.cat_id = category
        customer.last_payment_date = date.today()
        customer.save()

        # Create a new payment record
        # Get the last payment ID (if any) and increment the number part
        last_payment = Payment.objects.aggregate(Max('payment_id'))
        last_payment_id = last_payment['payment_id__max']

        if last_payment_id:
            # Extract the numeric part from the last payment ID (e.g., PM01 -> 01)
            last_number = int(last_payment_id[2:])
            new_payment_id = f"PM{last_number + 1:02d}"  # Increment and format with leading zero
        else:
            new_payment_id = "PM01"  # If no payment exists yet, start from PM01

        # Save to `tbl_payment`
        Payment.objects.create(
            payment_id=new_payment_id,  # Generates payment ID (PM01, PM02)
            customer_id=customer,  # Reference to the customer
            payment_date=date.today(),
            amount=category_payment,
        )


        # ✅ Redirect to the bill page with the new payment ID
        return redirect(f"/Home/Bill/?payment_id={new_payment_id}")

    return render(request, "topup.html", {
        "customer": customer,
        "categories": categories,
    })

def Payment_Page(request):
    if request.method == "POST":
        # Retrieve session data
        customer_data = request.session.get("customer_data")
        if not customer_data:
            return redirect("/Home/Register/")

        cust_id = customer_data["customer_id"]
        cat_id = customer_data["cat_id"]
        customer_name = customer_data["customer_name"]
        customer_email = customer_data["customer_email"]
        customer_phone = customer_data["customer_phone"]
        username = customer_data["username"]
        password = customer_data["password"]
        amount = customer_data["amount"]

        card_name = request.POST.get("card_name")
        card_number = request.POST.get("card_number")
        card_expiry = request.POST.get("card_expiry")

        # Save to `tbl_customer`
        customer = Customer.objects.create(
            customer_id=cust_id,  # ✅ Now correctly stored as CharField
            cat_id=TrainerCategory.objects.get(cat_id=cat_id),
            customer_email=customer_email,
            customer_phone=customer_phone,
            customer_name=customer_name,
            card_name=card_name,
            card_number=card_number,
            card_expiry=card_expiry,
            last_payment_date=date.today(),
        )

        # Save to `tbl_login`
        Login.objects.create(
            login_id=cust_id,  # ✅ Now matches CharField
            username=username,
            password=password,
            user_type="Customer",
            status=True,
        )

        # Create a new payment record
        # Get the last payment ID (if any) and increment the number part
        last_payment = Payment.objects.aggregate(Max('payment_id'))
        last_payment_id = last_payment['payment_id__max']

        if last_payment_id:
            # Extract the numeric part from the last payment ID (e.g., PM01 -> 01)
            last_number = int(last_payment_id[2:])
            new_payment_id = f"PM{last_number + 1:02d}"  # Increment and format with leading zero
        else:
            new_payment_id = "PM01"  # If no payment exists yet, start from PM01

        # Save to `tbl_payment`
        Payment.objects.create(
            payment_id=new_payment_id,  # Generates payment ID (PM01, PM02)
            customer_id=customer,  # ✅ Correct reference to CharField-based `customer_id`
            payment_date=date.today(),
            amount=amount,
        )


        # ✅ Redirect to the bill page with the payment ID
        return redirect(f"/Home/Bill/?payment_id={new_payment_id}")

    cust_id = request.GET.get("cust_id")
    amount = request.GET.get("amount")
    return render(request, "payment.html", {"cust_id": cust_id, "amount": amount})

def Bill_Page(request):
    payment_id = request.GET.get("payment_id")
    
    if not payment_id:
        return redirect("/Home/")

    payment = Payment.objects.get(payment_id=payment_id)
    customer = payment.customer_id  # Reference to Customer object
    category = TrainerCategory.objects.get(cat_id=customer.cat_id.cat_id)

    context = {
       "customer": customer,
            "payment": payment,
            "category" : category,
            "date": date.today(),
    }
    
    return render(request, "bill.html", context)

# ✅ Function to generate and download bill as PDF
def Download_Bill(request, payment_id):
    payment = Payment.objects.get(payment_id=payment_id)
    customer = payment.customer_id
    category = TrainerCategory.objects.get(cat_id=customer.cat_id.cat_id) 

    context = {
       "payment": payment,
            "customer": customer,
            "category": category,  # ✅ Now included
            "date": date.today(),
    }

    # ✅ Convert bill HTML to string
    html_string = render_to_string("bill.html", context)

    # ✅ Convert HTML to PDF
    pdf = pdfkit.from_string(html_string, False)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Bill_{payment_id}.pdf"'

    return response

#login page
def Login_Page(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            cursor.execute("SELECT login_id, username, password, user_type, status FROM tbl_login WHERE username = %s", [username])
            user = cursor.fetchone()

        if not user:
            messages.error(request, "No user found.")
            return redirect('/Home/Login/')

        login_id, db_username, db_password, user_type, status = user

        if password != db_password:
            messages.error(request, "Username and password do not match.")
            return redirect('/Home/Login/')

        if status == 0:
            messages.error(request, "No user found.")
            return redirect('/Home/Login/')

        # Save session data
        request.session['login_id'] = login_id
        request.session['username'] = db_username
        request.session['user_type'] = user_type  
        
        if user_type == "Customer":
            request.session['customer_id'] = login_id  # `login_id` is `customer_id`

            # ✅ Check Last Payment Date from `tbl_customer`
            with connection.cursor() as cursor:
                cursor.execute("SELECT last_payment_date FROM tbl_customer WHERE customer_id = %s", [login_id])
                last_payment = cursor.fetchone()

            if last_payment and last_payment[0]:  # Ensure a valid date exists
                last_payment_date = last_payment[0]
                days_since_payment = (datetime.today().date() - last_payment_date).days

                if days_since_payment > 30:
                    return redirect('/Home/Topup/')  # 🚀 Redirect if > 30 days

        request.session.modified = True  # Ensure session is updated

        # Redirect based on user type
        if user_type == "Admin":
            return redirect('/Admin/Dashboard/')
        elif user_type == "Trainer":
            return redirect('/Trainer/Dashboard/')
        elif user_type == "Customer":
            return redirect('/Cust/Dashboard/')
        else:
            messages.error(request, "Invalid user type.")
            return redirect('/Home/Login/')

    return render(request, 'login.html')


def Forgot_Password(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # Retrieve the username from the form
        new_password = request.POST.get('new-password')  # Retrieve the new password
        confirm_password = request.POST.get('confirm-password')  # Retrieve the confirm password
        
        try:
            user = Login.objects.get(username=username)  # Look for the user in the login table
            if new_password == confirm_password:  # Ensure the passwords match
                user.password = new_password  # Update the user's password
                user.save()  # Save the user with the updated password
                messages.success(request, "Password reset successful.")  # Show success message
                return redirect('Login')  # Corrected URL name
            else:
                messages.error(request, "Passwords do not match.")  # Show error message if passwords don't match
        except Login.DoesNotExist:
            messages.error(request, "User with this username does not exist.")  # Show error message if username is not found
    
    return render(request, 'forgot_password.html')

def Logout(request):    
    return render(request, 'logout.html')


#Admin pages
def AD_Dashboard(request):
    return render(request, 'ad_dashboard.html')
def Generate_Report(request):
    report_type = request.GET.get('reportType', 'customer')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    category_id = request.GET.get('category')
    customer_id = request.GET.get('customer')
    trainer_id = request.GET.get('trainer')

    report_data = Customer.objects.none()
    categories = TrainerCategory.objects.all()
    customers = Customer.objects.all()
    trainers = Trainer.objects.all()

    if report_type == 'payments_by_customer' and customer_id:
        report_data = Payment.objects.filter(customer_id=customer_id)
    elif report_type == 'customers_by_category' and category_id:
        report_data = Customer.objects.filter(cat_id=category_id)
    elif report_type == 'customers_by_date':
        report_data = Customer.objects.all()  # Start with all customers
    elif report_type == 'booking_customer' and customer_id:
        report_data = Booking.objects.filter(customer_id=customer_id)
    elif report_type == 'booking_trainer' and trainer_id:
        report_data = Booking.objects.filter(session_id__trainer_id=trainer_id)

    # Apply date filters for customers_by_date
    if report_type == 'customers_by_date':
        if start_date and end_date:
            report_data = report_data.filter(join_date__range=[start_date, end_date])
        elif start_date:
            report_data = report_data.filter(join_date__gte=start_date)
        elif end_date:
            report_data = report_data.filter(join_date__lte=end_date)
    # Apply other date filters
    elif start_date or end_date:
        date_field = 'payment_date' if report_type.startswith('payments') else \
                   'booking_date' if report_type.startswith('booking') else None
        if date_field:
            if start_date and end_date:
                report_data = report_data.filter(**{f"{date_field}__range": [start_date, end_date]})
            elif start_date:
                report_data = report_data.filter(**{f"{date_field}__gte": start_date})
            elif end_date:
                report_data = report_data.filter(**{f"{date_field}__lte": end_date})

    context = {
        'report_type': report_type,
        'data': report_data,
        'categories': categories,
        'customers': customers,
        'trainers': trainers,
        'date': date.today(),
    }
    
    return render(request, 'ad_report.html', context)

def Print_report(request):
    report_type = request.GET.get('reportType', 'all_customers')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')
    category_id = request.GET.get('category')
    customer_id = request.GET.get('customer')
    trainer_id = request.GET.get('trainer')

    report_data = []

    if report_type == 'all_customers':
        report_data = Customer.objects.all()
    elif report_type == 'active_customers':
        report_data = Customer.objects.filter(customer_status=True)
    elif report_type == 'inactive_customers':
        report_data = Customer.objects.filter(customer_status=False)
    elif report_type == 'customers_by_category' and category_id:
        report_data = Customer.objects.filter(cat_id=category_id)
    elif report_type == 'customers_by_date':
        report_data = Customer.objects.all()
    elif report_type == 'all_trainers':
        report_data = Trainer.objects.all()
    elif report_type == 'active_trainers':
        report_data = Trainer.objects.filter(trainer_status=True)  # Fixed to use trainer_status
    elif report_type == 'inactive_trainers':
        report_data = Trainer.objects.filter(trainer_status=False)
    elif report_type == 'trainers_by_category' and category_id:
        report_data = Trainer.objects.filter(cat_id=category_id)  # Fixed field name
    elif report_type == 'all_payments':
        report_data = Payment.objects.all()
    elif report_type == 'payments_by_customer' and customer_id:
        report_data = Payment.objects.filter(customer_id=customer_id)
    elif report_type == 'all_assessments':
        report_data = Assessment.objects.all()
    elif report_type == 'booking_all':
        report_data = Booking.objects.all()
    elif report_type == 'booking_customer' and customer_id:
        report_data = Booking.objects.filter(customer_id=customer_id)
    elif report_type == 'booking_trainer' and trainer_id:
        report_data = Booking.objects.filter(session_id__trainer_id=trainer_id)

    # Apply date filters for customers_by_date
    if report_type == 'customers_by_date':
        if start_date and end_date:
            report_data = report_data.filter(join_date__range=[start_date, end_date])
        elif start_date:
            report_data = report_data.filter(join_date__gte=start_date)
        elif end_date:
            report_data = report_data.filter(join_date__lte=end_date)
    # Apply other date filters
    elif start_date or end_date:
        date_field = 'join_date' if report_type in ['all_customers', 'active_customers', 'inactive_customers', 'customers_by_category'] else \
                   'payment_date' if report_type in ['all_payments', 'payments_by_customer'] else \
                   'date' if report_type == 'all_assessments' else \
                   'booking_date' if report_type.startswith('booking') else None
        
        if date_field:
            if start_date and end_date:
                report_data = report_data.filter(**{f"{date_field}__range": [start_date, end_date]})
            elif start_date:
                report_data = report_data.filter(**{f"{date_field}__gte": start_date})
            elif end_date:
                report_data = report_data.filter(**{f"{date_field}__lte": end_date})

    context = {
        'report_type': report_type,
        'data': report_data,
        'date': date.today(),
        'customer_reports': ['all_customers', 'active_customers', 'inactive_customers', 'customers_by_category', 'customers_by_date'],
        'trainer_reports': ['all_trainers', 'active_trainers', 'inactive_trainers','trainers_by_category'],
        'payment_reports': ['all_payments', 'payments_by_date', 'payments_by_customer'],
        'assessment_reports': ['all_assessments', 'assessments_by_customer', 'fitness_progress'],
        'booking_reports': ['booking_all', 'booking_customer', 'booking_trainer'],
    }

    return render(request, 'report_template.html', context)
#report generation stop
def AD_Trainer_cat(request):
    if request.method == "POST":
        cat_id = request.POST.get("catId")
        category_name = request.POST.get("categoryName")
        category_desc = request.POST.get("categoryDesc")
        category_payment = request.POST.get("categoryPayment")  # ✅ Fetch category_payment
        delete_cat_id = request.POST.get("deleteCatId")

        # Handle Deletion
        if delete_cat_id:
            TrainerCategory.objects.filter(cat_id=delete_cat_id).delete()
            return JsonResponse({"status": "deleted"})

        # Handle Update
        if cat_id:
            TrainerCategory.objects.filter(cat_id=cat_id).update(
                category_name=category_name,
                category_desc=category_desc,
                category_payment=category_payment  # ✅ Update category_payment
            )
            return JsonResponse({"status": "updated", "cat_id": cat_id})

        # Fetch latest cat_id, ensuring numeric sorting
        last_entry = TrainerCategory.objects.all()
        last_id = 0
        for entry in last_entry:
            match = re.match(r'TC(\d+)', entry.cat_id)  # Extract numeric part
            if match:
                num = int(match.group(1))
                if num > last_id:
                    last_id = num

        new_id = f"TC{last_id + 1:02d}"

        # Save new category
        TrainerCategory.objects.create(
            cat_id=new_id,
            category_name=category_name,
            category_desc=category_desc,
            category_payment=category_payment  # ✅ Save category_payment
        )
        return JsonResponse({"status": "success", "cat_id": new_id})

    # Fetch existing categories
    categories = TrainerCategory.objects.all()
    return render(request, 'ad_trainer_cat.html', {"categories": categories})
def AD_Bills(request):
    payments = Payment.objects.select_related("customer_id").order_by("-payment_date")

    return render(request, "ad_bills.html", {"payments": payments})

def AD_Bill_Page(request):
    payment_id = request.GET.get("payment_id")
    
    if not payment_id:
        return redirect("/Home/")

    payment = Payment.objects.get(payment_id=payment_id)
    customer = payment.customer_id  # Reference to Customer object
    category = TrainerCategory.objects.get(cat_id=customer.cat_id.cat_id)

    context = {
       "customer": customer,
            "payment": payment,
            "category" : category,
            "date": payment.payment_date,

    }
    
    return render(request, "common_bill.html", context)

# ✅ Function to generate and download bill as PDF
def AD_Download_Bill(request, payment_id):
    payment = Payment.objects.get(payment_id=payment_id)
    customer = payment.customer_id
    category = TrainerCategory.objects.get(cat_id=customer.cat_id.cat_id) 

    context = {
       "payment": payment,
            "customer": customer,
            "category": category,  # ✅ Now included
            "date": payment.payment_date,

    }

    # ✅ Convert bill HTML to string
    html_string = render_to_string("common_bill.html", context)

    # ✅ Convert HTML to PDF
    pdf = pdfkit.from_string(html_string, False)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Bill_{payment_id}.pdf"'

    return response


def GetTrainerDetails(request):
    trainer_id = request.GET.get("trainer_id")
    try:
        trainer = Trainer.objects.get(trainer_id=trainer_id)
        login_data = Login.objects.get(login_id=trainer_id)  # Fetch username & password from tbl_login
        
        return JsonResponse({
            "status": "success",
            "trainer": {
                "trainer_id": trainer.trainer_id,
                "trainer_name": trainer.trainer_name,
                "trainer_age": trainer.trainer_age,
                "trainer_email": trainer.trainer_email,
                "trainer_expertise": trainer.trainer_expertise,
                "cat_id": trainer.cat_id.cat_id,
                "username": login_data.username,
                "password": login_data.password  # Plaintext password (not recommended for production)
            }
        })
    except Trainer.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Trainer not found"})
    except Login.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Login details not found"})



def AD_Trainer(request):
    trainers = Trainer.objects.select_related('cat_id').all()  # Fetch all trainers with categories
    categories = TrainerCategory.objects.all()  # Fetch all categories for dropdown

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            trainer_name = request.POST.get("trainerName")
            trainer_age = request.POST.get("trainerAge")
            trainer_email = request.POST.get("trainerEmail")
            trainer_expertise = request.POST.get("trainerExpertise")
            cat_id = request.POST.get("catId")  
            username = request.POST.get("username")
            password = request.POST.get("password")
            
            if Trainer.objects.filter(trainer_email=trainer_email).exists():
                messages.error(request, "Email already taken. Please choose another email")
                return redirect("/Admin/Trainer")
            
            if Login.objects.filter(username=username).exists():
                messages.error(request, "Username already taken. Please choose another username")
                return redirect("/Admin/Trainer")

            # Generate `trainer_id` (TR01, TR02, ...)
            last_trainer = Trainer.objects.order_by('-trainer_id').first()
            if last_trainer:
                last_id = int(re.search(r'\d+', last_trainer.trainer_id).group())
                new_id = f"TR{last_id + 1:02d}"
            else:
                new_id = "TR01"

            # Fetch Category
            category = TrainerCategory.objects.get(cat_id=cat_id)

            # Save to `tbl_trainer`
            Trainer.objects.create(
                trainer_id=new_id,
                cat_id=category,  
                trainer_name=trainer_name,
                trainer_age=trainer_age,
                trainer_email=trainer_email,
                trainer_expertise=trainer_expertise,
                trainer_status=True  
            )

            try:
                # Save to `tbl_login`
                Login.objects.create(
                    login_id=new_id,
                    username=username,
                    password=password,
                    user_type="Trainer",
                    status=True  
                )
            except IntegrityError:
                return JsonResponse({"status": "error", "message": "Username already exists"})

        elif action == "edit":
            trainer_id = request.POST.get("trainerId")
            trainer = Trainer.objects.get(trainer_id=trainer_id)
            login = Login.objects.get(login_id=trainer_id)  # Get login details

            # Update Trainer Details
            trainer.trainer_name = request.POST.get("trainerName")
            trainer.trainer_age = request.POST.get("trainerAge")
            trainer.trainer_email = request.POST.get("trainerEmail")
            trainer.trainer_expertise = request.POST.get("trainerExpertise")
            trainer.cat_id = TrainerCategory.objects.get(cat_id=request.POST.get("catId"))
            trainer.save()

            # Update Username & Password
            new_username = request.POST.get("username")
            new_password = request.POST.get("password")

            if login.username != new_username:
                if Login.objects.filter(username=new_username).exists():
                    return JsonResponse({"status": "error", "message": "Username already exists"})
                login.username = new_username

            login.password = new_password  # WARNING: Storing plaintext passwords is insecure
            login.save()

            return render(request, "ad_trainer.html", {"trainers": trainers, "categories": categories})

        elif action == "toggle_status":
            trainer_id = request.POST.get("trainerId")
            trainer = Trainer.objects.get(trainer_id=trainer_id)
            trainer.trainer_status = not trainer.trainer_status
            trainer.save()

            # Update status in `tbl_login`
            Login.objects.filter(login_id=trainer_id).update(status=trainer.trainer_status)

    return render(request, "ad_trainer.html", {"trainers": trainers, "categories": categories})


def AD_Exercise(request):
    """Handles exercise management for admins."""
    
    if 'login_id' not in request.session or request.session.get('user_type') != "Admin":
        return redirect('/Home/Login/')

    # Fetch all exercises with trainer info
    exercises = Exercise.objects.select_related('trainer').all().order_by('exercise_id')
    
    return render(request, 'ad_exercise.html', {
        "exercises": exercises,
        "admin_id": request.session.get('login_id')  # optional if needed for admin checks
    })
    
def AD_Session(request):
    trainers = Trainer.objects.select_related('cat_id').all()
    return render(request, 'ad_session.html', {'trainers': trainers})
def GetTrainerSessions(request):
    trainer_id = request.GET.get('trainer_id')

    if trainer_id:
        sessions = Session.objects.filter(trainer_id=trainer_id).select_related('trainer_id')
        session_data = [
            {
                "session_id": session.session_id,
                "trainer_name": session.trainer_id.trainer_name,
                "time_slot": session.time_slot.strftime('%H:%M'),
                "session_status": session.session_status
            }
            for session in sessions
        ]
        return JsonResponse({"sessions": session_data})
    
    return JsonResponse({"error": "Trainer ID not provided"}, status=400)

def AD_Customer(request):
    customers = Customer.objects.select_related('cat_id').all()  # Fetch all customers with category names

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "toggle_status":
            customer_id = request.POST.get("customer_id")

            try:
                # Toggle status in tbl_customer
                customer = Customer.objects.get(customer_id=customer_id)
                customer.customer_status = not customer.customer_status
                customer.save()

                # Update status in tbl_login
                Login.objects.filter(login_id=customer_id).update(status=customer.customer_status)

                return JsonResponse({"status": "updated", "customer_status": customer.customer_status})
            except Customer.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Customer not found"}, status=404)

    return render(request, 'ad_customer.html', {"customers": customers})


    
def AD_Assessment(request):
    customers = Customer.objects.filter(customer_status=True)

    if request.method == "POST":
        customer_id = request.POST.get("customer_id")
        height = request.POST.get("height")
        weight = request.POST.get("weight")
        muscle_mass = request.POST.get("muscle_mass")
        fat_mass = request.POST.get("fat_mass")

        # Generate `assessment_id` (AS01, AS02, ...)
        last_assessment = Assessment.objects.order_by("-assessment_id").first()
        if last_assessment:
            last_id = int(re.search(r'\d+', last_assessment.assessment_id).group())
            new_id = f"AS{last_id + 1:02d}"
        else:
            new_id = "AS01"

        # Get Customer Object
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return JsonResponse({"error": "Customer not found"}, status=400)

        # Insert into `tbl_assessment`
        Assessment.objects.create(
            assessment_id=new_id,
            customer_id=customer,
            height=height,
            weight=weight,
            muscle_mass=muscle_mass,
            fat_mass=fat_mass,
            date=date.today()
        )

        return JsonResponse({"status": "success", "assessment_id": new_id})

    return render(request, "ad_assessment.html", {"customers": customers})

def GetLastAssessment(request):
    customer_id = request.GET.get("customer_id")
    last_assessment = Assessment.objects.filter(customer_id=customer_id).order_by("-date").first()

    if last_assessment:
        return JsonResponse({
            "assessment_id": last_assessment.assessment_id,  # ✅ Include assessment ID
            "height": last_assessment.height,
            "weight": last_assessment.weight,
            "muscle_mass": last_assessment.muscle_mass,
            "fat_mass": last_assessment.fat_mass,
            "date": last_assessment.date.strftime('%Y-%m-%d')
        })
    return JsonResponse({"error": "No assessment found"}, status=400)
def EditAssessment(request):
    if request.method == "POST":
        assessment_id = request.POST.get("assessment_id")

        if not assessment_id:
            return JsonResponse({"error": "Missing assessment ID"}, status=400)  # ✅ Handle missing ID

        try:
            assessment = Assessment.objects.get(assessment_id=assessment_id)
            assessment.height = request.POST.get("height")
            assessment.weight = request.POST.get("weight")
            assessment.muscle_mass = request.POST.get("muscle_mass")
            assessment.fat_mass = request.POST.get("fat_mass")
            assessment.save()

            return JsonResponse({"status": "updated"})
        except Assessment.DoesNotExist:
            return JsonResponse({"error": "Assessment not found"}, status=400)


def AD_Booking(request):
    # Ensure the admin is logged in
    if "login_id" not in request.session or request.session.get("user_type") != "Admin":
        return redirect('/Home/Login/')

    today = timezone.now().date()

    # Fetch all trainers
    trainers = Trainer.objects.filter(trainer_status=True)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "fetch_bookings":
            trainer_id = request.POST.get("trainer_id")

            # Fetch today's bookings for the selected trainer
            bookings = Booking.objects.filter(session_id__trainer_id=trainer_id, booking_date=today).select_related("session_id", "customer_id")

            booking_data = [
                {
                    "booking_id": b.booking_id,
                    "session_id": b.session_id.session_id,
                    "customer_name": b.customer_id.customer_name,
                    "time_slot": str(b.session_id.time_slot),
                } for b in bookings
            ]
            return JsonResponse({"status": "success", "bookings": booking_data})

    return render(request, "ad_booking.html", {
        "trainers": trainers,
    })


def AD_Records(request):
    if "login_id" not in request.session:
        return redirect('/Home/Login/')

    # Fetch all customers
    customers = Customer.objects.all()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "fetch_customer_records":
            customer_id = request.POST.get("customer_id")
            try:
                records = Record.objects.select_related('customer', 'plan_id', 'diet_id').filter(customer_id=customer_id)
                records_data = [
                    {
                        "record_id": record.record_id,
                        "goal": record.goal,
                        "workout_split": record.plan_id.workout_split if record.plan_id else None,
                        "week_start_date": record.plan_id.week_start_date.strftime("%Y-%m-%d") if record.plan_id else None,
                        "diet_calories": record.diet_id.calories if record.diet_id else None,
                        "diet_protein_grams": record.diet_id.protein_grams if record.diet_id else None,
                        "diet_fat_grams": record.diet_id.fat_grams if record.diet_id else None,
                        "diet_carb_grams": record.diet_id.carb_grams if record.diet_id else None,
                        "diet_water_liters": record.diet_id.water_liters if record.diet_id else None,
                        "diet_week_start_date": record.diet_id.week_start_date.strftime("%Y-%m-%d") if record.diet_id else None,
                        "plan_id": record.plan_id.plan_id if record.plan_id else None
                    }
                    for record in records
                ]
                return JsonResponse({"status": "success", "records": records_data})
            except Record.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Records not found"}, status=400)

        elif action == "fetch_workout_details":
            plan_id = request.POST.get("plan_id")
            try:
                workout_plan = WorkoutPlan.objects.get(plan_id=plan_id)
                workout_data = {
                    "goal": workout_plan.goal,
                    "week_start_date": workout_plan.week_start_date.strftime("%Y-%m-%d"),
                    "workout_split": workout_plan.workout_split,
                    "mon_exercises": workout_plan.mon_exercises,
                    "tue_exercises": workout_plan.tue_exercises,
                    "wed_exercises": workout_plan.wed_exercises,
                    "thu_exercises": workout_plan.thu_exercises,
                    "fri_exercises": workout_plan.fri_exercises,
                    "sat_exercises": workout_plan.sat_exercises,
                    "sun_exercises": workout_plan.sun_exercises
                }
                return JsonResponse({"status": "success", "workout": workout_data})
            except WorkoutPlan.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Workout plan not found"}, status=400)

    return render(request, "ad_records.html", {
        "customers": customers
    })


def AD_Analytics(request):
    if "login_id" not in request.session:
        return redirect('/Home/Login/')

    # Fetch all active customers
    active_customers = Customer.objects.filter(customer_status=True)

    # Handle AJAX requests for fetching assessment history
    if request.method == "POST" and request.POST.get("action") == "fetch_assessment_history":
        customer_id = request.POST.get("customer_id")
        assessments = Assessment.objects.filter(customer_id=customer_id).order_by("date")

        if not assessments.exists():
            return JsonResponse({"status": "error", "message": "No past assessments available."})

        history_data = {
            "dates": [a.date.strftime("%Y-%m-%d") for a in assessments],
            "weights": [a.weight for a in assessments],
            "bmis": [round(a.weight / ((a.height / 100) ** 2), 2) for a in assessments],  # Calculate BMI
            "muscle_masses": [a.muscle_mass for a in assessments],
            "fat_masses": [a.fat_mass for a in assessments]
        }

        return JsonResponse({"status": "success", "history": history_data})

    return render(request, "ad_analytics.html", {
        "active_customers": active_customers
    })

#Trainer Pages
def TR_Dashboard(request):
    return render(request, 'tr_dashboard.html')

def TR_Bills(request):
    payments = Payment.objects.select_related("customer_id").order_by("-payment_date")

    return render(request, "tr_bills.html", {"payments": payments})

def TR_Bill_Page(request):
    payment_id = request.GET.get("payment_id")
    
    if not payment_id:
        return redirect("/Home/")

    payment = Payment.objects.get(payment_id=payment_id)
    customer = payment.customer_id  # Reference to Customer object
    category = TrainerCategory.objects.get(cat_id=customer.cat_id.cat_id)

    context = {
       "customer": customer,
            "payment": payment,
            "category" : category,
            "date": payment.payment_date,

    }
    
    return render(request, "common_bill.html", context)

# ✅ Function to generate and download bill as PDF
def TR_Download_Bill(request, payment_id):
    payment = Payment.objects.get(payment_id=payment_id)
    customer = payment.customer_id
    category = TrainerCategory.objects.get(cat_id=customer.cat_id.cat_id) 

    context = {
       "payment": payment,
            "customer": customer,
            "category": category,  # ✅ Now included
            "date": payment.payment_date,

    }

    # ✅ Convert bill HTML to string
    html_string = render_to_string("common_bill.html", context)

    # ✅ Convert HTML to PDF
    pdf = pdfkit.from_string(html_string, False)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Bill_{payment_id}.pdf"'

    return response


def TR_Trainer_cat(request):
    categories = TrainerCategory.objects.all()  # Fetch all trainer categories
    return render(request, 'tr_trainer_cat.html', {"categories": categories})

def TR_Trainer(request):
    trainers = Trainer.objects.filter(trainer_status=True)  # Fetch only active trainers
    return render(request, 'tr_trainer.html', {"trainers": trainers})


def TR_Exercise(request):
    """Handles exercise management for trainers."""

    # Ensure only logged-in trainers can access
    if 'login_id' not in request.session or request.session.get('user_type') != "Trainer":
        return redirect('/Home/Login/')  

    trainer_id = request.session['login_id']

    if request.method == "POST":
        action = request.POST.get("action")

        try:
            # Delete exercise
            if action == "delete":
                exercise_id = request.POST.get("exerciseId")
                if not exercise_id:
                    return JsonResponse({"status": "error", "message": "Exercise ID is required"})
                Exercise.objects.filter(exercise_id=exercise_id, trainer_id=trainer_id).delete()
                return JsonResponse({"status": "success", "message": "Exercise deleted"})
            # Add or update exercise
            exercise_id = request.POST.get("exerciseId")
            exercise_name = request.POST.get("exerciseName")
            exercise_type = request.POST.get("exerciseType")
            target_muscle = request.POST.get("targetMuscle")

            # Basic validations
            if not exercise_name:
                return JsonResponse({"status": "error", "message": "Exercise name is required"})
            if exercise_type not in ['Push', 'Pull', 'Legs', 'Cardio', 'Full Body', 'Upper', 'Lower']:
                return JsonResponse({"status": "error", "message": "Invalid exercise type"})
            if target_muscle not in ['Chest', 'Back', 'Shoulders', 'Triceps', 'Biceps', 'Quads', 'Hamstrings', 'Calves', 'Glutes', 'Core', 'Full Body']:
                return JsonResponse({"status": "error", "message": "Invalid target muscle"})

            # Update existing exercise
            if exercise_id:
                exercise = Exercise.objects.filter(exercise_id=exercise_id, trainer_id=trainer_id).first()
                if not exercise:
                    return JsonResponse({"status": "error", "message": "Exercise not found"})
                exercise.exercise_name = exercise_name
                exercise.exercise_type = exercise_type
                exercise.target_muscle = target_muscle
                exercise.save()
                return JsonResponse({"status": "success", "message": "Exercise updated"})

            # Add new exercise
            last_exercise = Exercise.objects.aggregate(Max('exercise_id'))['exercise_id__max']
            if last_exercise and re.match(r'^EX\d{2}$', last_exercise):
                last_id = int(last_exercise[2:])
                new_id = f"EX{last_id + 1:02d}"
            else:
                new_id = "EX01"

            Exercise.objects.create(
                exercise_id=new_id,
                trainer=Trainer.objects.get(trainer_id=trainer_id),
                exercise_name=exercise_name,
                exercise_type=exercise_type,
                target_muscle=target_muscle
            )
            return JsonResponse({"status": "success", "message": "Exercise added"})

        except Trainer.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Trainer not found"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    # Fetch exercises for the logged-in trainer
    exercises = Exercise.objects.select_related('trainer').order_by('exercise_id')
    return render(request, 'tr_exercise.html', {
        "exercises": exercises,
        "trainer_id": trainer_id
    })

def TR_Session(request):
    # Redirect if the user is not logged in
    if 'login_id' not in request.session:
        return redirect('/Home/Login/')

    trainer_id = request.session.get('login_id')  # Get logged-in trainer's ID

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            # Add a new session
            time_slot = request.POST.get("timeSlot")

            if not time_slot:
                return JsonResponse({"status": "error", "message": "Invalid time slot"})

            try:
                # Generate a new session ID
                last_session = Session.objects.order_by('-session_id').first()
                if last_session:
                    last_id = int(re.search(r'\d+', last_session.session_id).group())
                    new_id = f"TS{last_id + 1:02d}"
                else:
                    new_id = "TS01"
                    
                # Create the new session
                Session.objects.create(
                    session_id=new_id,
                    trainer_id=Trainer.objects.get(trainer_id=trainer_id),
                    time_slot=time_slot,
                    session_status=True  # Default Active
                )

                return JsonResponse({"status": "success", "session_id": new_id})

            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)})

        elif action == "edit":
            # Edit an existing session
            session_id = request.POST.get("sessionId")
            time_slot = request.POST.get("timeSlot")

            if not session_id or not time_slot:
                return JsonResponse({"status": "error", "message": "Invalid data provided"})

            try:
                # Ensure the session belongs to the logged-in trainer
                session = Session.objects.get(session_id=session_id, trainer_id=trainer_id)
                session.time_slot = time_slot
                session.save()
                return JsonResponse({"status": "updated"})

            except ObjectDoesNotExist:
                return JsonResponse({"status": "error", "message": "Session not found"})
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)})

        elif action == "toggle_status":
            # Toggle session status (Active/Inactive)
            session_id = request.POST.get("sessionId")

            try:
                # Ensure the session belongs to the logged-in trainer
                session = Session.objects.get(session_id=session_id, trainer_id=trainer_id)
                session.session_status = not session.session_status
                session.save()
                return JsonResponse({"status": "updated", "session_status": session.session_status})

            except ObjectDoesNotExist:
                return JsonResponse({"status": "error", "message": "Session not found"})
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)})

        else:
            return JsonResponse({"status": "error", "message": "Invalid action"})

    # Handle GET request (Fetch all sessions for the logged-in trainer)
    try:
        sessions = Session.objects.filter(trainer_id=trainer_id)
        return render(request, 'tr_session.html', {"sessions": sessions, "trainer_id": trainer_id})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


def TR_Customer(request):
    customers = Customer.objects.select_related('cat_id').all()  # Fetch all customers with category names
    return render(request, 'tr_customer.html', {"customers": customers})
def TR_Assessment(request):
    customers = Customer.objects.filter(customer_status=True)

    if request.method == "POST":
        customer_id = request.POST.get("customer_id")
        height = request.POST.get("height")
        weight = request.POST.get("weight")
        muscle_mass = request.POST.get("muscle_mass")
        fat_mass = request.POST.get("fat_mass")

        # Generate `assessment_id` (AS01, AS02, ...)
        last_assessment = Assessment.objects.order_by("-assessment_id").first()
        if last_assessment:
            last_id = int(re.search(r'\d+', last_assessment.assessment_id).group())
            new_id = f"AS{last_id + 1:02d}"
        else:
            new_id = "AS01"

        # Get Customer Object
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return JsonResponse({"error": "Customer not found"}, status=400)

        # Insert into `tbl_assessment`
        Assessment.objects.create(
            assessment_id=new_id,
            customer_id=customer,
            height=height,
            weight=weight,
            muscle_mass=muscle_mass,
            fat_mass=fat_mass,
            date=date.today()
        )

        return JsonResponse({"status": "success", "assessment_id": new_id})

    return render(request, "tr_assessment.html", {"customers": customers})

def TR_Booking(request):
    # Ensure trainer is logged in
    if "login_id" not in request.session:
        return redirect('/Home/Login/')

    trainer_id = request.session.get("login_id")  # Logged-in trainer's ID

    try:
        trainer = Trainer.objects.get(trainer_id=trainer_id)
    except Trainer.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Trainer not found"}, status=400)

    today = timezone.now().date()

    # Fetch today's bookings for this trainer
    bookings = Booking.objects.filter(session_id__trainer_id=trainer, booking_date=today).select_related("session_id", "customer_id")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "cancel_booking":
            booking_id = request.POST.get("booking_id")

            try:
                booking = Booking.objects.get(booking_id=booking_id)
                booking.delete()  # Remove the booking entry
                return JsonResponse({"status": "success"})
            except Booking.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Booking not found"}, status=400)

    return render(request, "tr_booking.html", {
        "bookings": bookings
    })
    
    

def TR_Records(request):
    if "login_id" not in request.session:
        return redirect('/Home/Login/')

    trainer_id = request.session.get("login_id")

    # Fetch all unique active customers (where customer_status is True)
    customers = Customer.objects.filter(customer_status=True).distinct()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "fetch_customer_records":
            customer_id = request.POST.get("customer_id")
            try:
                records = Record.objects.select_related('customer', 'plan_id', 'diet_id').filter(customer_id=customer_id)
                records_data = [
                    {
                        "record_id": record.record_id,
                        "goal": record.goal,
                        "workout_split": record.plan_id.workout_split if record.plan_id else None,
                        "week_start_date": record.plan_id.week_start_date.strftime("%Y-%m-%d") if record.plan_id else None,
                        "diet_calories": record.diet_id.calories if record.diet_id else None,
                        "diet_protein_grams": record.diet_id.protein_grams if record.diet_id else None,
                        "diet_fat_grams": record.diet_id.fat_grams if record.diet_id else None,
                        "diet_carb_grams": record.diet_id.carb_grams if record.diet_id else None,
                        "diet_water_liters": record.diet_id.water_liters if record.diet_id else None,
                        "diet_week_start_date": record.diet_id.week_start_date.strftime("%Y-%m-%d") if record.diet_id else None,
                        "plan_id": record.plan_id.plan_id if record.plan_id else None
                    }
                    for record in records
                ]
                return JsonResponse({"status": "success", "records": records_data})
            except Record.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Records not found"}, status=400)

        elif action == "fetch_workout_details":
            plan_id = request.POST.get("plan_id")
            try:
                workout_plan = WorkoutPlan.objects.get(plan_id=plan_id)
                workout_data = {
                    "goal": workout_plan.goal,
                    "week_start_date": workout_plan.week_start_date.strftime("%Y-%m-%d"),
                    "workout_split": workout_plan.workout_split,
                    "mon_exercises": workout_plan.mon_exercises,
                    "tue_exercises": workout_plan.tue_exercises,
                    "wed_exercises": workout_plan.wed_exercises,
                    "thu_exercises": workout_plan.thu_exercises,
                    "fri_exercises": workout_plan.fri_exercises,
                    "sat_exercises": workout_plan.sat_exercises,
                    "sun_exercises": workout_plan.sun_exercises
                }
                return JsonResponse({"status": "success", "workout": workout_data})
            except WorkoutPlan.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Workout plan not found"}, status=400)

    return render(request, "tr_records.html", {
        "customers": customers
    })
    
def TR_Workout(request):
    if "login_id" not in request.session:
        return redirect('/Home/Login/')

    trainer_id = request.session.get("login_id")

    # Fetch all customers with their current workout plan
    customers = Customer.objects.prefetch_related(
        Prefetch('workoutplan_set', 
                queryset=WorkoutPlan.objects.order_by('-week_start_date'),
                to_attr='workout_plans')
    ).all()

    # Add current_workout property to each customer
    for customer in customers:
        customer.current_workout = customer.workout_plans[0] if customer.workout_plans else None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "fetch_exercises":
            exercises_data = [
                {
                    "exercise_id": ex.exercise_id,
                    "exercise_name": ex.exercise_name
                }
                for ex in Exercise.objects.all()
            ]
            return JsonResponse({"status": "success", "exercises": exercises_data})

        elif action == "fetch_workout_details":
            plan_id = request.POST.get("plan_id")
            try:
                workout_plan = WorkoutPlan.objects.get(plan_id=plan_id)
                workout_data = {
                    "customer_name": workout_plan.customer.customer_name,
                    "goal": workout_plan.goal,
                    "week_start_date": workout_plan.week_start_date.strftime("%Y-%m-%d"),
                    "workout_split": workout_plan.workout_split,
                    "mon_exercises": workout_plan.mon_exercises,
                    "tue_exercises": workout_plan.tue_exercises,
                    "wed_exercises": workout_plan.wed_exercises,
                    "thu_exercises": workout_plan.thu_exercises,
                    "fri_exercises": workout_plan.fri_exercises,
                    "sat_exercises": workout_plan.sat_exercises,
                    "sun_exercises": workout_plan.sun_exercises
                }
                return JsonResponse({"status": "success", "workout": workout_data})
            except WorkoutPlan.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Workout plan not found"}, status=400)

        elif action == "update_workout":
            plan_id = request.POST.get("plan_id")
            try:
                workout_plan = WorkoutPlan.objects.get(plan_id=plan_id)
                
                # Update exercises for each day
                days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
                for day in days:
                    exercises = request.POST.get(f"{day}_exercises", "")
                    setattr(workout_plan, f"{day}_exercises", exercises)
                
                workout_plan.save()
                return JsonResponse({"status": "success"})
            except WorkoutPlan.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Workout plan not found"}, status=400)

    return render(request, "tr_workout.html", {
        "customers": customers
    })
def TR_Diet(request):
    if "login_id" not in request.session:
        return redirect('/Home/Login/')

    trainer_id = request.session.get("login_id")

    # Fetch all customers with their current diet plan
    customers = Customer.objects.prefetch_related(
        Prefetch('diet_set', 
                 queryset=Diet.objects.order_by('-week_start_date'),
                 to_attr='diet_plans')
    ).all()

    # Add current_diet property to each customer
    for customer in customers:
        customer.current_diet = customer.diet_plans[0] if customer.diet_plans else None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "fetch_diet_details":
            diet_id = request.POST.get("diet_id")
            try:
                diet = Diet.objects.get(diet_id=diet_id)
                diet_data = {
                    "customer_name": diet.customer.customer_name,
                    "calories": diet.calories,
                    "protein_grams": diet.protein_grams,
                    "fat_grams": diet.fat_grams,
                    "carb_grams": diet.carb_grams,
                    "water_liters": diet.water_liters,
                    "week_start_date": diet.week_start_date.strftime("%Y-%m-%d")
                }
                return JsonResponse({"status": "success", "diet": diet_data})
            except Diet.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Diet plan not found"}, status=400)

        elif action == "update_diet":
            diet_id = request.POST.get("diet_id")
            try:
                diet = Diet.objects.get(diet_id=diet_id)
                diet.calories = request.POST.get("calories")
                diet.protein_grams = request.POST.get("protein_grams")
                diet.fat_grams = request.POST.get("fat_grams")
                diet.carb_grams = request.POST.get("carb_grams")
                diet.water_liters = request.POST.get("water_liters")
                diet.week_start_date = request.POST.get("week_start_date")
                diet.save()
                return JsonResponse({"status": "success"})
            except Diet.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Diet plan not found"}, status=400)

    return render(request, "tr_diet.html", {
        "customers": customers
    })
    
def TR_Analytics(request):
    if "login_id" not in request.session:
        return redirect('/Home/Login/')

    # Fetch all active customers
    active_customers = Customer.objects.filter(customer_status=True)

    # Handle AJAX requests for fetching assessment history
    if request.method == "POST" and request.POST.get("action") == "fetch_assessment_history":
        customer_id = request.POST.get("customer_id")
        assessments = Assessment.objects.filter(customer_id=customer_id).order_by("date")

        if not assessments.exists():
            return JsonResponse({"status": "error", "message": "No past assessments available."})

        history_data = {
            "dates": [a.date.strftime("%Y-%m-%d") for a in assessments],
            "weights": [a.weight for a in assessments],
            "bmis": [round(a.weight / ((a.height / 100) ** 2), 2) for a in assessments],  # Calculate BMI
            "muscle_masses": [a.muscle_mass for a in assessments],
            "fat_masses": [a.fat_mass for a in assessments]
        }

        return JsonResponse({"status": "success", "history": history_data})

    return render(request, "tr_analytics.html", {
        "active_customers": active_customers
    })

    
#Customer Pages
def CU_Dashboard(request):
    return render(request, 'cu_dashboard.html')

def CU_Bills(request):
    customer_id = request.session.get("customer_id")  # Fetch logged-in customer ID
    if not customer_id:
        messages.error(request, "You must be logged in to  past bills.")
        return redirect("/Home/Login/")

    # Retrieve all payments for the logged-in customer
    customer = Customer.objects.get(customer_id=customer_id)
    payments = Payment.objects.filter(customer_id=customer).order_by("-payment_date")  # Most recent first

    return render(request, "cu_bills.html", {"customer": customer, "payments": payments})

def CU_Bill_Page(request):
    payment_id = request.GET.get("payment_id")
    
    if not payment_id:
        return redirect("/Home/")

    payment = Payment.objects.get(payment_id=payment_id)
    customer = payment.customer_id  # Reference to Customer object
    category = TrainerCategory.objects.get(cat_id=customer.cat_id.cat_id)

    context = {
       "customer": customer,
            "payment": payment,
            "category" : category,
            "date": payment.payment_date,

    }
    
    return render(request, "common_bill.html", context)

# ✅ Function to generate and download bill as PDF
def CU_Download_Bill(request, payment_id):
    payment = Payment.objects.get(payment_id=payment_id)
    customer = payment.customer_id
    category = TrainerCategory.objects.get(cat_id=customer.cat_id.cat_id) 

    context = {
       "payment": payment,
            "customer": customer,
            "category": category,  # ✅ Now included
            "date": payment.payment_date,

    }

    # ✅ Convert bill HTML to string
    html_string = render_to_string("common_bill.html", context)

    # ✅ Convert HTML to PDF
    pdf = pdfkit.from_string(html_string, False)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Bill_{payment_id}.pdf"'

    return response



def CU_Trainer_cat(request):
    categories = TrainerCategory.objects.all()  # Fetch all trainer categories
    return render(request, 'cu_trainer_cat.html', {"categories": categories})

def CU_Trainer(request):
    trainers = Trainer.objects.filter(trainer_status=True)  # Fetch only active trainers
    return render(request, 'cu_trainer.html', {"trainers": trainers})


def CU_Session(request):
    # Fetch only active trainers and use select_related to optimize database queries
    trainers = Trainer.objects.select_related('cat_id').filter(trainer_status=True)
    return render(request, 'cu_session.html', {'trainers': trainers})


def CU_Customer(request):
    # Ensure customer is logged in
    if "login_id" not in request.session or request.session.get("user_type") != "Customer":
        return redirect("/Home/Login/")

    customer_id = request.session["login_id"]

    try:
        customer = Customer.objects.select_related("cat_id").get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Customer not found"}, status=404)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "edit":
            customer.customer_name = request.POST.get("customer_name")
            customer.customer_email = request.POST.get("customer_email")
            customer.customer_phone = request.POST.get("customer_phone")
            customer.save()
            return JsonResponse({"status": "updated"})

    return render(request, "cu_customer.html", {"customer": customer})

def CU_Assessment(request):
    # ✅ Print session data for debugging
    print("Session Data:", request.session)

    # Fetch the logged-in customer's ID from session
    customer_id = request.session.get("customer_id")  

    if not customer_id:
        return JsonResponse({"error": "User not logged in"}, status=400)

    # Fetch the latest assessment for the logged-in customer
    last_assessment = Assessment.objects.filter(customer_id=customer_id).order_by("-date").first()

    return render(request, "cu_assessment.html", {"last_assessment": last_assessment})


def CU_Booking(request):
    if "customer_id" not in request.session:
        return redirect('/Home/Login/')

    customer_id = request.session.get("customer_id")

    try:
        customer = Customer.objects.get(customer_id=customer_id)
        cat_id = customer.cat_id.cat_id
    except Customer.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Customer not found"}, status=400)

    trainers = Trainer.objects.filter(cat_id=cat_id, trainer_status=True)

    today = timezone.now().date()

    # Fetch today's booked session for this customer
    today_booking = Booking.objects.filter(customer_id=customer_id, booking_date=today).select_related("session_id").first()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "fetch_sessions":
            trainer_id = request.POST.get("trainer_id")

            # Get active sessions for the trainer that are not already booked today
            booked_sessions = Booking.objects.filter(booking_date=today).values_list("session_id", flat=True)
            sessions = Session.objects.filter(trainer_id=trainer_id, session_status=True).exclude(session_id__in=booked_sessions)

            session_data = [{"session_id": s.session_id, "time_slot": str(s.time_slot)} for s in sessions]
            return JsonResponse({"status": "success", "sessions": session_data})

        elif action == "book_session":
            session_id = request.POST.get("session_id")

            try:
                session = Session.objects.get(session_id=session_id, session_status=True)
            except Session.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Session not available"}, status=400)

            # Overwrite existing booking if it exists
            if today_booking:
                today_booking.session_id = session
                today_booking.save()
                return JsonResponse({"status": "success", "booking_id": today_booking.booking_id})

            # Generate new booking ID
            last_booking = Booking.objects.order_by("-booking_id").first()
            new_booking_id = f"BK{int(re.search(r'\d+', last_booking.booking_id).group()) + 1:02d}" if last_booking else "BK01"

            Booking.objects.create(
                booking_id=new_booking_id,
                session_id=session,
                customer_id=customer,
                booking_date=today
            )

            return JsonResponse({"status": "success", "booking_id": new_booking_id})

    return render(request, "cu_booking.html", {
        "trainers": trainers,
        "today_booking": today_booking
    })
    

def CU_Records(request):
    if "login_id" not in request.session:
        return redirect('/Home/Login/')

    customer_id = request.session.get("login_id")

    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return redirect('/Home/Login/')

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "fetch_customer_records":
            try:
                records = Record.objects.select_related('customer', 'plan_id', 'diet_id').filter(customer_id=customer_id)
                records_data = [
                    {
                        "record_id": record.record_id,
                        "goal": record.goal,
                        "workout_split": record.plan_id.workout_split if record.plan_id else None,
                        "week_start_date": record.plan_id.week_start_date.strftime("%Y-%m-%d") if record.plan_id else None,
                        "diet_calories": record.diet_id.calories if record.diet_id else None,
                        "diet_protein_grams": record.diet_id.protein_grams if record.diet_id else None,
                        "diet_fat_grams": record.diet_id.fat_grams if record.diet_id else None,
                        "diet_carb_grams": record.diet_id.carb_grams if record.diet_id else None,
                        "diet_water_liters": record.diet_id.water_liters if record.diet_id else None,
                        "diet_week_start_date": record.diet_id.week_start_date.strftime("%Y-%m-%d") if record.diet_id else None,
                        "plan_id": record.plan_id.plan_id if record.plan_id else None
                    }
                    for record in records
                ]
                return JsonResponse({"status": "success", "records": records_data})
            except Record.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Records not found"}, status=400)

        elif action == "fetch_workout_details":
            plan_id = request.POST.get("plan_id")
            try:
                workout_plan = WorkoutPlan.objects.get(plan_id=plan_id)
                workout_data = {
                    "goal": workout_plan.goal,
                    "week_start_date": workout_plan.week_start_date.strftime("%Y-%m-%d"),
                    "workout_split": workout_plan.workout_split,
                    "mon_exercises": workout_plan.mon_exercises,
                    "tue_exercises": workout_plan.tue_exercises,
                    "wed_exercises": workout_plan.wed_exercises,
                    "thu_exercises": workout_plan.thu_exercises,
                    "fri_exercises": workout_plan.fri_exercises,
                    "sat_exercises": workout_plan.sat_exercises,
                    "sun_exercises": workout_plan.sun_exercises
                }
                return JsonResponse({"status": "success", "workout": workout_data})
            except WorkoutPlan.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Workout plan not found"}, status=400)

    return render(request, "cu_records.html", {
        "customer": customer
    })



def CU_Analytics(request):
    if "login_id" not in request.session:
        return redirect('/Home/Login/')

    customer_id = request.session.get("login_id")  # Get the logged-in customer ID

    # Fetch all past assessments for this customer
    assessments = Assessment.objects.filter(customer_id=customer_id).order_by("date")

    history_data = {
        "dates": [a.date.strftime("%Y-%m-%d") for a in assessments],
        "weights": [a.weight for a in assessments],
        "bmis": [round(a.weight / ((a.height / 100) ** 2), 2) for a in assessments],  # Calculate BMI
        "muscle_masses": [a.muscle_mass for a in assessments],
        "fat_masses": [a.fat_mass for a in assessments]
    }

    return render(request, "cu_analytics.html", {
        "history_data": history_data
    })
#Api


# Set up logging
logger = logging.getLogger(__name__)

@login_required
def CU_Exercise(request):
    logger.info(f"Request: {request.method} {request.path}, User: {request.user}, Session: {request.session.items()}")
    login_id = request.session.get('login_id')
    user_type = request.session.get('user_type')

    if not login_id or user_type != "Customer":
        logger.warning(f"Unauthorized access: login_id={login_id}, user_type={user_type}")
        return render(request, 'cu_error.html', {'message': 'Unauthorized access or session expired.'})

    try:
        customer = Customer.objects.get(customer_id=login_id)
    except Customer.DoesNotExist:
        logger.error(f"Customer not found for login_id: {login_id}")
        return render(request, 'cu_error.html', {'message': 'Customer not found.'})

    latest_assessment = Assessment.objects.filter(customer_id=customer).order_by('-date').first()
    show_goal_form = False
    workout_plan = None
    day_exercises = {}
    workout_split = ''
    exercise_weights = {}
    history_data = {'dates': [], 'muscle_masses': [], 'fat_masses': [], 'weights': [], 'bmis': []}

    if latest_assessment:
        workout_plan = WorkoutPlan.objects.filter(customer=customer, assessment=latest_assessment).first()
        if not workout_plan:
            show_goal_form = True
        else:
            workout_split = workout_plan.workout_split
            day_exercises = {
                'Monday': [{'exercise': ex} for ex in (workout_plan.mon_exercises.split(',') if workout_plan.mon_exercises else []) if ex],
                'Tuesday': [{'exercise': ex} for ex in (workout_plan.tue_exercises.split(',') if workout_plan.tue_exercises else []) if ex],
                'Wednesday': [{'exercise': ex} for ex in (workout_plan.wed_exercises.split(',') if workout_plan.wed_exercises else []) if ex],
                'Thursday': [{'exercise': ex} for ex in (workout_plan.thu_exercises.split(',') if workout_plan.thu_exercises else []) if ex],
                'Friday': [{'exercise': ex} for ex in (workout_plan.fri_exercises.split(',') if workout_plan.fri_exercises else []) if ex],
                'Saturday': [{'exercise': ex} for ex in (workout_plan.sat_exercises.split(',') if workout_plan.sat_exercises else []) if ex],
                'Sunday': [{'exercise': ex} for ex in (workout_plan.sun_exercises.split(',') if workout_plan.sun_exercises else []) if ex]
            }
            plan_exercises = set()
            for day in day_exercises.values():
                for ex in day:
                    plan_exercises.add(ex['exercise'])
            exercises = Exercise.objects.filter(exercise_name__in=plan_exercises)
            for ex in exercises:
                last_weight = ExerciseWeight.objects.filter(
                    customer=customer,
                    exercise=ex
                ).order_by('-date').first()
                exercise_weights[ex.exercise_name] = {
                    'set_1_weight': last_weight.set_1_weight if last_weight else None,
                    'set_2_weight': last_weight.set_2_weight if last_weight else None,
                    'set_3_weight': last_weight.set_3_weight if last_weight else None,
                    'comment': last_weight.comment if last_weight else None,
                    'date': last_weight.date if last_weight else None
                }
            assessments = Assessment.objects.filter(customer_id=customer).order_by('date')
            history_data = {
                'dates': json.dumps([str(a.date) for a in assessments]),
                'muscle_masses': json.dumps([a.muscle_mass for a in assessments]),
                'fat_masses': json.dumps([a.fat_mass for a in assessments]),
                'weights': json.dumps([a.weight for a in assessments]),
                'bmis': json.dumps([(a.weight / ((a.height / 100) ** 2)) for a in assessments])
            }
    else:
        show_goal_form = True

    if request.method == 'POST' and 'action' in request.POST:
        if request.POST['action'] == 'set_goal':
            goal = request.POST.get('goal')
            if goal not in ['bulk', 'cut', 'maintenance']:
                logger.error(f"Invalid goal: {goal}")
                return JsonResponse({'status': 'error', 'message': 'Invalid goal'})

            goal_mapping = {
                'bulk': 'Build muscle mass with hypertrophy-focused exercises',
                'cut': 'Lose fat while preserving muscle with high-intensity workouts',
                'maintenance': 'Maintain physique with balanced strength and cardio'
            }
            goal_description = goal_mapping[goal]

            past_plans = WorkoutPlan.objects.filter(customer=customer).values(
                'workout_split', 'mon_exercises', 'tue_exercises', 'wed_exercises',
                'thu_exercises', 'fri_exercises', 'sat_exercises', 'sun_exercises'
            )
            past_exercises = [
                ex for plan in past_plans
                for day in ['mon_exercises', 'tue_exercises', 'wed_exercises', 'thu_exercises', 'fri_exercises', 'sat_exercises', 'sun_exercises']
                for ex in (plan[day].split(',') if plan[day] else [])
            ]

            def generate_fallback_plan(goal, past_exercises):
                exercises_by_type = {
                    'Push': list(Exercise.objects.filter(exercise_type='Push', target_muscle__in=['Chest', 'Shoulders', 'Triceps']).values_list('exercise_name', flat=True)),
                    'Pull': list(Exercise.objects.filter(exercise_type='Pull', target_muscle__in=['Back', 'Biceps']).values_list('exercise_name', flat=True)),
                    'Legs': list(Exercise.objects.filter(exercise_type='Legs', target_muscle__in=['Quads', 'Hamstrings', 'Calves', 'Glutes']).values_list('exercise_name', flat=True)),
                    'Cardio': list(Exercise.objects.filter(exercise_type='Cardio').values_list('exercise_name', flat=True)),
                    'Full Body': list(Exercise.objects.filter(exercise_type='Full Body').values_list('exercise_name', flat=True)),
                    'Upper': list(Exercise.objects.filter(exercise_type='Upper', target_muscle__in=['Chest', 'Back', 'Shoulders', 'Triceps', 'Biceps']).values_list('exercise_name', flat=True)),
                    'Lower': list(Exercise.objects.filter(exercise_type='Lower', target_muscle__in=['Quads', 'Hamstrings', 'Calves', 'Glutes']).values_list('exercise_name', flat=True)),
                }
                for key in exercises_by_type:
                    exercises_by_type[key] = [exercise for exercise in exercises_by_type[key] if exercise not in past_exercises]
                    random.shuffle(exercises_by_type[key])
                splits = {
                    'bulk': ['Push', 'Pull', 'Legs', 'Rest', 'Upper', 'Lower', 'Rest'],
                    'cut': ['Push', 'Pull', 'Legs', 'Cardio', 'Rest', 'Full Body', 'Rest'],
                    'maintenance': ['Upper', 'Lower', 'Rest', 'Full Body', 'Rest', 'Cardio', 'Rest']
                }
                workout_split = '-'.join(splits[goal])
                daily_exercises = {
                    'mon': [],
                    'tue': [],
                    'wed': [],
                    'thu': [],
                    'fri': [],
                    'sat': [],
                    'sun': []
                }
                days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
                for i, day in enumerate(days):
                    if splits[goal][i] == 'Rest':
                        daily_exercises[day] = []
                    elif splits[goal][i] == 'Cardio':
                        daily_exercises[day] = [{'name': 'Cardio: 30 mins LISS'}]
                    else:
                        exercise_pool = exercises_by_type.get(splits[goal][i], [])
                        if not exercise_pool:
                            exercise_pool = exercises_by_type['Full Body']
                        daily_exercises[day] = [{'name': exercise} for exercise in exercise_pool[:7]]
                return {'workout_split': workout_split, 'daily_exercises': daily_exercises}

            def generate_diet_plan(goal, assessment):
                weight = assessment.weight
                maintenance_calories = weight * 32
                if goal == 'bulk':
                    calories = int(maintenance_calories * 1.15)
                    protein_grams = int(weight * 2.0)
                    fat_grams = int(weight * 0.8)
                    carb_grams = int((calories - (protein_grams * 4 + fat_grams * 9)) / 4)
                elif goal == 'cut':
                    calories = int(maintenance_calories * 0.85)
                    protein_grams = int(weight * 2.2)
                    fat_grams = int(weight * 0.6)
                    carb_grams = int((calories - (protein_grams * 4 + fat_grams * 9)) / 4)
                else:
                    calories = int(maintenance_calories)
                    protein_grams = int(weight * 1.8)
                    fat_grams = int(weight * 0.7)
                    carb_grams = int((calories - (protein_grams * 4 + fat_grams * 9)) / 4)
                water_liters = round(weight * 0.033, 1)
                return {
                    'calories': calories,
                    'protein_grams': protein_grams,
                    'fat_grams': fat_grams,
                    'carb_grams': carb_grams,
                    'water_liters': water_liters
                }

            try:
                available_exercises = Exercise.objects.all()
                if not available_exercises:
                    logger.error("No exercises found in tbl_exercise")
                    return JsonResponse({'status': 'error', 'message': 'No exercises available in the database.'})

                prompt = f"""
                    You are an elite fitness coach tasked with creating a personalized 7-day workout plan for a gym member based on their latest fitness assessment and fitness goal.

                    ### User Assessment
                    - Height: {latest_assessment.height if latest_assessment else 'N/A'} cm
                    - Weight: {latest_assessment.weight if latest_assessment else 'N/A'} kg
                    - Muscle Mass: {latest_assessment.muscle_mass if latest_assessment else 'N/A'} kg
                    - Fat Mass: {latest_assessment.fat_mass if latest_assessment else 'N/A'} kg
                    - Goal: {goal_description} (e.g., Bulk, Cut, or Maintenance)

                    ### Exercise Pool
                    Available exercises with their type and target muscle group:
                    {', '.join([f'{ex.exercise_name} ({ex.exercise_type}, {ex.target_muscle})' for ex in available_exercises])}

                    ### Muscle Group Mapping
                    - Push: Chest, Shoulders, Triceps
                    - Pull: Back, Biceps
                    - Legs: Quads, Hamstrings, Calves, Glutes
                    - Upper: Chest, Back, Shoulders, Arms
                    - Lower: Quads, Hamstrings, Calves, Glutes
                    - Full Body: All muscle groups
                    - Cardio: Cardiovascular exercises

                    ### Past Exercises
                    Avoid reusing: {', '.join(set(past_exercises)) if past_exercises else 'None'}

                    ### Instructions
                    1. Choose the appropriate workout split based on the user's goal:
                       - Bulk: Push-Pull-Legs-Rest-Upper-Lower-Rest or similar
                       - Cut: Push-Pull-Legs-Cardio-Rest-Full Body-Rest or similar
                       - Maintenance: Upper-Lower-Rest-Full Body-Rest-Cardio-Rest or similar

                    2. Assign exercises based on their exercise_type and target_muscle:
                       - Push days: Only Push exercises targeting Chest, Shoulders, Triceps
                       - Pull days: Only Pull exercises targeting Back, Biceps
                       - Legs days: Only Legs exercises targeting Quads, Hamstrings, Calves, Glutes
                       - Upper days: Only Upper exercises targeting Chest, Back, Shoulders, Arms
                       - Lower days: Only Lower exercises targeting Quads, Hamstrings, Calves, Glutes
                       - Full Body days: Only Full Body exercises
                       - Cardio days: Only Cardio exercises (e.g., 'Cardio: 30 mins LISS')

                    3. Absolutely avoid:
                       - Leg exercises (e.g., squats, lunges, leg press) on Push, Pull, or Upper days
                       - Push or Pull exercises (e.g., bench press, pull-ups) on Legs or Lower days

                    4. Provide 5–7 exercises per workout day. Use ['Cardio: 30 mins LISS'] or [] for rest/cardio days.

                    5. Each workout should include 1–2 compound lifts and 3–5 isolation movements.

                    6. Only use exercises from the provided list. Do not invent new exercises.

                    7. Output a valid JSON:
                    ```json
                    {{
                    "workout_split": "Split Type Used",
                    "daily_exercises": {{
                        "mon": [{{"name": "Exercise 1"}}],
                        "tue": [],
                        "wed": [],
                        "thu": [],
                        "fri": [],
                        "sat": [],
                        "sun": []
                    }}
                    }}
                    """
                headers = {
                    'Content-Type': 'application/json',
                    'x-goog-api-key': settings.GOOGLE_AI_API_KEY
                }
                payload = {
                    'contents': [{
                        'parts': [{'text': prompt}]
                    }]
                }
                response = requests.post(
                    'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent',
                    headers=headers,
                    json=payload,
                    timeout=20
                )
                logger.info(f"Gemini API Response: Status {response.status_code}, Time: {response.elapsed.total_seconds()}s")
                if response.status_code == 200:
                    response_data = response.json()
                    generated_text = response_data['candidates'][0]['content']['parts'][0]['text']
                    if generated_text.startswith('```json') and generated_text.endswith('```'):
                        generated_text = generated_text[7:-3].strip()
                    workout_plan_data = json.loads(generated_text)
                else:
                    logger.warning(f"Gemini API failed: {response.text}. Using fallback.")
                    workout_plan_data = generate_fallback_plan(goal, past_exercises)
            except requests.Timeout:
                logger.error("Gemini API timed out. Using fallback.")
                workout_plan_data = generate_fallback_plan(goal, past_exercises)
            except Exception as e:
                logger.error(f"Gemini API Error: {str(e)}. Using fallback.")
                workout_plan_data = generate_fallback_plan(goal, past_exercises)

            try:
                with transaction.atomic():
                    valid_exercises = Exercise.objects.all()
                    valid_exercise_map = {ex.exercise_name: ex for ex in valid_exercises}
                    daily_exercises = workout_plan_data['daily_exercises']
                    splits = workout_plan_data['workout_split'].split('-')
                    for i, day in enumerate(['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']):
                        exercises = daily_exercises[day]
                        split_type = splits[i] if i < len(splits) else 'Rest'
                        valid_types = {
                            'Push': ['Push'],
                            'Pull': ['Pull'],
                            'Legs': ['Legs'],
                            'Upper': ['Upper'],
                            'Lower': ['Lower'],
                            'Full Body': ['Full Body'],
                            'Cardio': ['Cardio'],
                            'Rest': []
                        }.get(split_type, [])
                        for ex in exercises:
                            ex_name = ex['name']
                            if ex_name == 'Cardio: 30 mins LISS' and split_type == 'Cardio':
                                continue
                            if ex_name not in valid_exercise_map:
                                logger.error(f"Invalid exercise: {ex_name}")
                                raise ValueError(f"Exercise {ex_name} not found in database")
                            if valid_exercise_map[ex_name].exercise_type not in valid_types:
                                logger.error(f"Exercise {ex_name} type {valid_exercise_map[ex_name].exercise_type} invalid for {split_type} day")
                                raise ValueError(f"Exercise {ex_name} is not valid for {split_type} day")

                    last_plan_entries = WorkoutPlan.objects.all()
                    last_plan_num = 0
                    for entry in last_plan_entries:
                        match = re.match(r'PL(\d+)', entry.plan_id)
                        if match:
                            num = int(match.group(1))
                            if num > last_plan_num:
                                last_plan_num = num
                    new_plan_id = f"PL{last_plan_num + 1:02d}"
                    last_diet_entries = Diet.objects.all()
                    last_diet_num = 0
                    for entry in last_diet_entries:
                        match = re.match(r'DT(\d+)', entry.diet_id)
                        if match:
                            num = int(match.group(1))
                            if num > last_diet_num:
                                last_diet_num = num
                    new_diet_id = f"DT{last_diet_num + 1:02d}"
                    last_record_entries = Record.objects.all()
                    last_record_num = 0
                    for entry in last_record_entries:
                        match = re.match(r'RE(\d+)', entry.record_id)
                        if match:
                            num = int(match.group(1))
                            if num > last_record_num:
                                last_record_num = num
                    new_record_id = f"RE{last_record_num + 1:02d}"
                    diet_plan = generate_diet_plan(goal, latest_assessment)
                    new_diet = Diet.objects.create(
                        diet_id=new_diet_id,
                        customer=customer,
                        assessment=latest_assessment,
                        calories=diet_plan['calories'],
                        protein_grams=diet_plan['protein_grams'],
                        fat_grams=diet_plan['fat_grams'],
                        carb_grams=diet_plan['carb_grams'],
                        water_liters=diet_plan['water_liters'],
                        week_start_date=date.today()
                    )
                    new_plan = WorkoutPlan.objects.create(
                        plan_id=new_plan_id,
                        customer=customer,
                        assessment=latest_assessment,
                        goal=goal,
                        week_start_date=date.today(),
                        workout_split=workout_plan_data['workout_split'],
                        mon_exercises=','.join(ex['name'] for ex in daily_exercises['mon']),
                        tue_exercises=','.join(ex['name'] for ex in daily_exercises['tue']),
                        wed_exercises=','.join(ex['name'] for ex in daily_exercises['wed']),
                        thu_exercises=','.join(ex['name'] for ex in daily_exercises['thu']),
                        fri_exercises=','.join(ex['name'] for ex in daily_exercises['fri']),
                        sat_exercises=','.join(ex['name'] for ex in daily_exercises['sat']),
                        sun_exercises=','.join(ex['name'] for ex in daily_exercises['sun'])
                    )
                    Record.objects.create(
                        record_id=new_record_id,
                        customer=customer,
                        goal=goal,
                        plan_id=new_plan,
                        diet_id=new_diet
                    )
                    return JsonResponse({'status': 'success', 'message': 'Workout and diet plan created'})
            except Exception as e:
                logger.error(f"Error saving workout or diet plan: {str(e)}")
                return JsonResponse({'status': 'error', 'message': str(e)})

    context = {
        'customer': customer,
        'show_goal_form': show_goal_form,
        'workout_split': workout_split,
        'day_exercises': day_exercises,
        'exercise_weights': exercise_weights,
        'history_data': history_data
    }
    return render(request, 'cu_exercise.html', context)

@login_required
def SaveWeights(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    login_id = request.session.get('login_id')
    if not login_id or request.session.get('user_type') != 'Customer':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'})
    
    try:
        customer = Customer.objects.get(customer_id=login_id)
        exercise_name = request.POST.get('exercise_name')
        exercise = Exercise.objects.get(exercise_name=exercise_name)
        set_1_weight = request.POST.get('set_1_weight')
        set_2_weight = request.POST.get('set_2_weight')
        set_3_weight = request.POST.get('set_3_weight')
        comment = request.POST.get('comment')
        
        last_weight_entries = ExerciseWeight.objects.all()
        last_weight_num = 0
        for entry in last_weight_entries:
            match = re.match(r'WT(\d+)', entry.weight_id)
            if match:
                num = int(match.group(1))
                if num > last_weight_num:
                    last_weight_num = num
        new_weight_id = f"WT{last_weight_num + 1:02d}"
        
        ExerciseWeight.objects.create(
            weight_id=new_weight_id,
            customer=customer,
            exercise=exercise,
            set_1_weight=float(set_1_weight) if set_1_weight else None,
            set_2_weight=float(set_2_weight) if set_2_weight else None,
            set_3_weight=float(set_3_weight) if set_3_weight else None,
            comment=comment or None,
            date=date.today()
        )
        return JsonResponse({'status': 'success', 'message': 'Weights saved'})
    except Exception as e:
        logger.error(f"Error saving weights: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})@login_required
def save_weights(request):
    if request.method == 'POST':
        try:
            login_id = request.session.get('login_id')
            user_type = request.session.get('user_type')
            if not login_id or user_type != 'Customer':
                return JsonResponse({'status': 'error', 'message': 'Unauthorized access. Login as customer.'})
            customer = Customer.objects.filter(customer_id=login_id).first()
            if not customer:
                return JsonResponse({'status': 'error', 'message': 'Customer not found for logged-in user.'})
            exercise_name = request.POST.get('exercise_name')
            set_1_weight = float(request.POST.get('set_1_weight') or 0)
            set_2_weight = float(request.POST.get('set_2_weight') or 0)
            set_3_weight = float(request.POST.get('set_3_weight') or 0)
            comment = request.POST.get('comment', '') or None
            ex_obj = Exercise.objects.filter(exercise_name=exercise_name).first()
            if not ex_obj:
                return JsonResponse({'status': 'error', 'message': 'Exercise not found'})
            today = date.today()
            existing = ExerciseWeight.objects.filter(
                customer=customer,
                exercise=ex_obj,
                date=today
            ).first()
            if existing:
                existing.set_1_weight = set_1_weight
                existing.set_2_weight = set_2_weight
                existing.set_3_weight = set_3_weight
                existing.comment = comment
                existing.save()
            else:
                last_entries = ExerciseWeight.objects.all()
                last_num = 0
                for entry in last_entries:
                    match = re.match(r'WT(\d+)', entry.weight_id)
                    if match:
                        num = int(match.group(1))
                        if num > last_num:
                            last_num = num
                new_weight_id = f"WT{last_num + 1:02d}"
                ExerciseWeight.objects.create(
                    weight_id=new_weight_id,
                    customer=customer,
                    exercise=ex_obj,
                    date=today,
                    set_1_weight=set_1_weight,
                    set_2_weight=set_2_weight,
                    set_3_weight=set_3_weight,
                    comment=comment
                )
            return JsonResponse({'status': 'success', 'message': 'Weights saved'})
        except Exception as e:
            logger.error(f"Error saving weights: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

logger = logging.getLogger(__name__)

@login_required
def CU_Diet(request):
    login_id = request.session.get('login_id')
    user_type = request.session.get('user_type')

    if not login_id or user_type != "Customer":
        logger.warning(f"Unauthorized access: login_id={login_id}, user_type={user_type}")
        return render(request, 'main/error.html', {'message': 'Unauthorized access or session expired.'})

    customer = get_object_or_404(Customer, customer_id=login_id)
    today = date.today()

    latest_assessment = Assessment.objects.filter(customer_id=customer).order_by('-date').first()
    diet_plan = Diet.objects.filter(customer=customer, assessment=latest_assessment).first() if latest_assessment else None

    if not diet_plan:
        return render(request, 'cu_diet.html', {
            'customer': customer,
            'diet_plan': None,
            'show_create_plan_message': True
        })

    if request.method == 'POST':
        try:
            calories = float(request.POST.get('calories', 0))
            protein = float(request.POST.get('protein_grams', 0))
            fat = float(request.POST.get('fat_grams', 0))
            carbs = float(request.POST.get('carb_grams', 0))
            water = float(request.POST.get('water_liters', 0))

            existing_intake = DailyIntake.objects.filter(
                customer=customer,
                diet=diet_plan,
                date=today
            ).first()

            if existing_intake:
                existing_intake.calories += calories
                existing_intake.protein_grams += protein
                existing_intake.fat_grams += fat
                existing_intake.carb_grams += carbs
                existing_intake.water_liters += water
                existing_intake.save()
            else:
                last_entries = DailyIntake.objects.all()
                last_num = 0
                for entry in last_entries:
                    match = re.match(r'IN(\d+)', entry.intake_id)
                    if match:
                        num = int(match.group(1))
                        if num > last_num:
                            last_num = num
                new_intake_id = f"IN{last_num + 1:02d}"

                DailyIntake.objects.create(
                    intake_id=new_intake_id,
                    customer=customer,
                    diet=diet_plan,
                    date=today,
                    calories=calories,
                    protein_grams=protein,
                    fat_grams=fat,
                    carb_grams=carbs,
                    water_liters=water
                )

            return JsonResponse({
                'status': 'success',
                'message': 'Intake submitted successfully',
                'totals': {
                    'calories': existing_intake.calories if existing_intake else calories,
                    'protein': existing_intake.protein_grams if existing_intake else protein,
                    'fat': existing_intake.fat_grams if existing_intake else fat,
                    'carbs': existing_intake.carb_grams if existing_intake else carbs,
                    'water': existing_intake.water_liters if existing_intake else water
                }
            })
        except Exception as e:
            logger.error(f"Error processing intake: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    # Get today's intake for display
    today_intake = DailyIntake.objects.filter(customer=customer, diet=diet_plan, date=today).first()

    # Nutrient display structure
    nutrients = [
        {
            "label": "Calories", "name": "calories",
            "target": diet_plan.calories,
            "actual": today_intake.calories if today_intake else 0,
            "remaining": diet_plan.calories - (today_intake.calories if today_intake else 0),
            "input_type": "number"
        },
        {
            "label": "Protein (g)", "name": "protein_grams",
            "target": diet_plan.protein_grams,
            "actual": today_intake.protein_grams if today_intake else 0,
            "remaining": diet_plan.protein_grams - (today_intake.protein_grams if today_intake else 0),
            "input_type": "number"
        },
        {
            "label": "Fat (g)", "name": "fat_grams",
            "target": diet_plan.fat_grams,
            "actual": today_intake.fat_grams if today_intake else 0,
            "remaining": diet_plan.fat_grams - (today_intake.fat_grams if today_intake else 0),
            "input_type": "number"
        },
        {
            "label": "Carbs (g)", "name": "carb_grams",
            "target": diet_plan.carb_grams,
            "actual": today_intake.carb_grams if today_intake else 0,
            "remaining": diet_plan.carb_grams - (today_intake.carb_grams if today_intake else 0),
            "input_type": "number"
        },
        {
            "label": "Water (L)", "name": "water_liters",
            "target": diet_plan.water_liters,
            "actual": today_intake.water_liters if today_intake else 0,
            "remaining": diet_plan.water_liters - (today_intake.water_liters if today_intake else 0),
            "input_type": "number"
        }
    ]

    # Build graph data for the last 7 days
    week_dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    week_data = DailyIntake.objects.filter(customer=customer, diet=diet_plan, date__in=week_dates).order_by('date')
    graph_data = []
    for d in week_dates:
        intake = next((i for i in week_data if i.date == d), None)
        graph_data.append({
            "date": d.strftime("%d %b"),  # e.g., "20 Jun"
            "calories": intake.calories if intake else 0,
            "protein": intake.protein_grams if intake else 0,
            "fat": intake.fat_grams if intake else 0,
            "carbs": intake.carb_grams if intake else 0,
            "water": intake.water_liters if intake else 0
        })

    context = {
        'customer': customer,
        'diet_plan': diet_plan,
        'show_create_plan_message': False,
        'nutrients': nutrients,
        'graph_data': graph_data
    }
    return render(request, 'cu_diet.html', context)

@csrf_exempt
def get_nutrition_info(request):
    try:
        data = json.loads(request.body)
        prompt = data.get("prompt", "")

        refined_prompt = f"""
        You are a nutrition expert. Provide approximate nutritional values for the specified food and quantity.
        The output must be a valid JSON object with the following keys: 
        {{"calories": float, "protein": float, "fat": float, "carbs": float}}
        Values should be in kcal for calories, grams for protein, fat, and carbs, and liters for water.
        If the food is a complex dish, estimate based on common ingredients.
        Food: {prompt}
        Ensure the output is only the JSON object, no extra text or formatting.
        """

        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': settings.GOOGLE_AI_API_KEY
        }
        payload = {
            'contents': [{
                'parts': [{'text': refined_prompt}]
            }]
        }

        response = requests.post(
            'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent',
            headers=headers,
            json=payload,
            timeout=20
        )

        if response.status_code == 200:
            content = response.json()['candidates'][0]['content']['parts'][0]['text']
            logger.info(f"Gemini response: {content}")
            content = content.strip()
            if content.startswith('```json') and content.endswith('```'):
                content = content[7:-3].strip()
            nutrition = json.loads(content)
            return JsonResponse(nutrition)
        else:
            logger.error(f"Gemini API error {response.status_code}: {response.text}")
            return JsonResponse({"error": "Failed to fetch nutrition data from Gemini API"}, status=500)

    except json.JSONDecodeError:
        logger.error(f"Failed to parse Gemini response: {content}")
        return JsonResponse({"error": "Invalid response format from nutrition API"}, status=500)
    except Exception as e:
        logger.exception(f"Error in get_nutrition_info: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def save_intake(request):
    if request.method == 'POST':
        try:
            login_id = request.session.get('login_id')
            user_type = request.session.get('user_type')

            if not login_id or user_type != "Customer":
                return JsonResponse({'status': 'error', 'message': 'Unauthorized access. Login as customer.'})

            customer = get_object_or_404(Customer, customer_id=login_id)
            diet_plan = Diet.objects.filter(customer=customer).order_by('-week_start_date').first()
            if not diet_plan:
                return JsonResponse({'status': 'error', 'message': 'No diet plan found.'})

            calories = float(request.POST.get('calories', 0))
            protein = float(request.POST.get('protein', 0))
            fat = float(request.POST.get('fat', 0))
            carbs = float(request.POST.get('carbs', 0))
            water = float(request.POST.get('water', 0))

            today = date.today()
            existing_intake = DailyIntake.objects.filter(
                customer=customer,
                diet=diet_plan,
                date=today
            ).first()

            if existing_intake:
                existing_intake.calories += calories
                existing_intake.protein_grams += protein
                existing_intake.fat_grams += fat
                existing_intake.carb_grams += carbs
                existing_intake.water_liters += water
                existing_intake.save()
            else:
                last_entries = DailyIntake.objects.all()
                last_num = 0
                for entry in last_entries:
                    match = re.match(r'IN(\d+)', entry.intake_id)
                    if match:
                        num = int(match.group(1))
                        if num > last_num:
                            last_num = num
                new_intake_id = f"IN{last_num + 1:02d}"

                DailyIntake.objects.create(
                    intake_id=new_intake_id,
                    customer=customer,
                    diet=diet_plan,
                    date=today,
                    calories=calories,
                    protein_grams=protein,
                    fat_grams=fat,
                    carb_grams=carbs,
                    water_liters=water
                )

            return JsonResponse({
                'status': 'success',
                'message': 'Intake saved successfully',
                'totals': {
                    'calories': existing_intake.calories if existing_intake else calories,
                    'protein': existing_intake.protein_grams if existing_intake else protein,
                    'fat': existing_intake.fat_grams if existing_intake else fat,
                    'carbs': existing_intake.carb_grams if existing_intake else carbs,
                    'water': existing_intake.water_liters if existing_intake else water
                }
            })
        except Exception as e:
            logger.error(f"Error saving intake: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})