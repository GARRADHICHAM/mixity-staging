from django.db import migrations, models

def add_category_and_change_sub_in_every_model(apps, main_subcat, slug):
    Objective = apps.get_model("lead", "Objective")
    ActionKpi = apps.get_model("lead", "ActionKpi")
    GenericKpi = apps.get_model("lead", "GenericKpi")
    Question = apps.get_model("scoring", "Question")
    Aim = apps.get_model("scoring", "Aim")
    Strength = apps.get_model("scoring", "Strength")
    Weakness = apps.get_model("scoring", "Weakness")

    for objective in Objective.objects.filter(subcategory__slug=slug):
        objective.subcategory = main_subcat
        objective.save()
    for kpi in ActionKpi.objects.filter(subcategory__slug=slug):
        if kpi.subcategory:
            kpi.category = kpi.subcategory.category
            kpi.subcategory = main_subcat
            kpi.save()
    for kpi in GenericKpi.objects.all():
        for subcategory in kpi.subcategories.filter(slug=slug):
            kpi.categories.add(subcategory.category)
            kpi.subcategories.add(main_subcat)
            kpi.save()
    for question in Question.objects.filter(subcategory__slug=slug):
        if question.subcategory:
            question.category = question.subcategory.category
            question.subcategory = main_subcat
            question.save()
    for aim in Aim.objects.filter(subcategory__slug=slug):
        if aim.subcategory:
            aim.category = aim.subcategory.category
            aim.subcategory = main_subcat
            aim.save()
    for strength in Strength.objects.filter(subcategory__slug=slug):
        if strength.subcategory:
            strength.category = strength.subcategory.category
            strength.subcategory = main_subcat
            strength.save()
    for weakness in Weakness.objects.filter(subcategory__slug=slug):
        if weakness.subcategory:
            weakness.category = weakness.subcategory.category
            weakness.subcategory = main_subcat
            weakness.save()


def linking_subcat_to_cat(apps, schema_editor):
    subcat_slugs = [
        "purchases",
        "life-articulation",
        "career-development",
        "communication",
        "working-conditions",
        "training",
        "governance",
        "management",
        "diversity-in-professions",
        "partnerships",
        "promotion",
        "work-life-balance",
        "recruitment",
        "remuneration-and-benefits",
        "awareness"
    ]
    Category = apps.get_model("scoring", "Category")
    SubCategory = apps.get_model("scoring", "SubCategory")

    for slug in subcat_slugs:
        subcats = SubCategory.objects.filter(slug=slug).all()
        main_subcat = subcats.first()
        add_category_and_change_sub_in_every_model(apps, main_subcat, slug)
        for category in Category.objects.filter(subcategories__slug=slug):
            if category:
                main_subcat.categories.add(category)
        for sub_cat in subcats[1:]:
            sub_cat.delete()

class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0430_auto_20240307_1600"),
    ]

    operations = [
        migrations.RunPython(linking_subcat_to_cat, lambda x, y: None),
    ]
