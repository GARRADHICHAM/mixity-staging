from django.db import migrations

from mixity.models import SolutionFormat


def migrate_data(apps, schemaeditor):

    # Solution Format choices

    solution_format = apps.get_model("mixity", "SolutionFormat")

    solution_format_choices = (
        ("workshop", "Atelier", "Workshop"),
        ("games", "Jeux", "Games"),
        ("conference", "Conférence", "Conference"),
        ("panel-discussion", "Tables rondes", "Panel discussion"),
        ("study", "Étude", "Study"),
        ("tool", "Outil", "Tool"),
        ("support-solution", "Accompagnemet", "Support solution"),
    )

    # Filling solution formats
    for solution_format in solution_format_choices:
        solution_format_slug, solution_format_fr, solution_format_en = solution_format
        SolutionFormat.objects.create(
            slug=solution_format_slug,
            label_fr=solution_format_fr,
            label_en=solution_format_en,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("mixity", "0029_solutionformat_slug"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
