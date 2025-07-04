# Generated by Django 5.1.5 on 2025-07-02 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0032_dailyintake_delete_intake'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='exercise_type',
            field=models.CharField(choices=[('Push', 'Push'), ('Pull', 'Pull'), ('Legs', 'Legs'), ('Cardio', 'Cardio'), ('Full Body', 'Full Body'), ('Upper', 'Upper'), ('Lower', 'Lower')], default='Push', max_length=20),
        ),
        migrations.AddField(
            model_name='exercise',
            name='target_muscle',
            field=models.CharField(choices=[('Chest', 'Chest'), ('Back', 'Back'), ('Shoulders', 'Shoulders'), ('Triceps', 'Triceps'), ('Biceps', 'Biceps'), ('Quads', 'Quads'), ('Hamstrings', 'Hamstrings'), ('Calves', 'Calves'), ('Glutes', 'Glutes'), ('Core', 'Core'), ('Full Body', 'Full Body')], default='Chest', max_length=50),
        ),
    ]
