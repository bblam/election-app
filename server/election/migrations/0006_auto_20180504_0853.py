# Generated by Django 2.0.4 on 2018-05-04 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('election', '0005_remove_vote_party'),
    ]

    operations = [
        migrations.AlterField(
            model_name='party',
            name='name',
            field=models.CharField(blank=True, default='Independent', max_length=100, unique=True),
        ),
    ]