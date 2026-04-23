from django.db import migrations


def migrate_data(apps, schemaeditor):
    # Languages choices
    """
    language pattern = ( label_fr, label_en, label_es, code ISO 639-1°)
    """

    Language = apps.get_model("mixity", "Language")
    solution_language_choices = (
        ("Français", "French", "Francés", "fr"),
        ("Anglais", "English", "inglés", "en"),
        ("Espagnol", "Spanish", "español", "es"),
        ("Allemand", "German", "Alemán", "de"),
        ("Italien", "Italian", "italiano", "it"),
        ("Hollandais", "Dutch", "Holandés", "nl"),
        ("Chinois", "Chinese", "Chino", "zh"),
        ("Russe", "Russian", "ruso", "ru"),
        ("Portugais", "Portuguese", "portugués", "pt"),
        ("Arabe", "Arab", "árabe", "ar"),
        ("Japonais", "Japanese", "japonés", "ja"),
        ("Hindi", "Hindi", "hindi", "hi"),
    )

    # Filling languages
    for language in solution_language_choices:
        lang_label_fr, lang_label_en, lang_label_es, lang_code = language
        Language.objects.create(
            code=lang_code,
            label_fr=lang_label_fr,
            label_en=lang_label_en,
            label_es=lang_label_es,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("mixity", "0021_language"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
