import datetime
import csv
import io
import re

from django.http import JsonResponse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from django.contrib.auth.tokens import default_token_generator
from django.utils.text import slugify
from django_countries import countries
from rest_framework.reverse import reverse

from accounts.mails import (
    send_mail_validation_custom,
    send_invitation_mail,
    send_mail_forgotten_password,
    send_invitation_mail_without_link,
)
from django.utils.encoding import force_bytes, force_str

from accounts.models import (
    MixityUser,
    Membership,
    Structure,
    BusinessLine,
    Entity,
    EntityLevel,
)
from accounts.views import PasswordResetFormAllowNoPassword

from accounts.serializers import BusinessLineSerializer

from mixity.serializers import (
    StructureSerializer,
    EntitySerializer,
    EvaluationSerializer,
    CategorySerializer,
    CollaboratorsStatisticsSerializer,
    ScoreCategorySerializer,
    AssessScoreCategorySerializer,
    AllIndicatorSerializer,
    OneIndicatorSerializer,
)
from lead.serializers import (
    ObjectiveSerializer,
    ActionSerializer,
    KpiSerializer,
    GenericKpiSerializer,
    MixityUserSerializer,
)
from act.serializers import (
    SolutionSerializer,
    SolutionKeywordSerializer,
    LanguageSerializer,
    SolversSerializer,
    SolverSerializer,
    SolutionFormatSerializer,
    BestPracticeSerializer,
    BestPracticeKeywordSerializer,
    BestPracticeTypeSerializer,
    BestPracticePublicSerializer,
    OrganizationTypeSerializer,
    BestPracticeSizeSerializer,
    EntityFavoriteSerializer,
)
from scoring.models import QuestionSheetType, QuestionTag

from subscriptions.models import (
    SubscriptionType,
    Subscription,
    Coupon,
    SubscriptionPack,
    Product,
    SubscriptionOption,
)

from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login

from mixity.utils import encryption
from urllib.parse import unquote_plus


class ApiDashboardRegister(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email").lower().strip()
        password = request.data.get("password")
        subscription = request.data.get("subscription")
        is_newsletter = request.data.get("is_newsletter")

        if not email or not password:
            return Response(
                "Email and password are required", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = MixityUser.objects.create_user(
                username=email,
                email=email,
                password=password,
                is_newsletter=is_newsletter,
            )
            user.save()
            authenticated_user = authenticate(request, email=email, password=password)
            login(request, authenticated_user)
            if subscription == "start":
                send_mail_validation_custom(
                    user, request, "/account/register/start/step2/"
                )
            else:
                send_mail_validation_custom(user, request, "/account/register/step2")
            return Response(
                "POST request processed, Account Registered", status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                "User couldn't be created", status=status.HTTP_400_BAD_REQUEST
            )


class ApiGetUserName(APIView, LoginRequiredMixin):
    def get(self, request, *args, **kwargs):
        user = request.user
        return Response(
            {"first_name": user.first_name, "last_name": user.last_name},
            status=status.HTTP_200_OK,
        )


class ApiUserNewsletter(APIView, LoginRequiredMixin):
    def get(self, request, *args, **kwargs):
        user = request.user
        return Response(
            {"subscribed_to_newsletter": user.is_newsletter},
            status=status.HTTP_200_OK,
        )


class ApiGetEmail(APIView):
    def get(self, request, *args, **kwargs):
        encryption_class = encryption()
        encrypted_email = kwargs.get("encrypted_email")
        email = encryption_class.decrypt_data(
            unquote_plus(encrypted_email.replace("%25", "%"))
        )
        return Response({"email": email}, status=status.HTTP_200_OK)


class ApiGetCompanyName(APIView, LoginRequiredMixin):
    def get(self, request, *args, **kwargs):
        user = request.user

        if user.structures.length > 0:
            structure = user.structures[0]
            return Response(
                {"company": structure.juridic_name},
                status=status.HTTP_200_OK,
            )
        else:
            return Response("User has no structures", status=status.HTTP_404_NOT_FOUND)


class ApiCountriesList(APIView):
    def get(self, request, format=None):
        country_list = [{"code": code, "name": name} for code, name in countries]
        return Response(country_list)


class ApiUploadCollaboratorsCSV(APIView, LoginRequiredMixin):
    def post(self, request, *args, **kwargs):
        try:
            csv_file = request.FILES["file"]
            main_entity_slug = request.POST.get("entity_slug")
            
            if not Entity.objects.filter(slug=main_entity_slug).exists():
                return JsonResponse(
                    {"success": False, "message": "L'entité n'existe pas !"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not csv_file.name.endswith(".csv"):
                return JsonResponse(
                    {"success": False, "message": "Merci d'importer un fichier CSV !"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Lecture du fichier
            data_set = csv_file.read().decode("UTF-8")
            data_set = data_set.replace(";", ",")
            io_string = io.StringIO(data_set)
            header = next(io_string).strip().split(",")

            # Vérification des colonnes attendues
            expected_columns = [
                "first_name",
                "last_name",
                "email",
                "entity_slug",
                "is_owner",
                "is_reader",
            ]
            if header[:6] != expected_columns:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Les colonnes ne correspondent pas, merci d'utiliser la template CSV prévue à cet effet",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Vérification du contenu du fichier (au moins une ligne de données)
            rows = list(csv.reader(io_string, delimiter=","))
            if not rows:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Le fichier CSV doit contenir au moins un collaborateur.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Vérification de la filiation des entités mentionnées dans le fichier
            entity = Entity.objects.get(slug=main_entity_slug)
            structure = entity.entity_level.structure
            children_entities = entity.get_all_children_entities
            valid_entities_list = list(children_entities)
            valid_entities_list.append(entity)
            
            for row in rows:
                csv_entity_slug = row[3].strip()
                
                if not Entity.objects.filter(slug=csv_entity_slug):
                    return JsonResponse(
                        {
                            "success": False,
                            "message": f"Le slug '{csv_entity_slug}' ne correspond à aucune entité. Vérifiez que vous n'avez pas mis le nom de l'entité au lieu de son slug.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                entity_row = Entity.objects.get(slug=csv_entity_slug) 
                
                if not entity_row in valid_entities_list:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": f"Le collaborateur [{row[0]} {row[1]}] semble ne pas être rattaché à l'entité {entity.name}",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Vérification du format des mails
                regex_email = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                email = row[2]
                if not re.match(regex_email, email):
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Le champ email comporte des adresses mails invalides.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                    
                # Vérification du contenu des colonnes is_owner et is_reader
                if row[4].lower() not in ["true", "false"]:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Le champ is_owner ne peut contenir que la mention true ou false",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if row[5].lower() not in ["true", "false"]:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Le champ is_reader ne peut contenir que la mention true ou false",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            # Fin des vérifications

            # Création des collaborateurs
            with transaction.atomic():
                for row in rows:
                    first_name = row[0]
                    last_name = row[1]
                    email = row[2]
                    row_entity_slug = row[3].strip()
                    is_owner = row[4].lower() == "true"
                    is_reader = row[5].lower() == "true"

                    if not MixityUser.objects.filter(username=email).exists():
                        # Création d'un nouveau collaborateur
                        new_collaborator = MixityUser.objects.create(
                            first_name=first_name,
                            last_name=last_name,
                            username=email,
                            email=email,
                        )
                        mail = "send_invitation_mail"
                    elif Membership.objects.filter(user__username=email, entity=entity):
                        new_collaborator = MixityUser.objects.get(username=email)
                        mail = ""
                    else:
                        new_collaborator = MixityUser.objects.get(username=email)
                        mail = "send_invitation_mail_without_link"

                    # Création de l'adhésion
                    if not Membership.objects.filter(
                        user=new_collaborator,
                        entity=Entity.objects.get(slug=row_entity_slug),
                    ):
                        Membership.objects.create(
                            user=new_collaborator,
                            entity=Entity.objects.get(slug=row_entity_slug),
                            structure=structure,
                            is_reader=is_reader,
                            is_owner=is_owner,
                        )

                    from django.contrib.auth.tokens import PasswordResetTokenGenerator

                    token = PasswordResetTokenGenerator().make_token(
                        user=new_collaborator
                    )
                    uid = urlsafe_base64_encode(force_bytes(new_collaborator.pk))
                    if mail == "send_invitation_mail":
                        send_invitation_mail(
                            new_collaborator,
                            request=request,
                            structure=structure,
                            inviter=request.user,
                            uid=uid,
                            token=token,
                        )
                    elif not mail == "":
                        send_invitation_mail_without_link(
                            new_collaborator,
                            request=request,
                            structure=structure,
                            inviter=request.user,
                        )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Les collaborateurs ont été créés avec succès !",
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ApiUploadEntitiesCSV(APIView, LoginRequiredMixin):
    def validate_file(self, csv_file, entity_slug):
        try:
            main_entity = Entity.objects.get(slug=entity_slug)
            structure = main_entity.entity_level.structure

            # Vérification du type de fichier
            if not csv_file.name.endswith(".csv"):
                return JsonResponse(
                    {"success": False, "message": "Merci d'importer un fichier CSV !"},
                    status=400,
                )

            # Vérification que la structure n'a pas encore d'entités en dehors de sa main_entity
            entities = Entity.objects.filter(entity_level__structure=structure)
            if entities.count() > 1:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Cette structure est déjà rattachée à d'autres entités !",
                    },
                    status=400,
                )

            # Lecture du fichier
            data_set = csv_file.read().decode("UTF-8")
            data_set = data_set.replace(";", ",")
            io_string = io.StringIO(data_set)
            header = next(io_string).strip().split(",")

            # Vérification des colonnes attendues
            expected_columns = [
                "name",
                "slug",
                "workforce",
                "entity_level",
                "parent_entity_slug",
                "tag",
            ]
            if header[:6] != expected_columns:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Les colonnes ne correspondent pas, merci d'utiliser la template CSV prévue à cet effet",
                    },
                    status=422,
                )

            # Tri des entités par rapport au champ entity_level pour assurer la création des entités parentes avant la création des entités filles
            rows = csv.reader(io_string, delimiter=",")
            sorted_rows = sorted(rows, key=lambda row: row[3])

            # Intialisation du tableau contenant les parent_entity_slug possible
            entity_slugs = {entity_slug}

            # Vérification de la validité des lignes une à une
            for row in sorted_rows:
                if len(row) < 5:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Le fichier CSV fournit ne correspond pas au format attendu (nombre de colonnes pour chaque ligne)",
                        },
                        status=400,
                    )

                try:
                    workforce = int(row[2])
                except ValueError:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Merci de renseigner l'effectif en chiffres uniquement.",
                        },
                        status=400,
                    )

                try:
                    entity_level = int(row[3])
                except ValueError:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Merci de renseigner le niveau de l'entité en chiffres uniquement.",
                        },
                        status=400,
                    )

                name = row[0]
                slug = row[1]
                parent_entity_slug = row[4].strip()
                tags_names = row[5:]

                if not parent_entity_slug:
                    if slug == entity_slug:
                        # Si l'utilisateur tente de recréer l'entité main alors qu'elle a déjà été créée au moment de la création de la structure, alors on ignore la ligne.
                        continue
                    else:
                        return JsonResponse(
                            {
                                "success": False,
                                "message": f"Les entités rattachées à la structure {structure.juridic_name} doivent être issue de l'entité {entity_slug} ou d'une de ces entités filles !",
                            },
                            status=400,
                        )

                else:
                    if parent_entity_slug not in entity_slugs:
                        return JsonResponse(
                            {
                                "success": False,
                                "message": f"L'entité correspondant au slug {parent_entity_slug} n'existe pas !",
                            },
                            status=400,
                        )

                # Vérification des tags
                for tag_name in tags_names:
                    if (
                        tag_name != ""
                        and not QuestionTag.objects.filter(name=tag_name).exists()
                    ):
                        return JsonResponse(
                            {
                                "success": False,
                                "message": f"Le Tag [{tag_name}] n'existe pas !",
                            },
                            status=404,
                        )

                # Vérification de la correspondance en le parent_entity_level et l'entity_level
                parent_entity_level = 0
                for r in sorted_rows:
                    if r[1] == parent_entity_slug:
                        parent_entity_level = int(r[3])
                        break

                if parent_entity_level != entity_level - 1:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": f"L'entité parent {parent_entity_slug} doit avoir un niveau d'entité de {entity_level - 1} !",
                        },
                        status=400,
                    )

                entity_slugs.add(slug)

            return sorted_rows, structure

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    def post(self, request, *args, **kwargs):
        try:
            # Récupération des variables
            csv_file = request.FILES["file"]
            entity_slug = request.POST.get("entity_slug")

            # Vérifications validité du fichier
            validation_result = self.validate_file(csv_file, entity_slug)
            if isinstance(validation_result, JsonResponse):
                return validation_result
            sorted_rows, structure = validation_result

            # Création des entités ligne par ligne
            for row in sorted_rows:
                name = row[0]
                slug = row[1]
                workforce = int(row[2])
                entity_level = int(row[3])
                parent_entity_slug = row[4]
                tags_names = row[5:]

                if not parent_entity_slug:
                    new_entity = Entity.objects.get(slug=slug)
                else:
                    parent_entity = Entity.objects.get(slug=parent_entity_slug)

                    with transaction.atomic():
                        # Création de l'entity_level
                        (
                            entity_level_instance,
                            created,
                        ) = EntityLevel.objects.get_or_create(
                            structure_id=structure.id, level=entity_level
                        )

                        # Création de la nouvelle entité
                        new_entity = Entity.objects.create(
                            name=name,
                            slug=slug,
                            workforce=workforce,
                            entity_level=entity_level_instance,
                            parent_entity=parent_entity,
                        )

                    # Ajout des tags workforce
                    if workforce < 50:
                        workforce_tag = QuestionTag.objects.get(
                            name="very_small_company"
                        )
                    elif 50 <= workforce < 250:
                        workforce_tag = QuestionTag.objects.get(name="50_250_company")
                    elif 250 <= workforce < 500:
                        workforce_tag = QuestionTag.objects.get(name="small_company")
                    elif 500 <= workforce < 1000:
                        workforce_tag = QuestionTag.objects.get(name="middle_company")
                    elif 1000 <= workforce < 5000:
                        workforce_tag = QuestionTag.objects.get(
                            name="1000_4999_company"
                        )
                    else:
                        workforce_tag = QuestionTag.objects.get(name="5000_company")
                    new_entity.tags.add(workforce_tag)

                # Ajout des tags renseignés
                for tag_name in tags_names:
                    if tag_name:
                        tag = QuestionTag.objects.get(name=tag_name)
                        new_entity.tags.add(tag)

            return JsonResponse(
                {
                    "success": True,
                    "message": "Les entités ont été créées avec succès !",
                },
                status=201,
            )

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)


class ApiCreateStructureWithPack(APIView):
    # Algorithme de LUHN
    def validate_siret(self, siret: str) -> bool:
        if len(siret) != 14 or not siret.isdigit():
            return False

        total = 0
        for i in range(14):
            digit = int(siret[i])
            if i % 2 == 0:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit

        return total % 10 == 0

    def post(self, request, *args, **kwargs):
        user = request.user
        siret_or_duns = request.data.get("siret")
        organisation_name = request.data.get("organisation_name")
        category = request.data.get("category")
        country = request.data.get("country")
        phone = request.data.get("phone")
        activity = request.data.get("activity")
        employees = request.data.get("employees")
        website = request.data.get("website")

        if (
            not siret_or_duns
            or not siret_or_duns.isdigit()
            or len(siret_or_duns) not in [9, 14]
        ):
            return Response(
                {"message": "Merci de renseigner un SIRET ou un DUNS valide !"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(siret_or_duns) == 14 and not self.validate_siret(siret_or_duns):
            return Response(
                {"message": "Le SIRET saisi n'est pas valide !"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            employees = int(employees)
        except ValueError:
            return Response(
                {
                    "message": "Merci de renseigner un effectif composé uniquement de chiffres."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            structure = Structure.objects.get(
                Q(siret=siret_or_duns) | Q(duns=siret_or_duns)
            )
            return Response(
                {
                    "message": "Une structure correspondant à ce SIRET/DUNS existe déjà !"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Structure.DoesNotExist:
            pass

        business_line = BusinessLine.objects.get(name=activity)

        structure_data = {
            "juridic_name": organisation_name,
            "commercial_name": organisation_name,
            "category": category,
            "country": country,
            "phone1": phone,
            "business_line": business_line,
            "workforce": int(employees),
            "website": website,
            "slug": slugify(organisation_name),
        }

        if len(siret_or_duns) == 14:
            structure_data["siret"] = siret_or_duns
        else:
            structure_data["duns"] = siret_or_duns

        with transaction.atomic():
            structure = Structure.objects.create(**structure_data)

            entity_level = EntityLevel.objects.create(
                label="Groupe", structure=structure, level=0
            )

            entity_name = f"{structure.juridic_name}-main"
            entity_slug = slugify(entity_name)
            entity = Entity.objects.create(
                name=entity_name,
                slug=entity_slug,
                entity_level=entity_level,
                workforce=structure.workforce,
                country=structure.country,
                phone=structure.phone1,
            )

            membership, created = Membership.objects.get_or_create(
                user=user,
                structure=structure,
                entity=entity,
                defaults={"is_owner": True},
            )

            if not created and not membership.is_owner:
                membership.is_owner = True
                membership.save()

            # Ajout des tags workforce
            workforce = structure.workforce

            if workforce < 50:
                workforce_tag = QuestionTag.objects.get(name="very_small_company")
            elif 50 <= workforce < 250:
                workforce_tag = QuestionTag.objects.get(name="50_250_company")
            elif 250 <= workforce < 500:
                workforce_tag = QuestionTag.objects.get(name="small_company")
            elif 500 <= workforce < 1000:
                workforce_tag = QuestionTag.objects.get(name="middle_company")
            elif 1000 <= workforce < 5000:
                workforce_tag = QuestionTag.objects.get(name="1000_4999_company")
            else:
                workforce_tag = QuestionTag.objects.get(name="5000_company")

            structure.tags.add(workforce_tag)
            entity.tags.add(workforce_tag)

            # Ajout des tags pays
            country = structure.country
            try:
                country_tag = QuestionTag.objects.get(name=country.code.lower())
            except QuestionTag.DoesNotExist:
                country_tag = QuestionTag.objects.create(name=country.code.lower())
            if country_tag:
                structure.tags.add(country_tag)
                entity.tags.add(country_tag)

            sub_pack = structure.create_subscriptionPack()

        return Response(
            {
                "pk": structure.pk,
                "entity_slug": entity_slug,
                "message": "La structure a été créée avec succès !",
            },
            status=status.HTTP_200_OK,
        )


class ApiCreateOptions(APIView):
    def post(self, request, *args, **kwargs):
        # On reçoit soit "human", "diag" , "start" ou "pack360" dans product_slug
        product_slug = request.data.get("product")
        structure_id = request.data.get("structure_id")

        try:
            sub_pack = (
                SubscriptionPack.objects.filter(structure_id=structure_id)
                .order_by("-start_date")
                .first()
            )
            # Aucune vérification n'est effectuée pour s'assurer que le pack n'a pas déjà d'options, car dans le parcours, on vient de créer la structure et son pack.
            if product_slug in ["diag", "human"]:
                option = sub_pack.add_new_option(product_slug)
                return Response(
                    {
                        "message": f"L'option '{product_slug}' n° '{option.id}' a été créée."
                    },
                    status=status.HTTP_200_OK,
                )
            elif product_slug == "start":
                option = sub_pack.add_new_option("diag")
                start_tag = QuestionTag.objects.get(name="mixity_start")
                option.tags.add(start_tag)
                option.is_active = False  # Passera a True une fois le paiement validé
                option.save()
                return Response(
                    {
                        "message": f"Vous allez être redirigé vers Stripe pour le paiement."
                    },
                    status=status.HTTP_200_OK,
                )
            elif product_slug == "pack360":
                human_option = sub_pack.add_new_option("human")
                diag_option = sub_pack.add_new_option("diag")
                return Response(
                    {
                        "message": f"Les options '{product_slug}' n° '{human_option.id}' et n° '{diag_option.id}' ont été créées."
                    },
                    status=status.HTTP_200_OK,
                )

        except SubscriptionPack.DoesNotExist:
            return Response(
                {"message": "La structure n'est pas reconnue !"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ApiValidateCoupon(APIView):
    def post(self, request, *args, **kwargs):
        coupon = Coupon.objects.filter(code=request.data.get("coupon")).first()
        subscription_option = SubscriptionOption.objects.filter(
            subscriptionPack__structure=request.data.get("structure_id")
        ).first()

        if coupon and coupon.used < coupon.quantity:
            subscription_option.is_active = True
            subscription_option.save()
            coupon.used += 1
            coupon.save()
            return Response(
                {"message": f"Votre abonnement Mixity Start a été validé."},
                status=status.HTTP_200_OK,
            )
        elif coupon and coupon.used == coupon.quantity:
            return Response(
                {"message": "Le code coupon utilisé est expiré !"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            return Response(
                {"message": "Le code coupon utilisé n'existe pas !"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ApiCreateSubStartOption(APIView, LoginRequiredMixin):
    def post(self, request, *args, **kwargs):
        try:
            structure = Structure.objects.get(siret=request.data.get("siret"))
        except Structure.DoesNotExist:
            structure = Structure.objects.get(duns=request.data.get("siret"))

        sub_pack = structure.subscription_pack.order_by("-start_date").first()
        sub_start = sub_pack.add_new_option("diag")
        sub_start.is_active = False
        sub_start.save()

        try:
            tag = QuestionTag.objects.get(name="mixity_start")
        except QuestionTag.DoesNotExist:
            return Response("Tag not found", status=status.HTTP_404_NOT_FOUND)

        sub_start.tags.add(tag)
        return Response({"pk": sub_start.pk}, status=status.HTTP_200_OK)


class ApiLogin(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email").lower().strip()
        password = request.data.get("password")

        if not email or not password:
            return Response(
                "Email and password are required", status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return Response("Login successful", status=status.HTTP_200_OK)
        else:
            return Response(
                "User couldn't authenticate", status=status.HTTP_401_UNAUTHORIZED
            )


class ApiForgottenPasswordMail(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email").lower().strip()

        if not email:
            return Response(
                "Email and password are required", status=status.HTTP_400_BAD_REQUEST
            )

        user = MixityUser.objects.filter(email=email)

        if user.first() is not None:
            send_mail_forgotten_password(
                user.first(),
                request,
                urlsafe_base64_encode(force_bytes(user.first().pk)),
                default_token_generator.make_token(user.first()),
            )
            return Response("Email sent", status=status.HTTP_200_OK)
        else:
            return Response(
                "Couldn't find this user", status=status.HTTP_401_UNAUTHORIZED
            )


class ApiCollaboratorLogin(APIView):
    def post(self, request, *args, **kwargs):
        encryption_class = encryption()
        encrypted_email = request.data.get("encrypted_email")
        email = encryption_class.decrypt_data(
            unquote_plus(encrypted_email.replace("%25", "%"))
        )
        password = request.data.get("password")

        if not email or not password:
            return Response(
                "Email and password are required", status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return Response("Login successful", status=status.HTTP_200_OK)
        else:
            return Response(
                "User couldn't authenticate", status=status.HTTP_401_UNAUTHORIZED
            )


class ApiUpdateUser(APIView, LoginRequiredMixin):
    def post(self, request, *args, **kwargs):
        user = request.user
        user.first_name = request.data.get("first_name")
        user.last_name = request.data.get("last_name")
        user.phone = request.data.get("phone")
        user.job = request.data.get("job")
        user.save()
        return Response(
            "POST request processed, Evaluation started.", status=status.HTTP_200_OK
        )


class ApiCreateCollaboratorPassword(APIView):
    def post(self, request, *args, **kwargs):
        encryption_class = encryption()
        encrypted_email = request.data.get("encrypted_email")
        email = encryption_class.decrypt_data(
            unquote_plus(encrypted_email.replace("%25", "%"))
        )
        password = request.data.get("password")
        subscribed_to_newsletter = request.data.get("subscribed_to_newsletter")
        user = MixityUser.objects.get(email=email)
        if user == None:
            return Response("User not found", status=status.HTTP_404_NOT_FOUND)
        user.is_newsletter = subscribed_to_newsletter
        user.set_password(password)
        user.save()
        return Response(
            "POST request processed, Evaluation started.", status=status.HTTP_200_OK
        )


class ApiGetStructureEntities(APIView):
    def add_structure_entities(self, entities, entities_list_structured):
        for entity in entities:
            entity_node = {
                "label": entity.name,
                "display": False,
                "disabled": False,
                "selected": False,
                "childrens": [],
            }
            if entity.children_entities.exists():
                entity_node["childrens"] = self.add_structure_entities(
                    entity.children_entities.all()[::-1], entity_node["childrens"]
                )
            entities_list_structured.append(entity_node)
        return entities_list_structured

    def post(self, request):
        try:
            siret = request.data.get("siret")
            structure = Structure.objects.get(siret=siret)
        except Structure.DoesNotExist:
            duns = request.data.get("duns")
            structure = Structure.objects.get(duns=request.data.get("duns"))
        entities_list_structured = []

        main_entity = structure.get_main_entity
        entities_list_structured = self.add_structure_entities(
            [
                main_entity,
            ],
            entities_list_structured,
        )
        for entity in entities_list_structured:
            entity["display"] = True
        return Response(entities_list_structured, status=status.HTTP_200_OK)


class ApiUpdateProfile(APIView):
    def post(self, request):
        try:
            user = request.user
            data = request.data
            
            # Mise à jour des champs textes (avec l'ajout de la fonction oubliée)
            user.first_name = data.get("first_name")
            user.last_name = data.get("last_name")
            user.phone = data.get("phone")
            user.job = data.get("job")
            
            # Sécurisation de l'image : on ne la modifie QUE si c'est un vrai fichier
            # (Cela empêche Django de planter s'il reçoit l'ancienne URL en texte)
            foto = data.get("foto")
            if foto and not isinstance(foto, str):
                user.foto = foto
                
            user.save()
            return Response({"message": "Update successful"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Ce print te permettra de voir la vraie erreur dans tes logs Heroku si ça replante
            print(f"Erreur lors de la mise à jour du profil : {e}") 
            return Response({"error": "Update failed"}, status=status.HTTP_400_BAD_REQUEST)


class ApiPasswordChange(APIView):
    def post(self, request):
        try:
            user = request.user
            data = request.data
            if user.check_password(data.get("old_password")):
                user.set_password(data.get("new_password"))
                user.save()
            else:
                return Response(
                    {"Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({"Update failed"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"Update successful"}, status=status.HTTP_200_OK)


class ApiForgottenPasswordChange(APIView):
    def post(self, request):
        try:
            user = MixityUser.objects.get(
                pk=force_str(urlsafe_base64_decode(request.data.get("uuid")))
            )
            user.set_password(request.data.get("new_password"))
            user.save()
        except Exception as e:
            return Response({"Update failed"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"Update successful"}, status=status.HTTP_200_OK)


class ApiGetProfile(APIView):
    def get(self, request):
        user = request.user
        return Response(
            {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "foto": user.get_foto_url(),
                "job": user.job,
                "phone": user.phone,
            },
            status=status.HTTP_200_OK,
        )


class ApiUpdateCollaborator(APIView):
    def post(self, request):
        data = request.data
        try:
            siret = request.data.get("siret")
            structure = Structure.objects.get(siret=siret)
        except Structure.DoesNotExist:
            duns = request.data.get("duns")
            structure = Structure.objects.get(duns=duns)
        entities = []
        isParentOwner = structure.members.filter(
            username=request.user.username
        ).exists()
        EntitiesTree().get_all_entities(
            structure.get_main_entity, request.user.username, entities, isParentOwner
        )
        for entity in entities:
            if entity.name == data.get("entity_name"):
                membership = entity.memberships.get(user__email=data.get("email"))
                membership.is_owner = data.get("is_owner")
                membership.is_reader = data.get("is_reader")
                membership.save()
                break
        return Response({"Update successful"}, status=status.HTTP_200_OK)


class ApiDeleteCollaborator(APIView):
    def post(self, request):
        data = request.data
        try:
            siret = request.data.get("siret")
            structure = Structure.objects.get(siret=siret)
        except Structure.DoesNotExist:
            duns = request.data.get("duns")
            structure = Structure.objects.get(duns=request.data.get("duns"))
        entities = []
        empty_entity = {
            "entity_name": "",
            "collaborators": [
                {
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "is_owner": False,
                    "is_reader": False,
                }
            ],
        }
        entity_list = []
        isParentOwner = structure.members.filter(
            username=request.user.username
        ).exists()
        EntitiesTree().get_all_entities(
            structure.get_main_entity, request.user.username, entities, isParentOwner
        )
        for entity in entities:
            memberships = entity.memberships.all()
            entity_data = empty_entity.copy()
            entity_data["entity_name"] = entity.name
            entity_data["collaborators"] = []
            for membership in memberships:
                if entity.name == data.get(
                    "entity_name"
                ) and membership.user.email == data.get("email"):
                    membership.delete()
                    continue
                entity_data["collaborators"].append(
                    {
                        "first_name": membership.user.first_name,
                        "last_name": membership.user.last_name,
                        "email": membership.user.email,
                        "is_owner": membership.is_owner,
                        "is_reader": membership.is_reader,
                    }
                )
            entity_list.append(entity_data)
        return Response(entity_list, status=status.HTTP_200_OK)


class ApiGetCollaborators(APIView):
    def post(self, request):
        data = request.data
        try:
            siret = request.data.get("siret")
            structure = Structure.objects.get(siret=siret)
        except Structure.DoesNotExist:
            duns = request.data.get("duns")
            structure = Structure.objects.get(duns=request.data.get("duns"))
        entities = []
        empty_entity = {
            "entity_name": "",
            "workforce": 0,
            "phone": "",
            "creation_year": 0,
            "collaborators": [
                {
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "is_owner": False,
                    "is_reader": False,
                }
            ],
        }
        entity_list = []
        isParentOwner = structure.members.filter(
            username=request.user.username
        ).exists()
        EntitiesTree().get_all_entities(
            structure.get_main_entity, request.user.username, entities, isParentOwner
        )
        for entity in entities:
            memberships = entity.memberships.all()
            entity_data = empty_entity.copy()
            entity_data["entity_name"] = entity.name
            entity_data["workforce"] = entity.workforce
            entity_data["phone"] = entity.phone
            entity_data["creation_year"] = entity.creation_year
            entity_data["collaborators"] = []
            for membership in memberships:
                entity_data["collaborators"].append(
                    {
                        "first_name": membership.user.first_name,
                        "last_name": membership.user.last_name,
                        "email": membership.user.email,
                        "is_owner": membership.is_owner,
                        "is_reader": membership.is_reader,
                    }
                )
            entity_list.append(entity_data)
        return Response(entity_list, status=status.HTTP_200_OK)


class ApiGetBusinessLines(APIView):
    def get(self, request):
        business_lines = BusinessLine.objects.filter(is_private=False)
        serializer = BusinessLineSerializer(business_lines, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EntitiesTree:
    def get_all_entities(self, main_entity, username, entities, isParentOwner=False):
        if isParentOwner == True:
            entities.append(main_entity)
        elif main_entity.memberships.filter(user__username=username).exists():
            entities.append(main_entity)
            isParentOwner = True
        if main_entity.children_entities.exists():
            for entity in main_entity.children_entities.all():
                self.get_all_entities(entity, username, entities, isParentOwner)


class ApiInviteCollaborators(APIView):
    def post(self, request):
        data = request.data
        try:
            siret = request.data.get("siret")
            structure = Structure.objects.get(siret=siret)
        except Structure.DoesNotExist:
            duns = request.data.get("duns")
            structure = Structure.objects.get(duns=request.data.get("duns"))
        collaborators = data.get("collaborators")
        entities = []
        isParentOwner = structure.members.filter(
            username=request.user.username
        ).exists()
        EntitiesTree().get_all_entities(
            structure.get_main_entity, request.user.username, entities, isParentOwner
        )
        for collaborator in collaborators:
            user, created = MixityUser.objects.get_or_create(
                email=collaborator["email"], username=collaborator["email"]
            )
            for entity in entities:
                if collaborator["entity"] == entity.name:
                    entity.memberships.create(
                        user=user, is_owner=False, is_reader=False
                    )
            if created:
                from django.contrib.auth.tokens import PasswordResetTokenGenerator

                token = PasswordResetTokenGenerator().make_token(user=user)

                uid = urlsafe_base64_encode(force_bytes(user.pk))
                send_invitation_mail(
                    user,
                    request=self.request,
                    structure=structure,
                    inviter=self.request.user,
                    uid=uid,
                    token=token,
                )
        return Response({"Invitation sent"}, status=status.HTTP_200_OK)


class ApiUpdateStructureDescription(APIView):
    def post(self, request):
        data = request.data
        try:
            siret = request.data.get("siret")
            structure = Structure.objects.get(siret=siret)
        except Structure.DoesNotExist:
            duns = request.data.get("duns")
            structure = Structure.objects.get(duns=request.data.get("duns"))
        structure.description = data.get("activity_description")
        structure.human_description = data.get("human_description")
        structure.commitment = data.get("commitment_description")
        structure.save()
        return Response({"Update successful"}, status=status.HTTP_200_OK)


class ApiGetStructureDescription(APIView):
    def post(self, request):
        try:
            siret = request.data.get("siret")
            structure = Structure.objects.get(siret=siret)
        except Structure.DoesNotExist:
            duns = request.data.get("duns")
            structure = Structure.objects.get(duns=request.data.get("duns"))
        activity_description = structure.description if structure.description else ""
        human_description = (
            structure.human_description if structure.human_description else ""
        )
        commitment_description = structure.commitment if structure.commitment else ""
        return Response(
            {
                "activity_description": activity_description,
                "human_description": human_description,
                "commitment_description": commitment_description,
            },
            status=status.HTTP_200_OK,
        )


class ApiUpdateEntityInfos(APIView):
    def post(self, request):
        data = request.data
        entities = []
        try:
            siret = request.data.get("siret")
            structure = Structure.objects.get(siret=siret)
        except Structure.DoesNotExist:
            duns = request.data.get("duns")
            structure = Structure.objects.get(duns=request.data.get("duns"))
        isParentOwner = structure.members.filter(
            username=request.user.username
        ).exists()
        EntitiesTree().get_all_entities(
            structure.get_main_entity, request.user.username, entities
        )
        for entity in entities:
            if entity.name == data.get("entity_name"):
                entity.workforce = data.get("workforce")
                entity.phone = data.get("phone")
                entity.creation_year = data.get("creation_year")
                entity.save()
                break
        return Response({"Update successful"}, status=status.HTTP_200_OK)


class ApiUpdateStructure(APIView):
    def post(self, request):
        data = request.data
        structure = Structure.objects.get(siret=data.get("old_siret"))
        structure.commercial_name = data.get("commercial_name")
        structure.category = data.get("category")
        structure.logo = data.get("logo")
        structure.workforce = data.get("workforce")
        structure.business_line = BusinessLine.objects.get(
            name=data.get("business_line")
        )
        structure.secondary_business_line = data.get("secondary_business_line")
        structure.website = data.get("website")
        structure.phone1 = data.get("phone")
        structure.save()
        return Response({"Update successful"}, status=status.HTTP_200_OK)

    def patch(self, request):
        data = request.data
        try:
            structure = Structure.objects.get(siret=data.get("old_siret"))

            update_fields = [
                "juridic_name",
                "category",
                "logo",
                "workforce",
                "secondary_business_line",
                "website",
                "phone",
            ]

            for field in update_fields:
                if data.get(field) is not None:
                    if field == "phone":
                        setattr(structure, "phone1", data.get(field))
                    else:
                        setattr(structure, field, data.get(field))

            if data.get("business_line"):
                structure.business_line = BusinessLine.objects.get(
                    name=data.get("business_line")
                )

            structure.save()
            return Response({"Update successful"}, status=status.HTTP_200_OK)

        except Structure.DoesNotExist:
            return Response(
                {"error": "Structure not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except BusinessLine.DoesNotExist:
            return Response(
                {"error": "Business line not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
