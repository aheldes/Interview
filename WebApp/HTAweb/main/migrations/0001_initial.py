# Generated by Django 4.0.4 on 2022-06-18 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Substance',
            fields=[
                ('id', models.IntegerField(db_column='id', primary_key=True, serialize=False)),
                ('substance', models.CharField(db_column='Substance', max_length=255)),
            ],
            options={
                'db_table': 'SUBSTANCE',
                'managed': False,
            },
        ),
    ]