from django.contrib import admin
from .models import (
    Login, TrainerCategory, Trainer, Session, Customer, Payment,
    Assessment, Booking, Exercise, WorkoutPlan, ExerciseWeight,
    Diet, Record, DailyIntake
)

@admin.register(Login)
class LoginAdmin(admin.ModelAdmin):
    list_display = ("login_id", "username", "user_type", "status")
    search_fields = ("username",)
    list_filter = ("user_type", "status")
    readonly_fields = ("login_id",)

@admin.register(TrainerCategory)
class TrainerCategoryAdmin(admin.ModelAdmin):
    list_display = ("cat_id", "category_name", "category_desc", "category_payment")
    search_fields = ("category_name",)
    readonly_fields = ("cat_id",)

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ("trainer_id", "trainer_name", "cat_id", "trainer_age", "trainer_email", "trainer_expertise", "trainer_status")
    search_fields = ("trainer_name", "trainer_email")
    list_filter = ("cat_id", "trainer_status")
    readonly_fields = ("trainer_id",)

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "trainer_id", "time_slot", "session_status")
    list_filter = ("session_status",)
    readonly_fields = ("session_id",)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "customer_name", "customer_email", "customer_phone", "cat_id", "join_date", "last_payment_date", "customer_status")
    search_fields = ("customer_name", "customer_email", "customer_phone")
    list_filter = ("cat_id", "customer_status", "last_payment_date")
    ordering = ("customer_id",)
    list_editable = ("last_payment_date", "join_date")
    readonly_fields = ("customer_id",)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "customer_id", "payment_date", "amount")
    search_fields = ("payment_id", "customer_id__customer_name")
    list_filter = ("payment_date", "amount")
    ordering = ("payment_id",)
    list_editable = ("payment_date",)
    readonly_fields = ("payment_id",)

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("assessment_id", "customer_id", "height", "weight", "muscle_mass", "fat_mass", "date")
    search_fields = ("assessment_id", "customer_id__customer_name")
    list_filter = ("date",)
    readonly_fields = ("assessment_id",)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("booking_id", "session_id", "customer_id", "booking_date")
    search_fields = ("booking_id", "customer_id__customer_name", "session_id__session_id")
    list_filter = ("booking_date",)
    readonly_fields = ("booking_id",)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("exercise_id", "exercise_name", "exercise_type", "target_muscle", "trainer")
    search_fields = ("exercise_name", "trainer__trainer_name")
    list_filter = ("exercise_type", "target_muscle", "trainer")
    readonly_fields = ("exercise_id",)

@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = (
        "plan_id", "customer", "goal", "week_start_date", "workout_split",
        "short_mon", "short_tue", "short_wed", "short_thu",
        "short_fri", "short_sat", "short_sun"
    )
    search_fields = ("customer__customer_name", "goal", "workout_split")
    list_filter = ("goal", "week_start_date")
    readonly_fields = ("plan_id",)

    def short_mon(self, obj): return obj.mon_exercises[:10] + "..." if obj.mon_exercises else "Rest"
    def short_tue(self, obj): return obj.tue_exercises[:10] + "..." if obj.tue_exercises else "Rest"
    def short_wed(self, obj): return obj.wed_exercises[:10] + "..." if obj.wed_exercises else "Rest"
    def short_thu(self, obj): return obj.thu_exercises[:10] + "..." if obj.thu_exercises else "Rest"
    def short_fri(self, obj): return obj.fri_exercises[:10] + "..." if obj.fri_exercises else "Rest"
    def short_sat(self, obj): return obj.sat_exercises[:10] + "..." if obj.sat_exercises else "Rest"
    def short_sun(self, obj): return obj.sun_exercises[:10] + "..." if obj.sun_exercises else "Rest"

    short_mon.short_description = "Mon"
    short_tue.short_description = "Tue"
    short_wed.short_description = "Wed"
    short_thu.short_description = "Thu"
    short_fri.short_description = "Fri"
    short_sat.short_description = "Sat"
    short_sun.short_description = "Sun"

@admin.register(ExerciseWeight)
class ExerciseWeightAdmin(admin.ModelAdmin):
    list_display = ("weight_id", "customer", "exercise", "date", "weight_summary", "short_comment")
    search_fields = ("customer__customer_name", "exercise__exercise_name", "comment")
    list_filter = ("date", "exercise")
    list_editable = ("date",)
    readonly_fields = ("weight_id",)

    def weight_summary(self, obj):
        w = []
        if obj.set_1_weight: w.append(f"S1:{obj.set_1_weight}kg")
        if obj.set_2_weight: w.append(f"S2:{obj.set_2_weight}kg")
        if obj.set_3_weight: w.append(f"S3:{obj.set_3_weight}kg")
        return ", ".join(w) if w else "No weights"
    weight_summary.short_description = "Sets"

    def short_comment(self, obj):
        return (obj.comment[:30] + "...") if obj.comment and len(obj.comment) > 30 else obj.comment
    short_comment.short_description = "Comment"

@admin.register(Diet)
class DietAdmin(admin.ModelAdmin):
    list_display = ("diet_id", "customer", "week_start_date", "calories", "protein_grams", "carb_grams", "fat_grams", "water_liters")
    search_fields = ("customer__customer_name",)
    list_filter = ("week_start_date",)
    readonly_fields = ("diet_id",)

@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ("record_id", "customer", "goal", "plan_id", "diet_id", "diet_summary")
    search_fields = ("customer__customer_name", "goal")
    list_filter = ("goal",)
    readonly_fields = ("record_id",)

    def diet_summary(self, obj):
        if obj.diet_id:
            return f"{obj.diet_id.calories} kcal, {obj.diet_id.protein_grams}g P, {obj.diet_id.carb_grams}g C, {obj.diet_id.fat_grams}g F"
        return "No Diet"

@admin.register(DailyIntake)
class DailyIntakeAdmin(admin.ModelAdmin):
    list_display = ("intake_id", "customer", "diet", "date", "calories", "protein_grams", "fat_grams", "carb_grams", "water_liters")
    search_fields = ("customer__customer_name",)
    list_filter = ("date", "customer")
    ordering = ("-date",)
    readonly_fields = ("intake_id",)
