from django.db import migrations
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify


def migrate_data(apps, schemaeditor):
    Category = apps.get_model("scoring", "Category")
    SubCategory = apps.get_model("scoring", "SubCategory")

    new_category = Category.objects.create(
        name="CSRD",
        slug=slugify("CSRD"),
        weight_index=1,
        color="#000000",
        order=100,
    )

    for i in range(1, 18):
        subcat_name = "S1-" + str(i)
        subcategory = SubCategory.objects.create(
            name=subcat_name,
            name_fr=subcat_name,
            short_name=subcat_name,
            slug=slugify(subcat_name),
            order=i,
        )
        subcategory.categories.add(new_category)
        subcategory.save()


class Migration(migrations.Migration):
    dependencies = [
        ("scoring", "0438_import_collaborateurs360_v54"),
    ]

    operations = [migrations.RunPython(migrate_data, lambda x, y: None)]
