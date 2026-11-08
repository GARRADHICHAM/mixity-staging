# Mixity : plan de corrections, par ordre de priorité

Ce fichier liste tout ce qui doit être corrigé, du plus urgent au moins urgent.
Il est la **source de vérité** pour avancer étape par étape.

## Règles de travail

1. **On ne modifie rien sans confirmation.** Pour chaque point : je propose, vous confirmez, j'applique.
2. **Un point à la fois.** Après chaque correction : vérification, puis case cochée ici.
3. **Pour chaque point, avant d'agir, je vous montre** : les fichiers touchés, le changement exact et le risque de régression.
4. **Après chaque correction, on vérifie** avec la commande ou le test indiqué dans le point.
5. Les corrections du front React exigent de **recompiler les bundles** (`yarn build`) et de commiter les fichiers de `mixity/static/dist`.

## État de départ du dépôt (non commité)

| Fichier | Modification |
|---|---|
| `Dockerfile` | image Python 3.10 / Debian Bullseye, dépôts d'archive, allègement de l'image |
| `docker-compose.override.yml` (fichier local, ignoré par git) | base locale en `postgres:17` (alignée sur la production) |
| `subscriptions/migrations/0026_subscriptiontype_slug.py` | tolérance si les types de questionnaire n'existent pas encore |
| `start_webpack.sh` | changement de droits uniquement |

Ces changements sont uniquement locaux. Décidez plus tard lesquels vont dans un commit.

## Préalables (aucun code)

- [ ] **P-1. Régénérer toutes les clés et changer le mot de passe admin** (action du client : Mathieu).
  Stripe en premier (ou supprimer la clé live, le paiement n'étant plus utilisé), puis Cloudinary, OpenAI, DeepL, Google Maps, Webflow, Segment, Namsor, SendGrid, HubSpot. Les clés ont circulé en clair dans des messages et dans un PDF.
- [ ] **P-2. Vérifier que ce dépôt correspond au code déployé sur Heroku.**
  Yassir indique que cette version a été récupérée depuis la production : le risque de divergence est faible. Il reste à comparer le numéro de commit déployé (`heroku releases` ou l'onglet Activity) avec `git log` ici.
- [ ] **P-3. Retirer l'accès de l'ancien prestataire** à Heroku et à la base (action du client), s'il l'a toujours.

---

## PRIORITÉ 1 : MVP, à traiter en premier (environ 2 jours)

### 1.1 Images Cloudinary (demande explicite du client)
- [x] **M-1. Les chemins d'images contiennent `media/logos/` en trop.**
  - Où : `mixity/settings/prod.py:72-74` (stockage `MediaCloudinaryStorage`), champs `ImageField(upload_to=...)` (par exemple `accounts/models.py:282`).
  - Problème : le nouveau compte Cloudinary utilise les « dynamic folders » ; l'URL de livraison ne doit pas contenir le dossier. Exemple correct : `.../image/upload/v1/societe_..._logo_cpysda`. Exemple actuel (404) : `.../upload/v1/media/logos/societe_...`.
  - Correctif proposé : une classe de stockage personnalisée qui retire le préfixe dossier au moment de générer l'URL, utilisée à la place de `MediaCloudinaryStorage`. Un seul endroit, toutes les images.
  - Risque : faible. À tester avec un logo, une vignette et un PDF.
  - Effort : 0,5 j.

### 1.2 Sécurité de l'API (le risque le plus élevé)
- [x] **S-1. Définir une permission par défaut pour l'API.**
  - Où : `mixity/settings/base.py` (aucun bloc `REST_FRAMEWORK`).
  - Problème : DRF autorise tout le monde par défaut. Une grande partie des points d'accès n'a ni connexion ni contrôle de propriété.
  - Correctif proposé : `DEFAULT_PERMISSION_CLASSES = IsAuthenticated`, puis `AllowAny` explicite sur les points réellement publics : inscription (`ApiDashboardRegister`), connexion (`ApiLogin`), `ApiCollaboratorLogin`, liste des pays, mot de passe oublié et changement, accès par lien signé.
  - Risque : **moyen**. Un point public oublié casserait un parcours. Il faut lister les points publics avant et tester inscription, connexion, mot de passe oublié et lien collaborateur.
  - Effort : 0,5 à 1 j.
- [x] **S-2. Corriger l'ordre des classes de base** (`LoginRequiredMixin` placé après `APIView`, donc inopérant).
  - Où : `accounts/dashboard/views_api.py` : `ApiGetUserName` (127), `ApiUserNewsletter` (136), `ApiGetCompanyName` (155), `ApiUploadCollaboratorsCSV` (175), `ApiUploadEntitiesCSV` (363), `ApiCreateSubStartOption` (831), `ApiUpdateUser` (923).
  - Correctif : mettre le mixin en premier (`class X(LoginRequiredMixin, APIView)`), comme dans `mixity/dashboard`.
  - Effort : 0,25 j. À faire avec S-1.
- [x] **S-3. Les routes de validation et de réouverture d'évaluation sont sans contrôle.**
  - Où : `scoring/views.py:1597` (`EvaluationValidate`) et `:1616` (`EvaluationOpen`), routes `scoring/evaluation/<pk>/validate/` et `/open/`.
  - Problème : aucun `LoginRequired`, aucun contrôle de propriété. N'importe qui peut valider (déclenche le calcul des scores) ou rouvrir l'évaluation d'une autre entreprise en connaissant son numéro.
  - Correctif : connexion obligatoire et vérification que l'utilisateur est membre de la structure de l'évaluation.
  - À confirmer d'abord : les vues de téléversement `EvaluationFootprintUpload`, `EvaluationPDFUpload`, `EvaluationShareUpload`, `EvaluationSocialThumbnailUpload` (même fichier) semblent sans contrôle.
  - Effort : 0,5 j.
- [x] **S-4. Le point d'accès de création de mot de passe permet de prendre un compte.**
  - Où : `accounts/dashboard/views_api.py:936` (`ApiCreateCollaboratorPassword`) et `mixity/utils.py:73-90` (classe `encryption`).
  - Problème : sans authentification ; le jeton (e-mail chiffré) n'expire jamais et peut être réutilisé ; il marche pour n'importe quel utilisateur ; aucune validation du mot de passe ; `MixityUser.objects.get` lève une exception au lieu de renvoyer 404.
  - Correctif proposé : durée de vie du jeton (`ttl` à la vérification Fernet), limitation aux comptes collaborateurs, validation du mot de passe par Django, 404 propre.
  - Risque : moyen (les liens déjà envoyés peuvent expirer).
  - Effort : 0,25 à 1 j.

- [x] **S-8. « Mot de passe oublié » : le jeton du lien n'était jamais vérifié** (découvert pendant la priorité 2).
  - Où : `accounts/views.py` (`ResetPasswordConfirmView`) et `accounts/dashboard/views_api.py` (`ApiForgottenPasswordChange`).
  - Problème : le numéro d'utilisateur seul suffisait à changer le mot de passe de n'importe quel compte.
  - Correctif : la page vérifie le jeton et le mémorise en session ; l'API exige cette preuve. Voir `TRACE_CORRECTIONS.md`.

### 1.3 Secrets et configuration
- [x] **S-5. Retirer les valeurs sensibles par défaut du code.**
  - Où : `mixity/settings/base.py` : `SECRET_KEY` (40), `EMAIL_ENCRYPTION_KEY` (42-43), mot de passe de base par défaut (159), `GOOGLE_API_KEY` (337-338), `BLOG_API_KEY` (401) ; `mixity/settings/dev.py` (clés de chiffrement par défaut).
  - Correctif : lire ces valeurs depuis l'environnement uniquement, et faire échouer le démarrage en production si elles manquent. Le dev garde des valeurs factices.
  - Risque : **élevé en production** si une variable n'existe pas sur Heroku. À faire seulement après avoir vérifié la configuration Heroku.
  - Effort : 0,5 à 1 j.
- [x] **S-6. `DEBUG = True` par défaut et barre de débogage ouverte en préproduction.**
  - Où : `mixity/settings/base.py:313` ; `mixity/settings/prod.py:14-21` (`SHOW_TOOLBAR_CALLBACK` renvoie toujours `True`).
  - Correctif : `DEBUG` défaut `False` dans `base.py`, barre de débogage réservée au staff.
  - Effort : 0,25 j.
- [x] **S-7. L'en-tête `Host` brut sert à construire les URL de redirection Stripe.**
  - Où : `payments/views.py` (`StructureCreateCheckoutSession`, `request.META['HTTP_HOST']`), qui contourne la validation des hôtes autorisés de Django.
  - Correctif : utiliser `request.get_host()` (validé) ou une URL de base en configuration.
  - Effort : 0,25 j.

### 1.4 Vérifications nécessaires pour le MVP
- [x] **V-1. Comprendre pourquoi le worker RQ s'arrête immédiatement.**
  - Où : service `worker` de `docker-compose.yml` ; commande `rqworker default`. Sort avec le code 0, sans message.
  - À faire : le diagnostiquer, puis vérifier que les tâches (envoi de mails collaborateurs, calculs) tournent bien en production.
  - Effort : 0,5 j.
- [ ] **V-2. Vérifier l'envoi d'e-mails en production** (SendGrid / SMTP OVH, réception d'un e-mail de validation).

---

## PRIORITÉ 2 : défauts fonctionnels et robustesse

### 2.1 Contrôle de propriété des API
- [x] **F-1. Vérifier l'appartenance sur les endpoints qui reçoivent un SIRET/DUNS ou un identifiant.**
  - Où : `accounts/dashboard/views_api.py` : `ApiUpdateStructure` (1326), `ApiDeleteCollaborator` (1092), `ApiGetCollaborators` (1145), `ApiInviteCollaborators` (1218), `ApiUpdateStructureDescription` (1261), `ApiGetStructureDescription` (1277), `ApiUpdateEntityInfos` (1300), `ApiUpdateCollaborator` (1066), `ApiCreateStructureWithPack` (597), `ApiCreateOptions` (753) ; `mixity/dashboard/views_api.py` : `ApiSubscriptionOption` (1451), `ApiSubscriptionPack` (1474).
  - Problème : même avec S-1 (utilisateur connecté), n'importe quel compte pourrait modifier la structure d'un autre en changeant le SIRET.
  - Correctif : contrôle `request.user in structure.members` (ou rôle propriétaire) pour chaque vue.
  - Effort : 2 à 3 j. À faire vue par vue, avec test.
- [x] **F-2. `ApiGetCompanyName` plante toujours** (`user.structures.length`, `accounts/dashboard/views_api.py:155`). Correctif : `.count()` et un accès valide à la première structure. Effort : 0,25 j.
- [x] **F-3. Mauvaise cible de redirection** : la clé `"target"` est définie deux fois (`scoring/views.py:2332`). Correctif : garder la bonne valeur. Effort : 0,25 j.
- [x] **F-4. `except SubscriptionPack.DoesNotExist():` avec parenthèses** (`mixity/dashboard/views_api.py:~1488`). Effort : 0,1 j.
- [x] **F-5. Gestion des erreurs.**
  - 15 `except:` nus (`mixity/serializers.py` 161-377, `accounts/models.py:477`, `sirh/indicators.py:264`) ; 12 appels HTTP sans délai d'attente (ADP `sirh/services.py:100,115`, Webflow `scoring/management/commands/export_to_webflow.py`, Segment `mixity/services/segment.py`, webhooks).
  - Le catch-all de l'inscription (`ApiDashboardRegister`, `accounts/dashboard/views_api.py`) masque la vraie erreur : journaliser l'exception.
  - Effort : 1 à 2 j.
- [x] **F-6. Webhook Sentry** (`mixity/sentry_webhook.py`) : vérifier la signature avant d'analyser le JSON, utiliser `hmac.compare_digest`, gérer l'absence du secret. Effort : 0,5 j.

### 2.2 Front et interface
- [x] **U-1. L'adresse de l'API est écrite en `https` en dur** *(corrigé le 29/10 : protocole de la page, 12 bundles recompilés ; voir la trace)* : la page reste sur « Chargement » en local.
  - Où : `mixity/dashboard/js/Home.js:76`, `accounts/dashboard/js/CollaboratorLogin.js:37-40,117`, `mixity/dashboard/views.py:42`.
  - Correctif : utiliser `window.location.origin` ou des URL relatives ; puis `yarn build` et commit des bundles.
  - Effort : 0,25 j + recompilation.
- [x] **U-2. Boutons et liens morts sur les pages d'atterrissage.**
  - Où : `landing/dashboard/js/LandingDiag.js:55`, `LandingHuman.js:55` (`/evaluation/diag/`, `/evaluation/human/`), `/contact/`, `/pricing/`, `/360/` ; liens de `mixity/templates/500.html` (lignes 77, 185, 188, 191).
  - Cause : ces pages sont sur le site Webflow du client (en cours de restauration).
  - Correctif : une URL de site marketing configurable, ou retirer les boutons. À décider avec Mathieu.
  - Effort : 0,25 j.
- [x] **U-3. Six boutons « Voir un exemple » sans action** (Diag, Human, Pilot, trois sur Measure). Décision fonctionnelle nécessaire (exemple de rapport, démo, modale). Effort : 0,25 à 0,5 j.
- [ ] **U-4. Route fourre-tout `<slug:slug>/`** (`mixity/urls.py`) : toute adresse d'un mot est vue comme un identifiant d'entreprise. Correctif : préfixer ou valider le slug. Effort : 1 j. Risque : moyen (les routes dépendent du slug).

### 2.3 Traductions
- [x] **T-1. Le changement de langue n'a aucun effet en local Docker.**
  - Cause : les fichiers `.mo` compilés dans l'image sont masqués par le volume `.:/app` de `docker-compose.yml`.
  - Correctif : compiler les traductions au démarrage du conteneur, ou ne pas les masquer. En attendant : `docker compose exec web python manage.py compilemessages`.
  - Effort : 0,25 j.
- [x] **T-2. Enregistrements de traduction en double** (`scoring/translation.py:58`, `accounts/translation.py:12`) : deux classes portent le même nom. À vérifier : certains champs traduits peuvent manquer. Effort : 0,5 j.

### 2.4 Paiements (seulement si le paiement est réactivé)
- [ ] **PAY-1. Le webhook Stripe est incohérent avec le modèle.**
  - Où : `payments/views.py` (`StructureCreateCheckoutSession` crée une `CheckoutSession` avec `subscriptionOption`, `stripe_webhook` lit `checkout_session.subscription` qui reste vide).
  - Effort : 3 à 5 j avec tests. Le client dit que le paiement n'est plus utilisé : à reporter, ou à désactiver proprement.
- [x] **PAY-2. `stripe_price_id` lève `NameError`** (`subscriptions/models.py:323,325`, `settings` non importé). Effort : 0,1 j.
- [x] **PAY-3. Robustesse du webhook** : en-tête de signature absent (`KeyError`), session inconnue (`DoesNotExist`), doublons de facture, méthode non limitée à POST. Effort : inclus dans PAY-1.

### 2.5 Tests
- [x] **TEST-1. Réparer les 7 tests en échec** : 4 tests de formats de nombres (liés à T-1), 3 tests `assertNumQueries` aux nombres périmés (37 vs 38, 39 vs 40). Effort : 0,5 à 1 j.
- [ ] **TEST-2. Ajouter des tests** sur les parcours critiques : authentification des API, propriété des structures, validation d'évaluation, création de mot de passe. Effort : 2 à 3 j.

---

## Performance et chargement (ajouté pendant la priorité 2)

- [x] **PERF-1.** Barre de débogage Django facultative en développement (`DEBUG_TOOLBAR=1` pour l'activer) : tableau de bord 4,14 s -> 0,13 s en local.
- [x] **PERF-2.** `answer_count` : `EXISTS` à la place d'un `GROUP BY / HAVING` (aussi en production) : `/api/entity/` 0,71 s -> 0,24 s.
- [x] **UX-1.** Indicateur de chargement animé (composant `Loading.js`) sur 36 pages ; page d'accueil sans appel `api/url/` ni `https://` en dur.
- [ ] **PERF-3.** Regrouper les 177 petites requêtes de `/api/entity/` (`prefetch_related`) et paralléliser les appels de la page d'accueil (non nécessaire pour l'instant, risque de régression).

## Corrections du 28 et 29/10/2026 (test du parcours complet)

- [x] **WORKER-1. Le worker RQ s'arrêtait au bout d'une minute** (redis-py 8 incompatible avec RQ 1.16) : aucun score calculé. `requirements.txt` : `redis~=5.2.1`.
- [x] **DIAG-1. Les nouveaux Diag étaient créés sans question** (`is_collaborator = True` en base) : migration de données `scoring/0474`.
- [x] **M-2. Fichiers Excel, CSV et PDF Cloudinary en 404** : `FlatRawCloudinaryStorage`. Reste côté client : autoriser la diffusion des PDF dans Cloudinary.
- [x] **PAY-4. Carte « Start » bloquée sur la page de paiement Stripe** : redirection vers le tableau de bord sans clé Stripe.
- [x] **MAIL-1. Liens des e-mails vers `www.app.mixity.io`, domaine inexistant** : `app.mixity.io`.
- [ ] **À décider avec le client** : carte « Start » à l'inscription ; bouton de création d'entreprise pour un nouvel utilisateur ; fichiers absents du nouveau compte Cloudinary.

## PRIORITÉ 3 : maintenance (après stabilisation)

- [ ] **M-A. Mettre à jour Django 3.2 vers 4.2 LTS** (fin de vie en avril 2024) : remplacer `ugettext_lazy`, `force_text`, etc. Effort : 5 à 10 j.
- [ ] **M-B. Nettoyer les dépendances** : `uuid==1.30` (paquet obsolète), `psycopg2` et `psycopg2-binary` en double, `django-debug-toolbar` listé deux fois et livré en production, `reportlab`, `stripe`, `lxml` non épinglés, `requests` 2.26, `django-allauth` 0.51.
- [ ] **M-C. Rendre l'installation reproductible depuis zéro** : les migrations de `scoring` (613 fichiers) supposent des données de production (`scoring/migrations/0105`) ; solution à étudier : aplatir les migrations ou fournir des données de départ. Effort : 3 à 5 j.
- [ ] **M-D. Simplifier le code** : `scoring/models.py` (9 166 lignes), doublon `is_scan` (`:2888`), doublons de sérialiseurs (`mixity/serializers.py:88`), environ 700 alertes de lint, 41 `print()`, 47 TODO/FIXME.
- [ ] **M-E. Rendre le front indépendant des bundles commités** : ne plus versionner `mixity/static/dist`, construire à la mise en production.

---

## Récapitulatif des efforts

| Priorité | Contenu | Estimation |
|---|---|---|
| Préalables | clés, code Heroku, accès | actions client |
| 1 (MVP) | images, sécurité de base, secrets, vérifications | 3 à 5 j |
| 2 | propriété des données, fonctionnel, front, tests, traductions | 8 à 14 j |
| 2.4 | paiements (si réactivés) | 3 à 5 j |
| 3 | maintenance, mise à jour de Django | 10 à 20 j |

## Journal d'avancement

| Date | Point | Décision | Résultat |
|---|---|---|---|
| 24/10/2026 | Priorités 1 et 2 | autorisation de Yassir | voir TRACE_CORRECTIONS.md |
| 28-29/10/2026 | WORKER-1, DIAG-1, M-2, PAY-4, U-1, MAIL-1 | demande de Yassir | 172 tests OK, non déployé |
