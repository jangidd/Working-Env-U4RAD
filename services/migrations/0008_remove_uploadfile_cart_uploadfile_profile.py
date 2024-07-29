# Generated by Django 4.2.14 on 2024-07-25 09:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0007_uploadfile"),
    ]

    operations = [
        migrations.RemoveField(model_name="uploadfile", name="cart",),
        migrations.AddField(
            model_name="uploadfile",
            name="profile",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="uploads",
                to="services.profile",
            ),
        ),
    ]
