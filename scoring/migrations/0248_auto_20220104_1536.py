from django.db import migrations, models
from django.core.exceptions import ImproperlyConfigured

try:
    from cloudinary_storage.storage import RawMediaCloudinaryStorage

    RawStorage = RawMediaCloudinaryStorage()
except ImproperlyConfigured:
    from django.core.files.storage import FileSystemStorage

    RawStorage = FileSystemStorage()


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0247_merge_20211217_1620"),
    ]

    operations = [
        migrations.AlterField(
            model_name="evaluation",
            name="pdf_sheet",
            field=models.FileField(
                blank=True,
                null=True,
                storage=RawStorage,
                upload_to="pdf_sheets/",
                verbose_name="Fiche entreprise",
            ),
        ),
        migrations.AlterField(
            model_name="evaluation",
            name="pdf_sheet_en",
            field=models.FileField(
                blank=True,
                null=True,
                storage=RawStorage,
                upload_to="pdf_sheets/",
                verbose_name="Fiche entreprise",
            ),
        ),
        migrations.AlterField(
            model_name="evaluation",
            name="pdf_sheet_fr",
            field=models.FileField(
                blank=True,
                null=True,
                storage=RawStorage,
                upload_to="pdf_sheets/",
                verbose_name="Fiche entreprise",
            ),
        ),
        migrations.AlterField(
            model_name="evaluation",
            name="questions_sheet",
            field=models.FileField(
                blank=True,
                null=True,
                storage=RawStorage,
                upload_to="questions_sheets/",
                verbose_name="Questionnaire",
            ),
        ),
        migrations.AlterField(
            model_name="questionsheet",
            name="export",
            field=models.FileField(
                blank=True,
                null=True,
                storage=RawStorage,
                upload_to="sheets/",
                verbose_name="Export",
            ),
        ),
    ]
