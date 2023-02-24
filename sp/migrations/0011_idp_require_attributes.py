# Generated by Django 4.0.5 on 2022-06-15 15:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sp", "0010_auto_20210326_1923"),
    ]

    operations = [
        migrations.AddField(
            model_name="idp",
            name="require_attributes",
            field=models.BooleanField(
                default=True,
                help_text="Ensures the IdP provides attributes on responses.",
            ),
        ),
    ]
