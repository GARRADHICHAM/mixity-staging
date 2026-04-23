import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase as DjangoTestCase
from django.utils.text import slugify
from django.apps import apps
from django.utils import timezone
from accounts.models import (
    Structure,
    MixityUser,
    Membership,
    BusinessLine,
    Entity,
    EntityLevel,
)
from act.models import Solver, SolutionKeyword, Solution
from mixity.models import Language
from mixity.utils import HiddenPrints
from scoring.importsheets import import_20240527_1005
from scoring.models import (
    SubCategory,
    Category,
    QuestionSheet,
    QuestionSheetType,
    Evaluation,
)
from django.conf import settings
from subscriptions.models import (
    SubscriptionType,
    Subscription,
    SubscriptionOption,
    SubscriptionPack,
    Product,
)
from lead.models import Objective, LeadAction, ActionKpi, GenericKpi


def make_sheet(slug_type, name, file_path):
    if slug_type == "evaluation_collaborateurs_360":
        sheet_type = QuestionSheetType.objects.create(
            slug=slug_type,
            name=name,
            is_collaborator=True,
        )
    else:
        sheet_type = QuestionSheetType.objects.create(
            slug=slug_type,
            name=name,
        )
    file = os.path.join(
        settings.STATICFILES_DIRS[0],
        file_path,
    )
    with HiddenPrints():
        import_20240527_1005.import_questions(apps, file, slug_type)
    sheet = QuestionSheet.objects.first()
    sheet_return = (sheet, sheet_type)

    return sheet_return


class TestCase(DjangoTestCase):
    """
    All Mixity test classes must inherit from this class.

    Usage:
        class MyTest(TestCase):
            @classmethod
            def setUpClass(cls):
                cls.make_categories()
    """

    # Categories
    @classmethod
    def make_categories(cls):
        # Categories and Subcategories
        categories = [
            (
                "Transversal",
                "all",
                [
                    "Sensibilisation",
                    "Gouvernance",
                    "Qualité de vie au travail",
                    "Carrière",
                    "Recrutement",
                ],
            ),
            (
                "Genre",
                "gender",
                [
                    "Rémunération et avantages",
                    "Formation",
                    "Promotion",
                    "Mixité des métiers",
                    "Articulation des temps de vie",
                    "Communication",
                    "Gouvernance",
                    "Recrutement",
                    "Sensibilisation",
                    "Carrière",
                    "Qualité de vie au travail",
                ],
            ),
            (
                "Handicap",
                "disability",
                [
                    "Partenariat",
                    "Communication",
                    "Achats",
                    "Gouvernance",
                    "Conditions de travail",
                    "Recrutement",
                    "Formation",
                    "Sensibilisation",
                    "Qualité de vie au travail",
                    "Carrière",
                ],
            ),
            (
                "Origines",
                "cultural_diversity",
                [
                    "Partenariat",
                    "Achats",
                    "Articulation des temps de vie",
                    "Communication",
                    "Gouvernance",
                    "Sensibilisation",
                    "Qualité de vie au travail",
                    "Carrière",
                    "Recrutement",
                    "Rémunération et avantages",
                    "Formation",
                ],
            ),
            (
                "Générations",
                "generational_diversity",
                [
                    "Formation",
                    "Recrutement",
                    "Carrière",
                    "Qualité de vie au travail",
                    "Sensibilisation",
                    "Management",
                    "Conditions de travail",
                    "Gouvernance",
                ],
            ),
            (
                "LGBTQIA+",
                "lgbt",
                [
                    "Carrière",
                    "Communication",
                    "Sensibilisation",
                    "Recrutement",
                    "Gouvernance",
                    "Qualité de vie au travail",
                    "Rémunération et avantages",
                    "Articulation des temps de vie",
                ],
            ),
            ("Vos suggestions", "your-suggestions", ["Gouvernance"]),
        ]

        subcategories_slugs = {
            "Achats": ["purchases", 0],
            "Articulation des temps de vie": ["life-articulation", 1],
            "Sensibilisation": ["awareness", 2],
            "Carrière": ["career-development", 3],
            "Conditions de travail": ["working-conditions", 4],
            "Gouvernance": ["governance", 5],
            "Management": ["management", 6],
            "Mixité des métiers": ["diversity-in-professions", 7],
            "Partenariat": ["partnerships", 8],
            "Promotion": ["promotion", 1],
            "Qualité de vie au travail": ["work-life-balance", 9],
            "Recrutement": ["recruitment", 10],
            "Rémunération et avantages": ["remuneration-and-benefits", 11],
            "Formation": ["training", 12],
            "Communication": ["communication", 13],
        }

        for i in range(len(categories)):
            # Categories
            current_cat = Category.objects.create(
                name=categories[i][0],
                slug=categories[i][1],
                order=i + 1,
                weight_index=1.00,
            )
            # Subcategories
            current_subcategories = categories[i][2]
            for j in range(len(current_subcategories)):
                current_sub_cat_slug = subcategories_slugs[current_subcategories[j]]
                subcat, created = SubCategory.objects.get_or_create(
                    name=current_subcategories[j],
                    short_name=current_subcategories[j][0:14],
                    order=current_sub_cat_slug[1],
                    slug=current_sub_cat_slug[0],
                )
                subcat.categories.add(current_cat)
                subcat.save()

    # Sheet
    @classmethod
    def make_sheet_human(cls, name, file_path):
        slug_type = "evaluation_collaborateurs_360"
        return make_sheet(slug_type, name, file_path)

    @classmethod
    def make_sheet_diag(cls, name, file_path):
        slug_type = "mixity_evaluation_diag"
        return make_sheet(slug_type, name, file_path)

    @classmethod
    def make_sheet_international(cls):
        # TODO
        pass

    @classmethod
    def make_sheet_global(cls, name, file_path):
        slug_type = "mixity_evaluation_globale"
        return make_sheet(slug_type, name, file_path)

    @classmethod
    def make_sheet_start(cls, name, file_path):
        slug_type = "mixity_start"
        return make_sheet(slug_type, name, file_path)

    # BusinessLine
    @classmethod
    def make_business_line(cls, slug, name_fr, name_en):
        business_line = BusinessLine.objects.create(
            slug=slug,
            name_fr=name_fr,
            name_en=name_en,
        )
        return business_line

    @classmethod
    def make_evaluation(cls, entity, sheet, subscription):
        evaluation = Evaluation.objects.create(
            entity=entity,
            sheet=sheet,
            subscription=subscription,
        )
        return evaluation

    # Structure
    @classmethod
    def make_structure(cls, juridic_name, slug, workforce, category, business_line):
        s = Structure.objects.create(
            juridic_name=juridic_name,
            slug=slug + "-structure",
            workforce=workforce,
            category=category,
            business_line=business_line,
        )
        return s

    # Entity Level
    @classmethod
    def make_entity_level(cls, s, label, level):
        entity_level = EntityLevel.objects.create(
            label=label,
            structure=s,
            level=level,
        )
        return entity_level

    # Entity
    @classmethod
    def make_entity(cls, name, entity_level, workforce, parent=None):
        entity = Entity.objects.create(
            name=name,
            slug=slugify(name),
            entity_level=entity_level,
            workforce=workforce,
            parent_entity=parent,
        )
        return entity

    # User
    @classmethod
    def make_user(
        cls, email, password, username=None, first_name=None, last_name=None, phone=None
    ):
        if not username:
            if first_name and last_name and phone:
                user = MixityUser.objects.create(
                    email=email,
                    password=password,
                    first_name=first_name,
                    phone=phone,
                    last_name=last_name,
                )
        else:
            user = MixityUser.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
        return user

    @classmethod
    def make_common_user(cls):
        email = "user@user.com"
        password = "user"
        first_name = "user1"
        phone = 12345679
        last_name = "Yee"
        return cls.make_user(
            email, password, first_name=first_name, last_name=last_name, phone=phone
        )

    # Subscription
    @classmethod
    def make_product(cls, label, slug, question_sheet_type):
        if not Product.objects.filter(slug=slug).exists():
            product = Product.objects.create(
                label=label,
                slug=slug,
                question_sheet_type=question_sheet_type,
            )
        else:
            product = Product.objects.get(slug=slug)
        return product

    @classmethod
    def make_subscription_pack(cls, start_date, structure, is_active=True):
        sub_pack = SubscriptionPack.objects.create(
            is_active=is_active,
            start_date=start_date,
            structure=structure,
        )
        return sub_pack

    @classmethod
    def make_subscription_option(cls, sub_pack: SubscriptionPack, product: Product):
        return sub_pack.add_new_option(product)

    @classmethod
    def make_subscription_type(cls, label, pme_label, slug, order, desc, allow_c=None):
        if not allow_c:
            sub = SubscriptionType.objects.create(
                label=label,
                pme_label=pme_label,
                slug=slug,
                order=order,
                description=desc,
                is_active=True,
                allow_structure_evaluation=True,
                allow_public_display=True,
                allow_add_structure_members=True,
            )
        else:
            sub = SubscriptionType.objects.create(
                label=label,
                pme_label=pme_label,
                slug=slug,
                order=order,
                description=desc,
                is_active=True,
                allow_structure_evaluation=True,
                allow_public_display=True,
                allow_add_structure_members=True,
                allow_card_payment=True,
            )

        return sub

    @classmethod
    def make_subscription(
        cls, sheet_type, subscription_type, structure, is_active=True
    ):
        """
        This method creates an active subscription by default
        """
        subscription_type.question_sheet_types.add(sheet_type)
        subscription = Subscription.objects.create(
            is_active=is_active,
            start_date=timezone.now(),
            structure=structure,
            subscription_type=subscription_type,
            question_sheet_type=sheet_type,
        )
        return subscription

    # Membership
    @classmethod
    def make_membership(cls, user, structure):
        Membership.objects.create(structure=structure, user=user, is_owner=True)

    # Membership
    @classmethod
    def make_entity_membership(cls, user, entity):
        Membership.objects.create(entity=entity, user=user, is_owner=True)

    # Objective
    @classmethod
    def make_objective(cls, label, category, subcategory, structure):
        objective = Objective.objects.create(
            label=label,
            category=Category.objects.get(name=category),
            subcategory=SubCategory.objects.get(
                name=subcategory, categories__name=category
            ),
            structure=structure,
        )
        return objective

    # Action
    @classmethod
    def make_action(cls, label, status, budget, referent, objective):
        action = LeadAction.objects.create(
            label=label,
            status=status,
            action_date=timezone.now(),
            budget=budget,
            referent=referent,
            objective=objective,
        )
        return action

    # ActionKpi
    @classmethod
    def make_actionkpi(cls, label, unit, goal, category, subcategory, action):
        kpi = ActionKpi.objects.create(
            label=label,
            unit=unit,
            goal=goal,
            subcategory=SubCategory.objects.get(
                name=subcategory, categories__name=category
            ),
            action=action,
        )
        return kpi

    # GenericKpi
    @classmethod
    def make_generickpi(cls, label, unit, category, subcategory):
        kpi = GenericKpi.objects.create(
            label=label,
            unit=unit,
        )
        kpi.subcategories.add(
            SubCategory.objects.get(name=subcategory, categories__name=category)
        )
        return kpi

    # Solver
    @classmethod
    def make_solver(cls, structure):
        solver = Solver.objects.create(structure=structure)
        return solver

    # Languages
    @classmethod
    def make_language(cls, code, label_fr, label_en, label_es):
        language = Language.objects.create(
            code=code,
            label_fr=label_fr,
            label_en=label_en,
            label_es=label_es,
        )
        return language

    # Keywords
    @classmethod
    def make_keyword(cls, slug, label):
        keyword = SolutionKeyword.objects.create(slug=slug, label=label)
        return keyword

    # Solution
    @classmethod
    def make_solution(
        cls,
        solver,
        title,
        referent,
        email,
        category,
        subcategory,
        summary,
        country,
        region,
        description,
        languages,
        price_desc,
        keywords,
    ):
        solution = Solution.objects.create(
            solver=solver,
            title=title,
            referent=referent,
            email=email,
            summary=summary,
            photo=SimpleUploadedFile(
                name="thumbnail", content=b"content", content_type="image/jpeg"
            ),
            country=country,
            region=region,
            description=description,
            price_desc=price_desc,
        )
        # Setting translated fields to empty string to avoid None encoding problem
        solution.title_en = ""
        solution.title_es = ""
        solution.summary_en = ""
        solution.summary_es = ""
        solution.description_en = ""
        solution.description_es = ""
        solution.price_desc_en = ""
        solution.price_desc_es = ""
        # Setting M2M fields
        solution.categories.set([Category.objects.get(name=category)])
        solution.subcategories.set(
            [SubCategory.objects.get(name=subcategory, categories__name=category)]
        )
        solution.languages.set(languages)
        solution.keywords.set(keywords)
        solution.save()
        return solution
