from django.urls import path
from . import views

urlpatterns = [
    
    
    path('Home/', views.Home, name='Home'),
    
    path('Home/Register/', views.Register,name='Register'),
    path('Home/CheckAvailability/', views.CheckAvailability, name='CheckAvailability'),
    path('Home/Payment/', views.Payment_Page,name='Payment_Page'),
    path('Home/Bill/', views.Bill_Page, name='Bill_Page'),  # ✅ Bill page
    path('Home/Bill/Download/<str:payment_id>/', views.Download_Bill, name='Download_Bill'),  # ✅ PDF Download

    path('Home/Topup/', views.Topup,name='topup'),
    path('Home/Login/', views.Login_Page,name='Login'),
    path('Home/Forgot_Password/', views.Forgot_Password, name='Forgot_Password'),
    path('Home/Logout/', views.Logout),

    
    path('Admin/Dashboard/', views.AD_Dashboard),
    path('Admin/Report/', views.Generate_Report, name='Generate_Report'),
    path('Admin/Print/', views.Print_report, name='Print_report'),

    path('Admin/AD_Bills/', views.AD_Bills),
    
    path('Admin/Bill/', views.AD_Bill_Page),  # ✅ Bill page
    path('Admin/Bill/Download/<str:payment_id>/', views.AD_Download_Bill),  # ✅ PDF Download
    
    path('Admin/Trainer_Cat/', views.AD_Trainer_cat),
    path('Admin/Trainer/', views.AD_Trainer),
    path('Admin/GetTrainerDetails/', views.GetTrainerDetails, name='get_trainer_details'),
    path('Admin/Exercise/', views.AD_Exercise),
    path('Admin/Session/', views.AD_Session, name='admin_session'),
    path('Admin/GetTrainerSessions/', views.GetTrainerSessions, name='get_trainer_sessions'),
    path('Admin/Customer/', views.AD_Customer),
    path('Admin/Assessment/', views.AD_Assessment),
    path('Admin/GetLastAssessment/', views.GetLastAssessment, name='GetLastAssessment'),
    path("Admin/EditAssessment/", views.EditAssessment, name="EditAssessment"),
    path('Admin/Booking/', views.AD_Booking),
    path('Admin/Records/', views.AD_Records),
    path('Admin/Analytics/', views.AD_Analytics),
    
    path('Trainer/Dashboard/', views.TR_Dashboard),
    
    path('Trainer/TR_Bills/', views.TR_Bills),
    
    path('Trainer/Bill/', views.TR_Bill_Page),  # ✅ Bill page
    path('Trainer/Bill/Download/<str:payment_id>/', views.TR_Download_Bill),  # ✅ PDF Download
    
    path('Trainer/Trainer_Cat/', views.TR_Trainer_cat),
    path('Trainer/Trainer/', views.TR_Trainer),
    path('Trainer/Exercise/', views.TR_Exercise),
    path('Trainer/Session/', views.TR_Session),
    path('Trainer/Customer/', views.TR_Customer),
    path('Trainer/Assessment/', views.TR_Assessment),
    path('Trainer/Booking/', views.TR_Booking),
    path('Trainer/Records/', views.TR_Records),
    path('Trainer/Analytics/', views.TR_Analytics),
    path('Trainer/Workout/', views.TR_Workout),
    path('Trainer/Diet/', views.TR_Diet),
    
    path('Cust/Dashboard/', views.CU_Dashboard),
    path('Cust/CU_Bills/', views.CU_Bills, name='cu_bills'),
    
    path('Cust/Bill/', views.CU_Bill_Page),  # ✅ Bill page
    path('Cust/Bill/Download/<str:payment_id>/', views.CU_Download_Bill),  # ✅ PDF Download
    
    path('Cust/Trainer_Cat/', views.CU_Trainer_cat),
    path('Cust/Trainer/', views.CU_Trainer),
    path('Cust/Exercise/', views.CU_Exercise),
    path('Cust/SaveWeights/', views.save_weights, name='save_weights'),
    path('Cust/Diet/', views.CU_Diet),
    path('Cust/GetNutrition/', views.get_nutrition_info, name='get_nutrition_info'),
    path('Cust/SaveIntake/', views.save_intake, name='save_intake'),
    path('Cust/Session/', views.CU_Session, name='admin_session'),
    path('Cust/GetTrainerSessions/', views.GetTrainerSessions, name='get_trainer_sessions'),
    path('Cust/Customer/', views.CU_Customer),
    path('Cust/Assessment/', views.CU_Assessment),
    path('Cust/Booking/', views.CU_Booking),
    path('Cust/Records/', views.CU_Records),
    path('Cust/Analytics/', views.CU_Analytics),
    
]
