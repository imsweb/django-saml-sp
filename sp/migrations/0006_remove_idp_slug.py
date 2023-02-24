# Generated by Django 3.1.7 on 2021-03-23 15:29

from django.db import migrations


def move_slug(apps, schema_editor):
    IdP = apps.get_model("sp", "IdP")
    db_alias = schema_editor.connection.alias
    for idp in IdP.objects.using(db_alias).all():
        idp.url_params = {"idp_slug": idp.slug}
        idp.save()


class Migration(migrations.Migration):
    dependencies = [
        ("sp", "0005_auto_20210323_1526"),
    ]

    operations = [
        migrations.RunPython(move_slug),
        migrations.RemoveField(
            model_name="idp",
            name="slug",
        ),
    ]
