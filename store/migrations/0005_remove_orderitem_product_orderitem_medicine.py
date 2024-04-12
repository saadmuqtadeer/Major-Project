# Generated by Django 4.2.7 on 2024-04-10 16:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_remove_medicine_image_url_medicine_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='product',
        ),
        migrations.AddField(
            model_name='orderitem',
            name='medicine',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.medicine'),
        ),
    ]
