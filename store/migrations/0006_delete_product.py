# Generated by Django 4.2.7 on 2024-04-12 06:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_remove_orderitem_product_orderitem_medicine'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Product',
        ),
    ]
