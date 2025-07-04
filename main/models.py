from django.db import models
from datetime import date
# Create your models here.

#tbl_login
class Login(models.Model):
    login_id = models.CharField(max_length=4, primary_key=True)  # Unique identifier
    username = models.CharField(max_length=20, unique=True)  # Ensures no duplicate usernames
    password = models.CharField(max_length=10)  
    user_type = models.CharField(max_length=8)  # Type of user (Admin, Trainer, Customer)
    status = models.BooleanField(default=True)  # Active (True) / Inactive (False)

    def __str__(self):
        return self.username  # Returns username when object is printed
    class Meta:
        db_table = "tbl_login"  # Set custom table name
    

# tbl_trainer_cat
class TrainerCategory(models.Model):
    cat_id = models.CharField(max_length=4, primary_key=True)  # Unique identifier
    category_name = models.CharField(max_length=20, null=False)  # Name of the category
    category_desc = models.CharField(max_length=50, null=False)  # Description of the category
    category_payment = models.IntegerField(null=False, default=0)  # ✅ Default value added

    def __str__(self):
        return self.category_name  # Returns category name when object is printed

    class Meta:
        db_table = "tbl_trainer_cat"  # Set custom table name


#tbl_trainer
class Trainer(models.Model):
    trainer_id = models.CharField(max_length=4, primary_key=True)
    cat_id = models.ForeignKey(TrainerCategory, on_delete=models.CASCADE)
    trainer_name = models.CharField(max_length=20)
    trainer_age = models.IntegerField()
    trainer_email = models.EmailField(max_length=50, unique=True)
    trainer_expertise = models.CharField(max_length=50)
    trainer_status = models.BooleanField(default=True)  # True = Active, False = Inactive

    def __str__(self):
        return self.trainer_name
    
    class Meta:
        db_table = "tbl_trainer"  # Set custom table name
        

# tbl_session (Trainer Sessions)
class Session(models.Model):
    session_id = models.CharField(max_length=4, primary_key=True)  # Unique identifier
    trainer_id = models.ForeignKey(Trainer, on_delete=models.CASCADE)  # References Trainer
    time_slot = models.TimeField(null=False)  # Time slot for the session
    session_status = models.BooleanField(default=True)  # 1 = Active, 0 = Inactive

    def __str__(self):
        return f"{self.session_id} - {self.trainer_id.trainer_name} - {self.time_slot}"

    class Meta:
        db_table = "tbl_session"  # Set custom table name
 
from django.db import models

#tbl_customer
class Customer(models.Model):
    customer_id = models.CharField(max_length=4, primary_key=True)  # String ID (e.g., CT01, CT02)
    cat_id = models.ForeignKey(TrainerCategory, on_delete=models.CASCADE, db_column="cat_id")  # Foreign Key
    customer_email = models.EmailField(max_length=50, unique=True)
    customer_phone = models.CharField(max_length=10)  # CharField to preserve leading zeros
    customer_name = models.CharField(max_length=50)
    card_name = models.CharField(max_length=50)
    card_number = models.CharField(max_length=16)  # Stored as string to prevent numerical issues
    card_expiry = models.DateField()
    join_date = models.DateField(default=date.today) 
    last_payment_date = models.DateField()
    customer_status = models.BooleanField(default=True)  # ✅ Default value set to Active (True)

    def __str__(self):
        return f"{self.customer_name} ({self.customer_email})"

    class Meta:
        db_table = "tbl_customer"


 #tbl_payment      
class Payment(models.Model):
    payment_id = models.CharField(max_length=4, primary_key=True)  # Unique payment ID
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE)  # References tbl_customer
    payment_date = models.DateField(null=False)  # Date of payment
    amount = models.IntegerField(null=False)  # Payment amount

    def __str__(self):
        return f"Payment {self.payment_id} - {self.customer_id.customer_name}"

    class Meta:
        db_table = "tbl_payment"  # Custom table name
        
#tbl_assessment
class Assessment(models.Model):
    assessment_id = models.CharField(max_length=4, primary_key=True)  # Unique identifier
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column="customer_id")  # Foreign Key
    height = models.IntegerField()  # Height in cm
    weight = models.IntegerField()  # Weight in kg
    muscle_mass = models.IntegerField()  # Muscle mass in kg
    fat_mass = models.IntegerField()  # Fat mass in kg
    date = models.DateField()  # Date of assessment

    def __str__(self):
        return f"Assessment {self.assessment_id} - {self.customer_id.customer_name}"

    class Meta:
        db_table = "tbl_assessment"  # Set custom table name
        
#tbl_booking
class Booking(models.Model):
    booking_id = models.CharField(max_length=4, primary_key=True)  # Unique identifier
    session_id = models.ForeignKey(Session, on_delete=models.CASCADE, db_column="session_id")  # Foreign Key to tbl_session
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column="customer_id")  # Foreign Key to tbl_customer
    booking_date = models.DateField(null=False) 
    
    def __str__(self):
        return f"Booking {self.booking_id} - {self.customer_id.customer_name} - {self.session_id.session_id}"

    class Meta:
        db_table = "tbl_booking"  # Set custom table name
        


# tbl_exercise
class Exercise(models.Model):
    exercise_id = models.CharField(max_length=4, primary_key=True)
    exercise_name = models.CharField(max_length=100)
    trainer = models.ForeignKey('Trainer', on_delete=models.CASCADE, db_column="trainer_id")
    exercise_type = models.CharField(
        max_length=20,
        choices=[
            ('Push', 'Push'),
            ('Pull', 'Pull'),
            ('Legs', 'Legs'),
            ('Cardio', 'Cardio'),
            ('Full Body', 'Full Body'),
            ('Upper', 'Upper'),
            ('Lower', 'Lower')
        ],
        default='Push'  # Default value for existing and new records
    )
    target_muscle = models.CharField(
        max_length=50,
        choices=[
            ('Chest', 'Chest'),
            ('Back', 'Back'),
            ('Shoulders', 'Shoulders'),
            ('Triceps', 'Triceps'),
            ('Biceps', 'Biceps'),
            ('Quads', 'Quads'),
            ('Hamstrings', 'Hamstrings'),
            ('Calves', 'Calves'),
            ('Glutes', 'Glutes'),
            ('Core', 'Core'),
            ('Full Body', 'Full Body')
        ],
        default='Chest'  # Default value for existing and new records
    )

    def __str__(self):
        return f"{self.exercise_name} ({self.exercise_type})"

    class Meta:
        db_table = "tbl_exercise"
        
# tbl_workout_plan
class WorkoutPlan(models.Model):
    plan_id = models.CharField(max_length=4, primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column="customer_id")
    assessment = models.ForeignKey(Assessment, on_delete=models.SET_NULL, null=True, db_column="assessment_id", blank=True)
    goal = models.CharField(max_length=20, choices=[('bulk', 'Bulk'), ('cut', 'Cut'), ('maintenance', 'Maintenance')])
    week_start_date = models.DateField()
    workout_split = models.CharField(max_length=50)
    mon_exercises = models.TextField(blank=True, null=True)
    tue_exercises = models.TextField(blank=True, null=True)
    wed_exercises = models.TextField(blank=True, null=True)
    thu_exercises = models.TextField(blank=True, null=True)
    fri_exercises = models.TextField(blank=True, null=True)
    sat_exercises = models.TextField(blank=True, null=True)
    sun_exercises = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Plan {self.plan_id} - {self.customer.customer_name} - {self.goal}"

    class Meta:
        db_table = "tbl_workout_plan"
        unique_together = ('customer', 'assessment')  # Prevent duplicate plans for same customer and assessment


# tbl_exercise_weight
class ExerciseWeight(models.Model):
    weight_id =  models.CharField(max_length=4, primary_key=True) 
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column="customer_id")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, db_column="exercise_id", null=True, blank=True)  # Made nullable & optional
    set_1_weight = models.FloatField(null=True, blank=True)
    set_2_weight = models.FloatField(null=True, blank=True)
    set_3_weight = models.FloatField(null=True, blank=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(default=date.today)

    def __str__(self):
        return f"Weight {self.weight_id} - {self.customer.customer_name} - {self.exercise.exercise_name if self.exercise else 'No Exercise'}"

    class Meta:
        db_table = "tbl_exercise_weight"
        unique_together = ('customer', 'exercise', 'date')

# tbl_diet
class Diet(models.Model):
    diet_id = models.CharField(max_length=4, primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column="customer_id")
    assessment = models.ForeignKey(Assessment, on_delete=models.SET_NULL, null=True, db_column="assessment_id", blank=True)
    calories = models.IntegerField()
    protein_grams = models.IntegerField()
    fat_grams = models.IntegerField()
    carb_grams = models.IntegerField()
    water_liters = models.FloatField()
    week_start_date = models.DateField()

    def __str__(self):
        return f"Diet {self.diet_id} - {self.customer.customer_name}"

    class Meta:
        db_table = "tbl_diet"
        unique_together = ('customer', 'assessment')

# tbl_records
class Record(models.Model):
    record_id =  models.CharField(max_length=4, primary_key=True) 
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column="customer_id")
    plan_id = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, db_column="plan_id", null=True, blank=True) 
    diet_id = models.ForeignKey(Diet, on_delete=models.CASCADE, db_column="diet_id", null=True, blank=True)
    goal = models.CharField(max_length=50)

    def __str__(self):
        return f"Record {self.record_id} - {self.customer.customer_name} - {self.goal}"

    class Meta:
        db_table = "tbl_records"
        
class DailyIntake(models.Model):
    intake_id = models.CharField(max_length=4, primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column="customer_id")
    diet = models.ForeignKey(Diet, on_delete=models.CASCADE, db_column="diet_id")
    date = models.DateField(default=date.today)
    calories = models.FloatField(default=0)
    protein_grams = models.FloatField(default=0)
    fat_grams = models.FloatField(default=0)
    carb_grams = models.FloatField(default=0)
    water_liters = models.FloatField(default=0)

    def __str__(self):
        return f"Intake {self.intake_id} - {self.customer.customer_name} - {self.date}"

    class Meta:
        db_table = "tbl_daily_intake"
        unique_together = ('customer', 'diet', 'date')