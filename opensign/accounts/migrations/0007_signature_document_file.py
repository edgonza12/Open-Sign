# Generated by Django 5.1.1 on 2024-11-11 03:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_remove_signature_document_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='signature',
            name='document_file',
            field=models.FileField(default=2, upload_to='signed_documents/'),
            preserve_default=False,
        ),
    ]
