# Generated by Django 5.1.5 on 2025-06-19 19:26

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0031_alter_intake_intake_id_alter_intake_protein_grams'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyIntake',
            fields=[
                ('intake_id', models.CharField(max_length=4, primary_key=True, serialize=False)),
                ('date', models.DateField(default=datetime.date.today)),
                ('calories', models.FloatField(default=0)),
                ('protein_grams', models.FloatField(default=0)),
                ('fat_grams', models.FloatField(default=0)),
                ('carb_grams', models.FloatField(default=0)),
                ('water_liters', models.FloatField(default=0)),
                ('customer', models.ForeignKey(db_column='customer_id', on_delete=django.db.models.deletion.CASCADE, to='main.customer')),
                ('diet', models.ForeignKey(db_column='diet_id', on_delete=django.db.models.deletion.CASCADE, to='main.diet')),
            ],
            options={
                'db_table': 'tbl_daily_intake',
                'unique_together': {('customer', 'diet', 'date')},
            },
        ),
        migrations.DeleteModel(
            name='Intake',
        ),
    ]
