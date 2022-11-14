# Generated by Django 4.0.4 on 2022-06-18 22:51

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MarketingAuthorisation',
            fields=[
                ('id', models.IntegerField(db_column='ID', primary_key=True, serialize=False)),
                ('category', models.CharField(db_column='Category', max_length=255)),
                ('medicine_name', models.CharField(db_column='Medicine_name', max_length=255)),
                ('therapeutic_area', models.CharField(db_column='Therapeutic_area', max_length=255)),
                ('international_non_proprietary_name', models.CharField(db_column='International_non_proprietary_name', max_length=255)),
                ('active_substance', models.CharField(db_column='Active_substance', max_length=255)),
                ('product_number', models.CharField(db_column='Product_number', max_length=255)),
                ('patient_safety', models.CharField(db_column='Patient_safety', max_length=255)),
                ('authorisation_status', models.CharField(db_column='Authorisation_status', max_length=255)),
                ('ATC_code', models.CharField(db_column='ATC_code', max_length=255)),
                ('additional_monitoring', models.CharField(db_column='Additional_monitoring', max_length=255)),
                ('generic', models.CharField(db_column='Generic', max_length=255)),
                ('biosimilar', models.CharField(db_column='Biosimilar', max_length=255)),
                ('conditional_approval', models.CharField(db_column='Conditional_approval', max_length=255)),
                ('exceptional_circumstances', models.CharField(db_column='Exceptional_circumstances', max_length=255)),
                ('accelerated_assessment', models.CharField(db_column='Accelerated_assessment', max_length=255)),
                ('orphan_medicine', models.CharField(db_column='Orphan_medicine', max_length=255)),
                ('marketing_authorisation_date', models.CharField(db_column='Marketing_authorisation_date', max_length=255)),
                ('refusal_date', models.CharField(db_column='Refusal_date', max_length=255)),
                ('marketing_authorisation_name', models.CharField(db_column='Marketing_authorisation_name', max_length=255)),
                ('human_pharmacotherapeutic_group', models.CharField(db_column='Human_pharmacotherapeutic_group', max_length=255)),
                ('vet_pharmacotherapeutic_group', models.CharField(db_column='Vet_pharmacotherapeutic_group', max_length=255)),
                ('date_of_opinion', models.CharField(db_column='Date_of_opinion', max_length=255)),
                ('decision_date', models.CharField(db_column='Decision_date', max_length=255)),
                ('revision_number', models.CharField(db_column='Revision_number', max_length=255)),
                ('condition_indication', models.CharField(db_column='Condition_indication', max_length=255)),
                ('species', models.CharField(db_column='Species', max_length=255)),
                ('ATCvet_code', models.CharField(db_column='ATCvet_code', max_length=255)),
                ('first_published', models.CharField(db_column='First_published', max_length=255)),
                ('revision_date', models.CharField(db_column='Revision_date', max_length=255)),
                ('url', models.CharField(db_column='URL', max_length=255)),
            ],
            options={
                'db_table': 'MARKETING_AUTHORISATION',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Substance',
            fields=[
                ('id', models.IntegerField(db_column='ID', primary_key=True, serialize=False)),
                ('substance', models.CharField(db_column='Substance', max_length=255)),
            ],
            options={
                'db_table': 'SUBSTANCE',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TherapeuticArea',
            fields=[
                ('id', models.IntegerField(db_column='ID', primary_key=True, serialize=False)),
                ('area', models.CharField(db_column='Area', max_length=255)),
            ],
            options={
                'db_table': 'THERAPEUTIC_AREA',
                'managed': False,
            },
        ),
    ]