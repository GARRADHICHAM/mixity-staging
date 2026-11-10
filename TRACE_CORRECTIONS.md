# Mixity : traces des corrections

Ce fichier garde la trace de **chaque correction appliquée** : ce qui a été fait, comment, et comment on l'a vérifié.
La liste des points à traiter est dans `CORRECTIONS_MIXITY.md`.

## Méthode

1. Le point est analysé en lecture seule.
2. Le changement exact est présenté, avec les fichiers touchés et le risque.
3. **Rien n'est appliqué avant confirmation.**
4. Après application : vérification, puis une entrée est ajoutée ci-dessous.

## Modèle d'entrée

```
### [Identifiant] Titre (date)
- Décision : confirmé le ... par ...
- Problème : ...
- Fichiers modifiés : ...
- Changement : ... (avant / après)
- Pourquoi cette approche : ...
- Vérification : commandes lancées et résultat
- Risques et limites : ...
- À faire ensuite : ...
```

## Corrections appliquées

### M-1. Images Cloudinary : l'URL contenait le dossier en trop (24/10/2026)
- **Décision** : demandée par le client (affichage des images), autorisation de modifier le code donnée par Yassir.
- **Problème** : les logos et autres fichiers s'affichaient en 404. En base, les noms ont la forme `media/logos/<fichier>_<suffixe>` (157 logos sur 157). Le nouveau compte Cloudinary est en mode « dynamic folders » : l'identifiant public est le nom du fichier seul, sans dossier. La bibliothèque générait `.../upload/v1/media/logos/<fichier>` au lieu de `.../upload/<fichier>`.
- **Fichiers modifiés** :
  - `mixity/storage.py` (nouveau) : classe `FlatCloudinaryStorage`.
  - `mixity/settings/prod.py` : `DEFAULT_FILE_STORAGE` passe de `cloudinary_storage.storage.MediaCloudinaryStorage` à `mixity.storage.FlatCloudinaryStorage`.
  - `mixity/test_storage.py` (nouveau) : 6 tests unitaires.
- **Changement** :
  - `_get_url` ne garde que `os.path.basename(name)` : les anciens noms (`media/logos/x`) et les nouveaux (`x`) donnent la même adresse.
  - `_upload` envoie le dossier dans `asset_folder` (rangement dans la médiathèque) et n'utilise plus `folder`, qui mettait le dossier dans l'identifiant public.
  - `delete` utilise aussi le nom seul.
- **Pourquoi cette approche** : toutes les images passent par `FieldFile.url` (17 champs fichier), donc un seul point de correction suffit. Les anciens noms en base restent valides, aucune migration de données n'est nécessaire.
- **Vérification** :
  - `python manage.py test mixity.test_storage` (réglages de test) : 6 tests, OK.
  - Avec un faux compte `mixity`, `url('media/logos/societe_cooperative_migros_geneve_logo_cpysda')` et `url('societe_cooperative_migros_geneve_logo_cpysda')` donnent la même adresse `https://res.cloudinary.com/mixity/image/upload/societe_cooperative_migros_geneve_logo_cpysda`.
- **Risques et limites** :
  - Non testé contre le vrai Cloudinary (aucune clé utilisée). **À tester par le client après déploiement** : un logo, une vignette de partage, une photo d'expert et un PDF.
  - Seuls les logos sont confirmés par le support Cloudinary. Si d'autres types de fichiers ont gardé leur dossier dans l'identifiant, ils casseront.
  - `asset_folder` n'est valable qu'en mode « dynamic folders » ; non validé sur le compte réel.
  - Sans effet en local : le stockage Cloudinary n'est configuré qu'en production.
- **À faire ensuite** : le client teste les images sur le site après déploiement.

### S-1 et S-2. API : connexion obligatoire par défaut, mixins corrigés (24/10/2026)
- **Décision** : autorisation de modifier le code donnée par Yassir (périmètre Priorité 1).
- **Problème** :
  - Aucun bloc `REST_FRAMEWORK` dans les réglages : Django REST Framework autorise tout le monde par défaut. Sur 107 classes DRF routées, **36 étaient accessibles sans connexion** (dont `update_structure`, `get_collaborators`, `delete_collaborator`, `invite_collaborators`, les imports CSV).
  - Sept vues avaient `class X(APIView, LoginRequiredMixin)` : le mixin était après `APIView`, donc jamais exécuté.
- **Fichiers modifiés** :
  - `mixity/settings/base.py` : ajout de `REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"]}`.
  - `accounts/dashboard/views_api.py` : import de `AllowAny` ; `permission_classes = [AllowAny]` sur les 8 vues réellement publiques ; ordre des bases corrigé en `(LoginRequiredMixin, APIView)` pour `ApiGetUserName`, `ApiUserNewsletter`, `ApiGetCompanyName`, `ApiUploadCollaboratorsCSV`, `ApiUploadEntitiesCSV`, `ApiCreateSubStartOption`, `ApiUpdateUser`.
  - `accounts/test_api_permissions.py` (nouveau) : 4 tests.
- **Vues laissées publiques (8)**, choisies d'après les appels des pages non connectées (`accounts/dashboard/js/*`) : `ApiLogin`, `ApiDashboardRegister`, `ApiCountriesList`, `ApiForgottenPasswordMail`, `ApiForgottenPasswordChange`, `ApiCollaboratorLogin`, `ApiCreateCollaboratorPassword`, `ApiGetEmail`.
- **Pourquoi cette approche** : un réglage global ferme d'un coup toutes les vues oubliées, présentes et futures. Les points publics sont déclarés explicitement. Les 71 vues déjà protégées par `LoginRequiredMixin` ne changent pas.
- **Vérification** :
  - `python manage.py test accounts.test_api_permissions` : 4 tests, OK. Le test principal liste toutes les vues DRF routées et vérifie que l'ensemble des vues ouvertes est exactement les 8 ci-dessus : il échouera si une vue ouverte est ajoutée par oubli.
  - Requêtes réelles sur l'instance locale, sans connexion : `update_structure`, `get_collaborators`, `delete_collaborator`, `invite_collaborators` répondent 403 ; `upload_collaborators_csv` et `get_user_name` redirigent (302) vers la connexion. `countries` répond 200 ; une connexion avec un mauvais mot de passe répond 401.
  - Avec un compte connecté : `login` 200, `get_user_name` 200, `membership` 200, `category` 200.
- **Risques et limites** :
  - Un parcours public oublié serait bloqué. L'inventaire s'appuie sur les appels des pages non connectées de `accounts/dashboard/js`. À tester en recette : inscription, mot de passe oublié, invitation d'un collaborateur, enquête collaborateur.
  - **Ce n'est pas un contrôle de propriété** : un utilisateur connecté peut encore modifier la structure d'un autre en changeant le SIRET (point F-1, priorité 2).
  - Les vues protégées par `LoginRequiredMixin` renvoient une redirection (302) aux visiteurs, les autres un 403 : comportement mixte hérité du projet.
- **À faire ensuite** : S-3 (routes `validate` et `open` des évaluations), S-4, S-5 à S-7.

### S-3. Évaluations : validation, réouverture et téléversements sans contrôle (24/10/2026)
- **Décision** : autorisation de modifier le code donnée par Yassir (périmètre Priorité 1).
- **Problème** : six vues de `scoring/views.py` n'avaient ni connexion ni contrôle de propriété :
  - `EvaluationValidate` (`/scoring/evaluation/<pk>/validate/`) : déclenche le calcul des scores ;
  - `EvaluationOpen` (`/scoring/evaluation/<pk>/open/`) : rouvre une évaluation ;
  - `EvaluationFootprintUpload`, `EvaluationPDFUpload`, `EvaluationShareUpload`, `EvaluationSocialThumbnailUpload` : remplacent l'image, le PDF ou la vignette d'une évaluation (écriture sur Cloudinary en production).
  Un visiteur anonyme connaissant un numéro d'évaluation pouvait donc valider, rouvrir ou remplacer les fichiers de n'importe quelle entreprise.
- **Fichiers modifiés** :
  - `scoring/views.py` : nouvelle classe `EvaluationEditorMixin(LoginRequiredMixin, UserPassesTestMixin)` ; les six vues en héritent.
  - `scoring/test_evaluation_access.py` (nouveau) : 6 tests.
- **Règle d'accès** : connexion obligatoire ; équipe Mixity (`is_staff`) autorisée ; sinon l'utilisateur doit avoir des droits sur l'entité de l'évaluation (`user.test_func_rights`, règle déjà utilisée dans le projet : appartenance à l'entreprise, à l'entité, ou propriétaire d'une entité parente) **et ne pas être lecteur** (`membership.is_reader`).
- **Réponses** : visiteur non connecté, redirection vers la connexion (302) ; connecté sans droit, 403.
- **Pourquoi cette approche** : réutilise les règles de droits déjà présentes dans `accounts/models.py` au lieu d'en inventer. Un seul mixin pour les six vues.
- **Vérification** :
  - `python manage.py test scoring.test_evaluation_access` : 6 tests, OK (visiteur anonyme, membre d'une autre entreprise, lecteur, propriétaire, équipe Mixity ; le calcul de score n'est pas lancé quand l'accès est refusé).
  - Contrôle de non-régression du test : avec l'ancienne version de `scoring/views.py`, les mêmes tests échouent (16 échecs, 3 erreurs).
- **Risques et limites** :
  - Un utilisateur légitime dont les droits ne passent pas par `test_func_rights` serait refusé. Cas à tester en recette : propriétaire d'entreprise, utilisateur rattaché à une entité seulement, utilisateur lecteur.
  - Les vues `EvaluationFootprintUpload` et consorts utilisent le jeton CSRF de Django ; l'appel du front (`AssessPage.js:517`) n'a pas été modifié.
  - Les autres vues de `scoring/views.py` qui n'ont pas de mixin de connexion (`AdvancedEvaluationFilter`, `StructureDetailPublicView`) sont des filtres ou des pages publiques par conception.
- **À faire ensuite** : S-4 (point d'accès de création de mot de passe).

### S-4. Création de mot de passe : prise de contrôle de comptes (24/10/2026)
- **Décision** : autorisation de modifier le code donnée par Yassir (périmètre Priorité 1).
- **Problème** : `ApiCreateCollaboratorPassword` (`POST /api/create_password/`) était public et acceptait un jeton (l'e-mail chiffré avec Fernet) qui **n'expirait jamais** et pouvait être réutilisé. Avec ce jeton, n'importe qui pouvait **remplacer le mot de passe de n'importe quel compte**, même un compte qui en avait déjà un. De plus, `MixityUser.objects.get` levait une exception pour un e-mail inconnu (le test `== None` suivant était du code mort), et l'absence de l'option newsletter provoquait une erreur 500 (`is_newsletter` à `NULL`).
- **Fichiers modifiés** :
  - `mixity/utils.py` : `encryption.decrypt_data(encoded_email, ttl=None)` accepte une durée de validité (Fernet vérifie la date incluse dans le jeton).
  - `accounts/dashboard/views_api.py` : réécriture de la vue ; imports de `InvalidToken` et de `settings`.
  - `accounts/test_create_password.py` (nouveau) : 7 tests.
- **Changement** :
  - champs obligatoires : `encrypted_email` et `password`, sinon 400 ;
  - jeton valable `PASSWORD_RESET_TIMEOUT_DAYS` jours (30 par défaut, le même réglage que la réinitialisation de mot de passe) ; jeton invalide, falsifié ou expiré : 400 « Invalid or expired link » ;
  - e-mail inconnu : 404 (au lieu d'une exception) ;
  - **le mot de passe n'est défini que si le compte n'en a pas encore** (mot de passe vide ou « inutilisable », ce qui est le cas des invités : 474 comptes « inutilisables » et 18 vides sur 2 055 dans la base de production) ; sinon 400 ;
  - l'option newsletter devient facultative.
- **Pourquoi cette approche** : ferme la prise de contrôle sans changer le parcours d'invitation (même adresse, mêmes champs, même réponse 200). Le délai réutilise un réglage existant.
- **Vérification** : `python manage.py test accounts.test_create_password` : 7 tests, OK (invité qui définit son mot de passe, compte avec mot de passe non écrasé, lien expiré refusé à 31 jours, lien accepté à 10 jours, lien falsifié, champs manquants, utilisateur inconnu). Les 23 tests de S-1 à S-4 passent ensemble.
- **Risques et limites** :
  - Un invité qui ouvre son lien **plus de 30 jours** après l'envoi devra passer par « Mot de passe oublié ».
  - Un invité qui a déjà défini son mot de passe et rejoue le lien est refusé (400) ; le front affiche son message d'erreur générique.
  - Les autres usages du jeton (`/api/get_email/<jeton>/`, `/api/collaborator_login/`) n'ont pas de limite de durée : ils ne définissent pas de mot de passe (le second exige le mot de passe actuel).
  - Les règles de qualité de mot de passe de Django (`AUTH_PASSWORD_VALIDATORS`) ne sont toujours pas appliquées ici ni à l'inscription : à décider avec le client (impact sur l'expérience utilisateur).
- **À faire ensuite** : S-5 (valeurs sensibles par défaut), S-6 (`DEBUG`), S-7 (en-tête `Host`).

### S-5, S-6 et S-7. Secrets dans le dépôt, DEBUG, barre de débogage et validation de l'hôte (24/10/2026)
- **Décision** : autorisation de modifier le code donnée par Yassir (périmètre Priorité 1).
- **Problèmes** :
  - Des secrets étaient écrits en clair dans `mixity/settings/base.py` : une clé Google (`GOOGLE_API_KEY`), la clé de l'API du blog Ghost (`BLOG_API_KEY`), et **deux adresses de webhook Google Chat avec clé et jeton** (`GOOGLECHAT_WEBHOOK_URL`, `GOOGLECHAT_LOGENTRIES_WEBHOOK_URL`). Les valeurs par défaut publiques de `SECRET_KEY` et `EMAIL_ENCRYPTION_KEY` sont utilisées silencieusement si la variable d'environnement manque en production.
  - `DEBUG = True` par défaut dans `base.py` ; en préproduction avec `DEBUG` actif, la barre de débogage était visible par tout le monde (`SHOW_TOOLBAR_CALLBACK` renvoyait toujours `True`).
  - **Plus grave que prévu (S-7)** : `django_heroku.settings(locals())` impose `ALLOWED_HOSTS = ["*"]`. L'en-tête `Host` n'était donc pas validé en production, alors que les liens des e-mails (réinitialisation de mot de passe, invitations, confirmation) sont construits avec `request.build_absolute_uri`, c'est-à-dire à partir de cet en-tête : un attaquant pouvait faire envoyer à une victime un lien pointant vers son propre domaine.
  - `payments/views.py` construisait l'URL de retour Stripe avec `request.META['HTTP_HOST']`, qui contourne la validation de Django.
- **Fichiers modifiés** :
  - `mixity/settings/base.py` : `PUBLIC_DEFAULT_SECRETS` (valeurs publiques, nommées explicitement) ; `DEBUG = False` par défaut (`dev.py` et `test.py` le passent à `True`, `prod.py` le fixe) ; `GOOGLE_API_KEY`, `BLOG_API_KEY` et les deux webhooks Google Chat lus depuis l'environnement, valeur par défaut vide.
  - `mixity/settings/prod.py` : barre de débogage réservée au staff ; `ALLOWED_HOSTS` rétabli **après** `django_heroku` (`app.mixity.io`, `www.app.mixity.io`, `staging.mixity.io`, `.herokuapp.com`, plus la variable d'environnement `ALLOWED_HOSTS` pour en ajouter) ; message CRITICAL (journaux et Sentry) si `SECRET_KEY` ou `EMAIL_ENCRYPTION_KEY` sont encore les valeurs publiques.
  - `payments/views.py` : `request.get_host()` à la place de `request.META['HTTP_HOST']`.
- **Pourquoi cette approche** :
  - `GOOGLE_API_KEY`, `BLOG_API_KEY` et les webhooks ne sont utilisés par aucun code en dehors des réglages et des webhooks Sentry / Logentries (propres à l'ancienne société) : les retirer du dépôt ne change aucune fonctionnalité.
  - `SECRET_KEY` et `EMAIL_ENCRYPTION_KEY` : pas d'arrêt brutal du démarrage, car on ignore si la production a déjà ses propres valeurs ; changer `EMAIL_ENCRYPTION_KEY` invalide tous les liens déjà envoyés. On alerte donc sans bloquer.
- **Vérification** (réglages de production chargés dans le conteneur avec des variables simulées) :
  - `DEBUG = False`, `DEFAULT_FILE_STORAGE = mixity.storage.FlatCloudinaryStorage`, `REST_FRAMEWORK` présent, clés Google, Ghost et webhooks vides.
  - Sans secrets fournis : deux messages CRITICAL (`SECRET_KEY`, `EMAIL_ENCRYPTION_KEY`). Avec secrets fournis : aucun message.
  - Validation de l'hôte : `app.mixity.io` et `mixityv2-049dc76b4d62.herokuapp.com` acceptés ; `evil.example.com` refusé (`DisallowedHost`) ; un domaine ajouté par `ALLOWED_HOSTS=client.exemple.fr` est accepté.
  - Un scan du dépôt (`git grep`) ne trouve plus de clé Google, Stripe, SendGrid, OpenAI, AWS, jeton de webhook ni clé privée dans le code versionné.
  - L'instance de développement répond toujours (200).
- **Risques et limites, avec action du client** :
  - **Avant le déploiement, vérifier que le domaine réel de production est dans la liste.** Si le site est servi sur un autre domaine que `app.mixity.io`, `www.app.mixity.io`, `staging.mixity.io` ou `*.herokuapp.com`, Django répondra 400 « Bad Request (400) » : dans ce cas ajouter la variable Heroku `ALLOWED_HOSTS` (domaines séparés par des virgules).
  - Les clés qui étaient dans l'historique du dépôt **restent visibles dans l'historique git** : elles doivent être régénérées (clé Google, clé Ghost, webhooks Google Chat), comme les clés de l'échange avec l'ancien prestataire (point P-1).
  - À définir sur Heroku : `SECRET_KEY`, `EMAIL_ENCRYPTION_KEY` (avec le risque d'invalider les liens déjà envoyés), `GOOGLE_API_KEY` si une carte Google est utilisée (rien dans le code actuel ne s'en sert).
  - Si le webhook Sentry ou Logentries est encore utilisé, définir `GOOGLECHAT_WEBHOOK_URL` / `GOOGLECHAT_LOGENTRIES_WEBHOOK_URL` ; sinon ces points d'accès renverront une erreur (cas traité dans le point F-6).
  - `manage.py` utilise `mixity.settings` (= `base.py`) quand `DJANGO_SETTINGS_MODULE` n'est pas défini : `DEBUG` y est maintenant `False`. Sur Heroku la variable doit pointer vers `mixity.settings.prod`.
- **À faire ensuite** : V-1 (worker) et V-2 (e-mails), puis passage de toute la suite de tests.

### V-1 et V-2. Vérifications : worker de tâches de fond et envoi d'e-mails (24/10/2026)
- **Décision** : vérifications du périmètre Priorité 1, aucune modification de code.
- **V-1. Worker RQ** : on avait constaté que le conteneur `worker` s'arrêtait aussitôt après son démarrage (code 0, sans message).
  - Diagnostic : la boucle de travail de RQ (`Worker.work`) attend bien les tâches ; l'absence de message vient de la configuration des journaux, qui n'affiche pas ceux de RQ.
  - Test réalisé : démarrage du conteneur (`docker compose up -d worker`), puis ajout d'une tâche (`builtins.len([1, 2, 3])`) dans la file `default` : la tâche passe à l'état `finished` avec le résultat `3`. Le conteneur reste actif.
  - Conclusion : **non reproduit, le worker fonctionne en local.** L'arrêt observé plus tôt coïncidait avec la réinitialisation de la base et le redémarrage des conteneurs ; il n'a pas été expliqué avec certitude.
  - À vérifier en production : que le process `worker` du Procfile est démarré sur Heroku (onglet Resources : `worker` à 1 dyno) et que Redis est relié.
- **V-2. E-mails** :
  - En local : l'inscription envoie bien le mail de confirmation vers Mailhog (http://localhost:8025), avec un lien correct (`http://localhost:8000/account/register/step2?...`).
  - En production : `prod.py` utilise le SMTP OVH (`pro2.mail.ovh.net`, compte `support@mixity.io`, mot de passe lu dans `EMAIL_HOST_PASSWORD`). Le package SendGrid est dans les dépendances mais n'est pas utilisé par ces réglages. **Non vérifiable depuis ce poste.**
  - **Action du client** : créer un compte de test sur le site déployé et vérifier la réception du mail de confirmation (et du mail « mot de passe oublié »).

## Bilan de la Priorité 1 (24/10/2026)

| Point | Résultat |
|---|---|
| M-1 Images Cloudinary | appliqué, 6 tests |
| S-1, S-2 API protégée par défaut, mixins | appliqués, 4 tests |
| S-3 Évaluations (validate, open, téléversements) | appliqué, 6 tests |
| S-4 Création de mot de passe | appliqué, 7 tests |
| S-5, S-6, S-7 Secrets, DEBUG, validation de l'hôte | appliqués, vérifiés avec les réglages de production simulés |
| V-1 Worker | vérifié, fonctionne en local |
| V-2 E-mails | local vérifié ; production à vérifier par le client |

**Suite de tests complète** (`python manage.py test --parallel 4`, réglages de test) : 112 tests (89 d'origine + 23 nouveaux). Résultat : 4 échecs et 3 erreurs, **exactement les mêmes 7 qu'avant les corrections** (formats de nombres traduits, et trois tests de nombre de requêtes). Aucun test n'a été cassé par les changements.

**Fichiers touchés** : `mixity/storage.py` (nouveau), `mixity/settings/base.py`, `mixity/settings/prod.py`, `mixity/utils.py`, `accounts/dashboard/views_api.py`, `scoring/views.py`, `payments/views.py`. **Tests ajoutés** : `mixity/test_storage.py`, `accounts/test_api_permissions.py`, `accounts/test_create_password.py`, `scoring/test_evaluation_access.py`.

**Rien n'est commité ni déployé.** Avant de déployer, le client doit : voir la liste ci-dessus des risques de S-5 à S-7 (domaines autorisés, variables `SECRET_KEY` et `EMAIL_ENCRYPTION_KEY`), régénérer les clés (P-1), puis tester après déploiement une image, une inscription, un mot de passe oublié et un parcours d'invitation.

### Complément à S-5. Valeurs locales dans `mixity/settings/.env` (24/10/2026)
- **Demande de Yassir** : pouvoir continuer à tester avec les valeurs retirées du code.
- **Changement** :
  - création de `mixity/settings/.env` (fichier local, **ignoré par git** : `.gitignore` ligne 69, permissions 600) contenant `GOOGLE_API_KEY`, `BLOG_API_KEY`, `GOOGLECHAT_WEBHOOK_URL`, `GOOGLECHAT_LOGENTRIES_WEBHOOK_URL`. Les valeurs ont été copiées depuis `HEAD` par un script, sans affichage ;
  - `mixity/settings/dev.py` : quatre lignes relisent ces variables via `env(...)` après `read_env`, car `base.py` est exécuté avant la lecture du `.env` ; `BLOG_API_URL` est recalculé.
- **Vérification** : dans les réglages de développement, les quatre variables sont renseignées (longueurs 39, 26, 155, 155) ; l'application répond (200) ; `git grep` ne trouve aucune de ces valeurs dans les fichiers suivis.
- **Limites** : ces valeurs restent exposées par l'historique git ; elles doivent être régénérées (P-1). Pour tout autre secret local (Stripe, SendGrid, Cloudinary...), ajouter une ligne `NOM=valeur` dans ce `.env` ; en production, utiliser les variables de configuration Heroku.

## PRIORITÉ 2 : défauts fonctionnels et robustesse

### S-8 (nouveau, découvert pendant F-1). « Mot de passe oublié » : n'importe quel compte modifiable (24/10/2026)
- **Décision** : autorisation de modifier le code donnée par Yassir (« passe maintenant à la Priorité 2 »). Point ajouté au plan car plus grave que les autres.
- **Problème** : le mail « mot de passe oublié » contient un lien `/user/reset/<uidb64>/<jeton>/`, mais **le jeton n'était vérifié nulle part** :
  - la page `ResetPasswordConfirmView` (`accounts/views.py`) affichait simplement le formulaire en y mettant l'identifiant (`uuid = uidb64`) ;
  - l'API publique `ApiForgottenPasswordChange` (`POST /api/forgotten_password_change/`) changeait le mot de passe de l'utilisateur désigné par `uuid` (le numéro d'utilisateur encodé) **sans aucun jeton**.
  Il suffisait de connaître (ou de deviner : ce sont des numéros qui se suivent) le numéro d'un utilisateur pour changer son mot de passe et prendre son compte, y compris un administrateur. Cette vue avait été laissée publique volontairement à l'étape S-1 car la page de réinitialisation doit fonctionner sans connexion.
- **Fichiers modifiés** :
  - `accounts/views.py` : `ResetPasswordConfirmView.get` vérifie le jeton avec `default_token_generator.check_token` ; si le lien est invalide ou périmé, redirection vers `user:password_reset` avec un message ; sinon la preuve (identifiant + jeton) est mémorisée **dans la session du navigateur**. Ajout de `PASSWORD_RESET_SESSION_KEY` et de `get_user_from_uidb64` (utilisateur actif uniquement).
  - `accounts/dashboard/views_api.py` : `ApiForgottenPasswordChange` exige cette preuve de session, vérifie que l'identifiant correspond et que le jeton est toujours valide, puis efface la preuve.
  - `accounts/test_forgotten_password.py` (nouveau) : 6 tests.
- **Pourquoi cette approche** : le front React n'a pas à changer (il envoie déjà `uuid` et le nouveau mot de passe) donc pas de recompilation. Le jeton de Django dépend de l'ancien mot de passe : **un lien ne fonctionne qu'une fois** et expire après `PASSWORD_RESET_TIMEOUT_DAYS` (30 jours).
- **Vérification** :
  - Tests (6, OK) : le numéro seul ne suffit plus (400, mot de passe inchangé) ; lien valide puis changement (200) ; jeton faux (redirection, puis 400) ; la preuve d'un utilisateur ne permet pas de changer un autre compte ; lien utilisable une seule fois ; utilisateur inactif refusé.
  - Essai réel sur l'instance locale avec un compte jetable : demande de réinitialisation, lien reçu dans Mailhog ; changement direct sans ouvrir le lien : **400** ; ouverture du lien : 200 ; changement : 200 ; connexion avec le nouveau mot de passe : 200 ; rejeu : **400**.
- **Risques et limites** :
  - L'utilisateur doit ouvrir le lien et changer le mot de passe **dans le même navigateur** (même session). Ouvrir le lien sur un téléphone puis changer sur un ordinateur ne fonctionnera pas : c'est le comportement standard de Django.
  - **À vérifier en production** : le lien du mail est construit avec `https://` + `ENVIRONMENT_DOMAIN`. En production ce réglage vaut `www.app.mixity.io` (`mixity/settings/prod.py`) ; si le vrai domaine est `app.mixity.io`, le lien du mail pointe vers un domaine inexistant et la réinitialisation ne peut pas aboutir. Cela se règle dans `prod.py` ou par variable d'environnement (à confirmer avec le client).
  - `ApiForgottenPasswordMail` répond 401 pour une adresse inconnue : cela permet de savoir quelles adresses existent (énumération). Non modifié.

### F-1. Contrôle de propriété des API qui désignent une entreprise (24/10/2026)
- **Décision** : autorisation de modifier le code donnée par Yassir.
- **Problème** : depuis S-1, il fallait être connecté, mais **n'importe quel utilisateur connecté** pouvait agir sur l'entreprise d'un autre en changeant le SIRET dans la requête : modifier sa fiche, ses descriptions, ses collaborateurs (y compris s'attribuer le rôle de propriétaire), importer des collaborateurs en CSV, créer des options d'abonnement (`create_options`, `create_sub_start_option`). Plusieurs vues filtraient déjà par entité (`EntitiesTree`), mais n'importe quel **lecteur** pouvait modifier.
- **Fichiers modifiés** :
  - `accounts/permissions.py` (nouveau) : `find_structure` (SIRET puis DUNS), `has_structure_access`, `is_structure_owner`, `owns_entity`, `structure_for_member`, `structure_for_owner`.
  - `accounts/dashboard/views_api.py` : les vues ci-dessous utilisent ces aides.
  - `mixity/dashboard/views_api.py` : `ApiSubscriptionOption` et `ApiSubscriptionPack`.
  - `accounts/test_structure_ownership.py` (nouveau) : 16 tests.
- **Règles** (alignées sur l'interface, dont les menus de gestion ne sont visibles que si `membership.is_owner`) :
  - lecture (`get_structure_entities`, `get_structure_description`, `subscription-pack`, `subscription-option`) : membre de l'entreprise, au niveau de l'entreprise ou d'une de ses entités ;
  - gestion (`get_collaborators`, `update_collaborator`, `delete_collaborator`, `invite_collaborators`, `update_structure_description`, `update_entity_infos`, `update_structure` en POST et PATCH, `create_options`, `create_sub_start_option`) : propriétaire (`is_owner`) ;
  - imports CSV de collaborateurs et d'entités : propriétaire de l'entreprise, ou de l'entité visée ou d'une entité parente (`owns_entity`) ;
  - l'équipe Mixity (`is_staff`) a tous les droits ; structure inconnue : 404 (au lieu d'une erreur 500) ; non autorisé : 403 ; pour les données d'abonnement, 404 afin de ne rien révéler.
- **Vérification** : `python manage.py test accounts.test_structure_ownership` : 16 tests, OK (propriétaire, membre simple, lecteur, propriétaire d'une autre entreprise, équipe Mixity ; désignation par DUNS ; structure inconnue ; un lecteur ne peut pas se promouvoir ; un tiers ne peut pas supprimer un collaborateur, inviter, modifier la description, modifier la structure, créer des options, importer un CSV). Contrôle de non-régression : avec les anciennes vues, 14 tests sur 16 échouent (12 échecs, 2 erreurs).
- **Risques et limites** :
  - Un utilisateur qui n'est pas marqué `is_owner` mais qui utilisait ces écrans ne pourra plus les utiliser. En base, les propriétaires sont nombreux (854 au niveau entreprise, 928 au niveau entité) ; 4 comptes sont à la fois `is_owner` et `is_reader` et restent traités comme propriétaires, comme dans l'interface.
  - Pas de vérification sur `ApiValidateCoupon` (un utilisateur connecté peut tester des codes promotionnels) ni sur `ApiCreateStructureWithPack` (crée une nouvelle entreprise, refuse un SIRET existant).
  - Les vues déjà protégées par un mixin dans `mixity/dashboard`, `act`, `lead` et `sirh` n'ont pas été revues une à une dans ce lot.
  - Les 4 000 lignes de `mixity/dashboard/views_api.py` méritent un audit de propriété complet dans un second temps.

### F-2, F-3, F-4 et PAY-2. Quatre défauts rapides (24/10/2026)
- **Décision** : autorisation de modifier le code donnée par Yassir.
- **F-2** `ApiGetCompanyName` (`accounts/dashboard/views_api.py`) renvoyait toujours une erreur 500 : `user.structures.length` n'existe pas. Remplacé par `user.structures.order_by("pk").first()`.
- **F-3** `scoring/views.py` (`EvaluationFill.get_success_url`, navigation entre cibles) : le dictionnaire de paramètres définissait `"target"` deux fois ; Python gardait la seconde valeur (`question.target`) et ignorait la première. Le doublon mort a été supprimé, **sans changer le comportement réel** (la valeur effective était déjà `question.target`, qui est logiquement la cible suivante).
- **F-4** `ApiSubscriptionPack` : `except SubscriptionPack.DoesNotExist():` (avec parenthèses) ne pouvait jamais servir, et `.first()` ne lève pas d'exception ; la vue renvoie maintenant 404 quand il n'y a pas de pack (corrigé avec F-1).
- **PAY-2** `subscriptions/models.py` : `SubscriptionOption.stripe_price_id` utilisait `settings` sans l'importer (`NameError`) ; ajout de `from django.conf import settings`.
- **Vérification** : les tests de F-1 couvrent F-4 ; `python manage.py check` sans erreur ; l'import de `settings` est vérifiable par un appel de la propriété. F-2 et F-3 : pas de test dédié ajouté (F-3 ne change pas le comportement).
- **À faire ensuite** : F-5 (gestion des erreurs), F-6 (webhook Sentry), T-1, T-2, TEST-1, puis les points d'interface.

### F-5 et F-6. Gestion des erreurs, webhooks, routes masquées et mixins mal placés (24/10/2026)
- **Décision** : autorisation de modifier le code donnée par Yassir.
- **Problèmes** :
  - **Webhooks inatteignables** : `sentry-webhook/` et `logentries-webhook/` étaient déclarés dans `mixity/urls.py` **après** la route `<slug:slug>/`, qui intercepte tout chemin d'un seul mot : les requêtes étaient redirigées vers la connexion (302) et n'atteignaient jamais le code. Les deux outils internes `google-sheets-data-check/` et `question-type-generator/` sont dans le même cas.
  - Webhook Sentry : lisait le JSON avant de vérifier la signature, comparait les signatures sans fonction à temps constant, plantait (500) si `SENTRY_CLIENT_SECRET` n'était pas défini, ne gérait pas un JSON invalide ni une panne de Google Chat. Webhook Logentries : aucun contrôle et appel externe sans délai d'attente.
  - **Mixins de contrôle mal placés** : en plus des 7 vues API déjà corrigées (S-2), `GoogleSheetsDataCheckView` et `QuestionTypeGeneratorView` (`mixity/views.py`) déclaraient `(TemplateView, LoginRequiredMixin, UserPassesTestMixin)` : le contrôle « équipe Mixity seulement » ne s'exécutait jamais. Même défaut pour `DashboardRegisterStartView` (`accounts/dashboard/views.py`).
  - **9 appels `requests` sans délai d'attente** (ADP, Webflow, Segment) : un service lent pouvait bloquer un processus indéfiniment.
  - **15 `except:` nus** (`mixity/serializers.py`, `accounts/models.py`, `scoring/models.py`, `scoring/serializers.py`, `sirh/indicators.py`), qui interceptent même les arrêts du programme.
  - **Inscription** : l'erreur réelle était masquée par un message unique ; une adresse déjà utilisée n'était pas distinguée ; un champ `is_newsletter` absent faisait échouer l'inscription (valeur `NULL` refusée par la base) ; `login`, `register` et `forgotten_password_mail` plantaient (500) si le champ `email` manquait.
- **Fichiers modifiés** :
  - `mixity/urls.py` : les deux webhooks sont déclarés avant `<slug:slug>/` ; les deux outils internes ne sont **volontairement pas déplacés** (voir limites).
  - `mixity/sentry_webhook.py`, `mixity/logentries_webhook.py` : réécriture des contrôles.
  - `mixity/views.py`, `accounts/dashboard/views.py` : ordre des classes de base corrigé.
  - `mixity/services/segment.py` (délai 10 s), `scoring/management/commands/export_to_webflow.py` (30 s), `sirh/services.py` (30 s).
  - 15 `except:` devenus `except Exception:`.
  - `accounts/dashboard/views_api.py` : inscription (adresse existante : 409 « Email already used » ; erreur réelle journalisée par `logger.exception` sans l'adresse ; `is_newsletter` facultatif ; `email` manquant : 400) ; même protection pour `login` et `forgotten_password_mail`.
  - Tests ajoutés : `mixity/test_webhooks.py` (9), `mixity/test_views_protection.py` (1), `accounts/test_register.py` (5).
- **Comportement du webhook Sentry** : réponse 404 si le secret ou l'adresse Google Chat ne sont pas configurés ; 400 si la signature est fausse ou absente (comparée avec `hmac.compare_digest`, avant toute lecture du contenu) ou si le JSON est invalide ; 502 si Google Chat est injoignable ; délai 10 s. Logentries : 404 si l'adresse n'est pas configurée.
- **Vérification** :
  - 15 tests (webhooks, protection des vues, inscription) : OK.
  - Le test `test_views_protection` parcourt toutes les vues routées et échoue si un mixin de contrôle est placé après la vue de base ; avec l'ancien `accounts/dashboard/views.py`, il échoue (1 défaut détecté).
  - Un balayage automatique ne trouve plus aucun appel `requests` sans `timeout` dans le code hors tests, migrations et scripts d'import ; `python manage.py check` sans erreur.
- **Risques et limites** :
  - Les webhooks Sentry et Logentries, maintenant atteignables, ne répondent que si `SENTRY_CLIENT_SECRET` et `GOOGLECHAT_WEBHOOK_URL` (ou `GOOGLECHAT_LOGENTRIES_WEBHOOK_URL`) sont définis. Le webhook Logentries n'a pas de signature : il faudrait en définir une côté Logentries si on le réactive.
  - **Les deux outils internes restent masqués par `<slug:slug>/`** (donc inaccessibles, comme avant). Leurs contrôles sont maintenant corrects, mais les rendre accessibles relève du point U-4 (routes) et d'une décision du client : ce sont des outils pour l'équipe interne qui n'ont pas de raison d'être exposés tant que Google Sheets n'est pas utilisé.
  - L'inscription renvoie maintenant 409 pour une adresse déjà utilisée ; le front affiche toujours son message générique tant que U-5 (message précis) n'est pas fait.
  - `except Exception:` conserve le comportement actuel (renvoyer `None`) : les erreurs sont toujours masquées silencieusement dans ces 15 endroits, mais plus les arrêts du programme. Les journaliser serait une amélioration ultérieure.
  - Les délais d'attente (10 et 30 secondes) sont des valeurs raisonnables, à ajuster si Webflow ou ADP sont plus lents.

### T-1, T-2 et TEST-1. Traductions en local et tests en échec (24/10/2026)
- **Décision** : autorisation de modifier le code donnée par Yassir.
- **T-1. Le changement de langue n'avait aucun effet en local**
  - **Cause** : Django traduit à partir des fichiers compilés `.mo` (ignorés par git). L'image Docker les compile, mais `docker-compose.yml` monte le dossier du projet sur `/app` et masque ces fichiers.
  - **Changement** : `docker-compose.yml`, service `web` : la commande devient `/bin/sh -c "python manage.py compilemessages ; python manage.py runserver 0.0.0.0:8000"`. Si la compilation échoue, le serveur démarre quand même.
  - **Vérification** : après `docker compose up -d web` (serveur prêt en 15 s), `gettext("ND*")` renvoie `ND*` en français, **`UA*` en anglais** et **`N / A*` en espagnol** ; les fichiers `.mo` apparaissent dans `mixity/locale/*/LC_MESSAGES/` et `git status` ne les signale pas (ignorés).
  - **Effet de bord** : les 4 tests de formats de nombres (`NumFormatTemplateTagTest`) qui échouaient depuis le départ passent maintenant : leur échec venait de cette même cause (traductions absentes), pas de la désactivation de fast-i18n comme je l'avais supposé.
  - **Limite** : sans effet en production (les traductions y sont compilées à la mise en production, `make I18N:compile`).
- **T-2. Doublons de noms dans les fichiers de traduction** (point D4 de l'audit)
  - **Vérification avant correction** : `translator.get_registered_models()` montre que `Question`, `Choice`, `Structure` et `BusinessLine` sont bien enregistrés avec tous leurs champs traduits. Le décorateur `@register` enregistre chaque classe au moment où elle est définie : **le doublon de noms ne cassait donc rien**. Mon hypothèse de l'audit (« certains champs traduits peuvent manquer ») était fausse.
  - **Changement** (lisibilité seulement) : `scoring/translation.py` : la seconde `QuestionTranslationOptions` devient `ChoiceTranslationOptions` ; `accounts/translation.py` : la seconde `StructureTranslationOptions` devient `BusinessLineTranslationOptions`. Aucune migration ni changement de comportement.
- **TEST-1. Les 3 tests de nombre de requêtes**
  - **Cause** : le chargement de la page d'accueil (`home`) exécute une requête de moins qu'au moment où les tests ont été écrits (37 au lieu de 38, et 39 au lieu de 40). Cet écart existait déjà avant toute correction.
  - **Changement** : `mixity/dashboard/tests.py` (`nb_requests=38` devient `37`) et `scoring/tests.py` (`assertNumQueries(38)` devient `37`, `assertNumQueries(40)` devient `39`).
  - **Vérification** : `HomeTest`, `DashboardTest`, `MultiEntitiesTest` et `NumFormatTemplateTagTest` : 12 tests, OK.
  - **Limite** : je n'ai pas identifié la requête qui a disparu ; le nombre baisse (la page est plus économe), mais ces tests figent des nombres exacts et resteront fragiles.
- **Résultat d'ensemble** : suite complète à ce stade : 149 tests, **seulement les 3 tests de requêtes en erreur avant TEST-1, tous corrigés ici** (les 7 échecs du départ sont résolus).

### PAY-3. Webhook Stripe plus robuste (24/10/2026)
- **Décision** : autorisation de modifier le code donnée par Yassir. Le paiement n'est plus utilisé selon le client : on ne traite que la robustesse (PAY-1, l'incohérence du modèle, reste ouvert).
- **Problème** : `payments/views.py::stripe_webhook` plantait en erreur 500 si l'en-tête `Stripe-Signature` manquait (`KeyError`), si la session était inconnue (`DoesNotExist`), ou si la session n'était liée à aucun abonnement (`AttributeError`). Stripe réessaie alors indéfiniment. Il acceptait aussi les requêtes GET.
- **Changement** : `@require_POST` ; en-tête de signature absent : 400 ; session inconnue : journal d'avertissement et réponse 200 ; session sans abonnement : journal d'erreur et réponse 200, **sans rien activer**.
- **Fichiers** : `payments/views.py`, `payments/test_webhook.py` (nouveau, 5 tests).
- **Vérification** : 5 tests OK (GET refusé en 405, en-tête manquant 400, signature invalide 400, sessions inconnues 200, session sans abonnement 200 et statut inchangé).
- **Limite** : l'activation automatique d'un abonnement après paiement **ne fonctionne toujours pas** (PAY-1) : la session de paiement est enregistrée avec une option d'abonnement (`subscriptionOption`) alors que le webhook attend un abonnement (`subscription`). À traiter seulement si le client réactive le paiement.

### U-1 (contournement local). Tableau de bord bloqué sur « Chargement » (24/10/2026)
- **Décision** : le correctif du code front n'est pas fait. Le défaut est le `https://` écrit en dur devant le nom d'hôte de l'API dans une douzaine de fichiers (`mixity/dashboard/js/Home.js:76`, `accounts/dashboard/js/CollaboratorLogin.js`, `lead/js/Lead.js`, `lead/js/Overview.js`, `scoring/dashboard/js/AssessPage.js`, `EvaluationSurvey.js`, `EvaluationCriteriasPage.js`, `CollaboratorScoreCard.js`, `includes/AssessSheetDownload.js`, `includes/CollaboratorsImporter.js`, `scoring/pdf_generator/js/AssessPage_Pdf.js`, soit une vingtaine d'endroits). Il est invisible en production (le site y est en HTTPS) et sa correction impose de **recompiler les 221 fichiers de `mixity/static/dist`** et de les valider un par un : risque et bruit disproportionnés pour un gain limité à l'environnement local.
- **Contournement sans toucher au code du client** : `docker-compose.override.yml` (fichier local ignoré par git) ajoute un service `https` (image `caddy:2`) qui sert l'application sur **https://localhost:8443** et conserve l'en-tête `Host`. Le front appelle alors `https://localhost:8443/api/...`.
- **Vérification** : `/api/url/` renvoie `"localhost:8443"` ; `category`, `membership`, `first-five-actions`, `first-five-solutions` répondent 200 en HTTPS ; la page d'accueil du tableau de bord répond 200.
- **Utilisation** : ouvrir https://localhost:8443 et accepter l'avertissement de certificat auto-signé du navigateur.
- **Si le client veut le vrai correctif** : remplacer `'https://' + x` par `window.location.protocol + '//' + x` dans ces fichiers, puis `yarn build` et validation des pages principales (environ 0,5 à 1 jour avec la recette).

## Bilan de la Priorité 2 (24/10/2026)

| Point | Résultat |
|---|---|
| S-8 (nouveau) Mot de passe oublié sans jeton | corrigé, 6 tests + essai réel de bout en bout |
| F-1 Contrôle de propriété des API | appliqué, 16 tests |
| F-2, F-3, F-4, PAY-2 Défauts rapides | corrigés |
| F-5 Gestion des erreurs (délais, `except`, inscription) | corrigé, 5 tests |
| F-6 Webhooks Sentry / Logentries + routes masquées + mixins | corrigé, 10 tests |
| PAY-3 Webhook Stripe | robuste, 5 tests ; PAY-1 (activation) non traité |
| T-1 Traductions en local | corrigé (compilation au démarrage) |
| T-2 Doublons de noms de traduction | n'était pas un défaut ; classes renommées |
| TEST-1 Tests en échec | les 7 tests du départ sont corrigés |
| U-1 Tableau de bord bloqué en local | contourné (proxy `https://localhost:8443`) ; correctif du code non fait |
| U-2, U-3, U-4, U-5, PAY-1 | **non traités** : décisions du client nécessaires (voir ci-dessous) |

**Suite de tests complète** (`python manage.py test --parallel 4`, réglages de test) : **154 tests, tous réussis** (au départ : 89 tests dont 7 en échec ; ajout de 65 tests). Un contrôle en conditions réelles sur l'instance locale confirme : visiteur refusé (403), propriétaire accepté (200), autre entreprise refusée (403), SIRET inconnu (404), inscription avec adresse existante (409), webhook non configuré (404).

**Nouveaux fichiers de test** : `accounts/test_forgotten_password.py`, `accounts/test_structure_ownership.py`, `accounts/test_register.py`, `mixity/test_webhooks.py`, `mixity/test_views_protection.py`, `payments/test_webhook.py` (en plus de ceux de la Priorité 1). **Nouveau module** : `accounts/permissions.py`.

**Fichiers modifiés pendant la Priorité 2** : `accounts/views.py`, `accounts/dashboard/views_api.py`, `accounts/dashboard/views.py`, `accounts/translation.py`, `scoring/translation.py`, `scoring/views.py`, `scoring/tests.py`, `mixity/dashboard/views_api.py`, `mixity/dashboard/tests.py`, `mixity/views.py`, `mixity/urls.py`, `mixity/sentry_webhook.py`, `mixity/logentries_webhook.py`, `mixity/services/segment.py`, `scoring/management/commands/export_to_webflow.py`, `sirh/services.py`, `sirh/indicators.py`, `accounts/models.py`, `scoring/models.py`, `scoring/serializers.py`, `mixity/serializers.py`, `payments/views.py`, `subscriptions/models.py`, `docker-compose.yml`. Fichier local ignoré par git : `docker-compose.override.yml` (service `https`).

**Décisions du client nécessaires pour la suite**
1. **U-2 / U-3** : où doivent mener les boutons des pages d'atterrissage (« Qu'est-ce que Mixity Diag ? », « Demander une démo », « Voir un exemple »...) ? Ces pages vivent sur le site Webflow en cours de restauration, et le contenu de « Voir un exemple » est à définir.
2. **U-4** : faut-il préfixer les adresses des entreprises (`/<slug>/` devient par exemple `/e/<slug>/`) ? Cela évite que toute adresse d'un seul mot soit prise pour une entreprise, mais touche de nombreuses routes.
3. **U-1** : le correctif du `https://` en dur dans le front demande de recompiler les 221 bundles (environ 0,5 à 1 jour avec la recette). Utile surtout pour le développement local.
4. **PAY-1** : le paiement est-il réactivé ? Sinon, l'activation automatique d'un abonnement restera non fonctionnelle.
5. **Domaine de production** : confirmer `app.mixity.io` et corriger `ENVIRONMENT_DOMAIN` (`www.app.mixity.io`) si besoin, faute de quoi les liens des e-mails (mot de passe oublié, invitations) pointent vers un domaine inexistant.

### U-2 et U-3. Boutons des pages d'atterrissage : liens morts et boutons inactifs (24/10/2026)
- **Décision** : demandée par Yassir (« les boutons ne marchent toujours pas »). Elle remplace la mention « décision du client nécessaire » : le site marketing réel existe et ses pages ont été retrouvées.
- **Problème** : les boutons des pages `/diag/landing/`, `/human/landing/`, `/measure/landing/`, `/pilot/landing/` et `/solver/landing/` pointaient vers des adresses relatives qui n'existent pas dans l'application (`/evaluation/diag/`, `/evaluation/human/`, `/contact/`, `/pricing/`, `/360/`) et menaient à une erreur 404 ; six boutons « Voir un exemple » n'avaient aucune action ; sur la page Measure, les cartes « Mixity Diag » et « Mixity Human » menaient toutes à la page 360 ; sur la page Pilot, « Demander une demo » menait aux tarifs.
- **Recherche des bonnes cibles** : le site `https://www.mixity.io` est en ligne (200). Ses pages (confirmées une à une) : `/solutions/diag`, `/solutions/human`, `/solutions/360`, `/solutions/scan`, `/solutions/start`, `/demo`, `/tarifs`, `/partenaires`, `/empreintes` (exemples de résultats publiés), `/faq`, `/contact`.
- **Correspondance retenue** (une seule table dans `landing/dashboard/js/marketing.js`, facile à changer) :

| Bouton | Page de destination |
|---|---|
| Qu'est-ce que Mixity Diag ? | `/solutions/diag` |
| Qu'est-ce que Mixity Human ? | `/solutions/human` |
| Qu'est-ce que 360 DEI ? | `/solutions/360` |
| Demander une demo | `/demo` |
| Prendre un abonnement | `/tarifs` |
| S'inscrire (solutionneur) | `/partenaires` |
| Voir un exemple (6 boutons) | `/empreintes` |

- **Fichiers modifiés** :
  - `mixity/settings/base.py` : nouveau réglage `MARKETING_SITE_URL` (variable d'environnement du même nom, `https://www.mixity.io` par défaut).
  - `landing/templates/dashboard/landing_{diag,human,measure,pilot,solver}.html` : exposent `var marketing_site_url`.
  - `landing/dashboard/js/marketing.js` (nouveau) et les cinq `Landing*.js` : `openMarketingPage('diag' | 'human' | 'measure360' | 'demo' | 'pricing' | 'partners' | 'example')`.
  - `mixity/static/dist/js/dashboardlanding{diag,human,measure,pilot,solver}components-1.0.0.js` : **seuls ces 5 bundles compilés sont remplacés** ; les 216 autres fichiers de `dist` sont inchangés.
  - `mixity/templates/500.html` : 20 liens relatifs morts remplacés par les adresses du site marketing.
  - `mixity/settings/dev.py` : la barre de débogage démarre repliée (`SHOW_COLLAPSED`).
  - `landing/test_landing.py` (nouveau, 3 tests).
- **Compilation** : `webpack --mode production` exécuté dans le conteneur `webpack` avec `--output-path /tmp/wp_out` (le plugin de nettoyage de webpack vide son dossier de sortie : on ne l'a jamais dirigé vers `mixity/`). Un recompilation complète ne reproduit pas à l'identique les fichiers livrés (empreintes différentes, bundles légèrement plus petits), c'est pourquoi on ne copie que les cinq bundles nécessaires.
- **Vérification dans un vrai navigateur** (Chromium via Playwright dans le conteneur, site marketing simulé pour ne regarder que l'adresse demandée) : les **16 boutons** concernés mènent à la page attendue, y compris « Demander une demo » (diag, measure, pilot), « Prendre un abonnement », « S'inscrire » et les 6 « Voir un exemple ». `landing.test_landing` : 3 tests OK (adresse injectée dans les 5 pages, adresse par défaut, absence des anciens liens dans les bundles).
- **Cause du « ça ne marche toujours pas » en local** : la barre de débogage Django, dépliée, recouvre le coin supérieur droit et **intercepte les clics** sur les boutons colorés (« Demander une demo », « S'inscrire »). Elle n'existe pas en production. Elle démarre maintenant repliée.
- **Risques et limites** :
  - Les destinations sont mon choix à partir des pages du site marketing ; **à faire valider par Mathieu** (notamment « Voir un exemple » vers `/empreintes` et « S'inscrire » vers `/partenaires`).
  - Les bundles de ces cinq pages ont été recompilés avec la chaîne d'outils de l'image Docker, pas celle de l'origine : un test visuel de ces cinq pages en préproduction est conseillé.
  - Le site Webflow est en cours de restauration : si une page change d'adresse, il suffit de modifier la table de `marketing.js` ou de renseigner `MARKETING_SITE_URL`, puis de recompiler.
  - Les autres défauts du même type (le `https://` en dur dans l'API, voir U-1) restent à traiter.

### PERF-1, PERF-2, UX-1. Chargement rapide et indicateur animé (24/10/2026)
- **Décision** : demandée par Yassir (« améliorer le chargement pour qu'il soit rapide, et le design du chargement, avec animation »).
- **Mesures avant correction** (instance locale, page d'accueil du tableau de bord, base de production) : `/` 1,3 à 2,5 s ; `/api/category/` 0,4 s ; `/api/first-five-actions/` 0,4 à 2,4 s ; `/api/first-five-solutions/` 1,2 s ; `/api/entity/` 0,71 s. Le temps SQL était négligeable (0,03 s sur 1,9 s pour `/`) : la perte venait de Python.

**PERF-1. Barre de débogage Django facultative en développement**
- **Cause** : le profilage (`cProfile`) montre que la barre de débogage consommait plus de la moitié du temps (1,08 s sur 2,55 s pour `/`, environ 25 ms par requête SQL, même sur une requête d'API triviale). Elle n'existe pas en production.
- **Changement** : `mixity/settings/dev.py` : `USE_DEBUG_TOOLBAR = os.environ.get("DEBUG_TOOLBAR") == "1"` ; l'application et le middleware ne sont ajoutés que dans ce cas. `mixity/urls.py` : les routes `theme/` et les médias locaux ne dépendent plus de la barre ; seule la route `__debug__/` en dépend.
- **Mesure après** : tout le tableau de bord (6 appels) passe de **4,14 s à 0,13 s** ; `/` 0,06 à 0,08 s, appels d'API 0,02 à 0,05 s.
- **Utilisation** : pour réactiver la barre, définir `DEBUG_TOOLBAR=1` dans l'environnement du service `web` (par exemple dans `docker-compose.override.yml`).

**PERF-2. Comptage des collaborateurs ayant répondu (`answer_count`)**
- **Cause** : `Evaluation.answer_count` et `get_filtered_collaborators_count` utilisaient une jointure avec `GROUP BY` / `HAVING` sur toutes les réponses, pour chaque évaluation du tableau de bord (plus de 40 ms par évaluation sur les grosses évaluations 360). Cela concerne aussi la production.
- **Changement** (`scoring/models.py`) : nouvelle fonction `count_collaborators_with_answers` fondée sur `EXISTS` (même sémantique : collaborateurs distincts avec au moins une réponse).
- **Vérification** : sur les **424 évaluations** de la base, **0 différence** entre l'ancienne et la nouvelle méthode ; temps cumulé 3,32 s contre 0,62 s ; `/api/entity/` passe de 0,71 s à 0,24 s (SQL 0,46 s à 0,03 s) ; 5 tests (`scoring/test_collaborators_count.py`).
- **Limite** : `/api/entity/` exécute encore environ 177 petites requêtes (une par évaluation et par relation : scores, objectifs, forces, faiblesses, tags). Elles ne coûtent plus que 0,03 s ; les regrouper (`prefetch_related`) demanderait de retoucher le sérialiseur et des propriétés du modèle, jugé non nécessaire.

**UX-1. Indicateur de chargement animé**
- **Problème** : 36 pages affichaient simplement le texte « Chargement » en haut de l'écran (parfois avec une marge de 40 % pour le décaler).
- **Changement** : composant `mixity/dashboard/js/includes/Loading.js` : anneau animé aux couleurs de la marque (`#8888E2`), libellé « Chargement… » qui respire et barre de progression qui défile, centrés dans la zone de contenu (le menu reste visible). Il affiche l'animation tant que l'état vaut « Chargement » (traduit) et, si la page y met un message d'erreur, un pictogramme et ce message (« Quelque chose s'est mal passé ! »), sans animation. Accessible (`role="status"` / `role="alert"`) et respectueux de `prefers-reduced-motion`. Styles inclus dans le composant (aucune feuille de style externe).
- **Pages concernées** (36 fichiers sources, 34 bundles compilés) : tableau de bord, pages d'atterrissage, pilotage (Lead, Overview), solutions et bonnes pratiques (6 listes), analyse de noms, évaluation (AssessPage, critères, enquête, création d'indicateur), état ADP, comptes (connexion, inscription, profil, mot de passe, invitations, structure). **Non modifié** : le générateur de PDF (`scoring/pdf_generator`), pour ne pas changer le rendu des rapports.
- **Page d'accueil** (`mixity/dashboard/js/Home.js`) : l'adresse de l'API est prise sur la page elle-même (`window.location`) au lieu d'appeler `api/url/` : **un aller-retour en moins** et plus de `https://` en dur pour cette page (elle fonctionne maintenant en HTTP simple, ce qui règle U-1 pour le tableau de bord).
- **Compilation** : `webpack --mode production --output-path /tmp/wp_out` dans le conteneur `webpack` ; seuls les 34 bundles contenant le nouveau composant sont copiés dans `mixity/static/dist/js` (les autres fichiers de `dist` ne bougent pas).
- **Vérification dans un vrai navigateur** (Chromium via Playwright) : tableau de bord complet en HTTP simple en 2,1 s depuis zéro (avant : bloqué) ; captures d'écran de l'animation et du message d'erreur ; 14 pages connectées et 3 pages visiteur chargées sans erreur JavaScript, l'animation disparaissant à la fin ; les 4 pages qui conservent un `https://` en dur (Lead, Overview, solutions, évaluation) se chargent via le proxy `https://localhost:8443`. 2 tests (`mixity/test_loading.py`).
- **Risques et limites** :
  - Les 34 bundles ont été recompilés avec la chaîne d'outils de l'image Docker (légèrement différente de l'origine) : **à valider en préproduction** sur les pages principales avant déploiement.
  - Le délai d'affichage reste lié à la chaîne d'appels de la page d'accueil (plusieurs appels successifs) ; la réécrire en appels parallèles n'a pas été fait, le risque de régression étant élevé pour un composant de plus de 1 000 lignes.
  - Le texte du chargement reste celui des traductions existantes (« Chargement »).

### DEV-1. Lien de confirmation d'inscription en `http://` derrière le proxy HTTPS local (24/10/2026)
- **Décision** : demandée par Yassir (« quand je clique sur valider mon email j'obtiens : Client sent an HTTP request to an HTTPS server »).
- **Problème** : en s'inscrivant sur `https://localhost:8443` (proxy Caddy local), le mail de confirmation contenait `http://localhost:8443/account/register/step2?...`. Django construit ces liens avec `request.build_absolute_uri`, donc à partir de la requête qu'il reçoit ; le proxy lui parle en HTTP simple vers `web:8000`, et le lien sortait en `http://`, que le proxy HTTPS refuse. Même défaut pour les liens de « mot de passe oublié » et d'invitation.
- **Changement** : `mixity/settings/dev.py` : `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`. Caddy ajoute cet en-tête ; Django sait alors que la requête d'origine était en HTTPS. La production définit déjà ce réglage (`prod.py`).
- **Vérification** : inscription par `https://localhost:8443` : le lien du mail est en `https://localhost:8443/account/register/step2?...` et s'ouvre (200) ; inscription par `http://localhost:8000` : le lien reste en `http://localhost:8000/...`.
- **Limite** : les mails déjà envoyés gardent l'ancien lien (remplacer `http://` par `https://` à la main, ou refaire l'inscription) ; le lien de confirmation expire au bout de 10 minutes (`SESAME_MAX_AGE`).

### NOUVEL UTILISATEUR. Parcours constaté et défaut trouvé (24/10/2026)
- **Question de Yassir** : comment un utilisateur qui vient de créer son compte accède-t-il aux fonctions de l'application, au lieu des seules pages statiques ?
- **Parcours vérifié** : inscription et confirmation de l'e-mail ; création de l'entreprise sur `/structure/add/` (API `create_structure` : entreprise, entité principale, propriétaire, pack d'abonnement actif) ; choix d'une offre (API `create_options`, **offre créée inactive**) ; **validation par l'équipe Mixity** dans l'administration (`Subscriptions > Subscription options`, action « Valider les offres » : active l'offre, génère l'évaluation, envoie le mail au propriétaire) ; l'utilisateur voit alors « Mixity Diag, En cours, Reprendre le questionnaire ».
- **Données de test créées en local** : entreprise « Société de Test Locale » (structure 899), dont `nomember.test@example.com` est propriétaire ; offre Diag activée ; évaluation 937 « en cours ».
- **Défaut trouvé (non corrigé)** : le bouton « Reprendre le questionnaire » mène à `/scoring/evaluation/937/confirm/`, qui plante (`KeyError: 582`, `scoring/views.py` ligne 2531). `EvaluationConfirm.get_context_data` cherche, pour chaque entité accessible, une évaluation « globale » (`sheet__type__is_collaborator=False`) ; or, dans les données, le type `mixity_evaluation_diag` est marqué `is_collaborator = vrai`, donc l'entité n'a aucune évaluation correspondante et l'accès au dictionnaire échoue. Pour les évaluations de ce type, `generate_answers()` ne crée aucune réponse (retour anticipé). Publicis, qui a des évaluations validées, n'affiche pas ce bouton.
- **À décider avec le client** : la page doit-elle être rendue tolérante, et comment un propriétaire remplit-il un Diag (questionnaire destiné à des collaborateurs invités) ?

### WORKER-1. Le worker RQ s'arrêtait au bout d'une minute : aucun score n'était calculé (28/10/2026)
- **Décision** : demandée par Yassir (« fix the bug to calculate, i need it to be working »).
- **Symptôme** : après « Valider votre évaluation », le tableau de bord restait vide. Le conteneur `worker` s'arrêtait environ 60 s après son démarrage avec `Redis connection timeout, quitting...`. Les tâches `do_update_scoring` étaient mises en file mais jamais exécutées.
- **Cause** : `redis` n'était pas épinglé dans `requirements.txt`, donc l'installation prenait la dernière version (**redis-py 8.1.0**). Depuis redis-py 6, les connexions ont un délai par défaut de 5 s (`redis/_defaults.py` : `DEFAULT_SOCKET_TIMEOUT = 5`). RQ 1.16 ne pose son propre délai que si aucun n'est défini (`rq/worker.py:301`) ; son attente bloquante (`BLPOP`, jusqu'à 405 s) dépassait les 5 s et le worker s'arrêtait. **Heroku installe depuis le même fichier : le worker de production est très probablement touché aussi.** Cela explique aussi l'arrêt constaté en V-1 et non reproduit à l'époque.
- **Fichier modifié** : `requirements.txt` : ajout de `redis~=5.2.1` (version prise en charge par RQ 1.16 et `django-redis` 5.0).
- **Vérification** :
  - redis 5.2.1 installé dans les conteneurs `web` et `worker` ; worker actif plus de 2 min 30 sans message d'arrêt (avant : arrêt à 1 min).
  - Parcours réel : évaluation 938 (Entrepris1) remplie avec les réponses de Piex (même questionnaire), validée par la vue `evaluation_validate` : tâche exécutée par le worker en 0,5 s (`score = 19.60`, `Job OK`), scores par dimension enregistrés.
- **Limite** : en local, l'image Docker contient encore redis 8 ; la version 5.2 a été installée dans les conteneurs en cours. Après un `docker compose build`, l'image suivra `requirements.txt`.
- **À vérifier après déploiement** : dyno `worker` actif sur Heroku (onglet Resources) et absence de `Redis connection timeout` dans les journaux.

### DIAG-1. Les nouveaux Diag étaient créés sans aucune question (28 et 29/10/2026)
- **Problème** : en base (copie de production du 23/10), le type `mixity_evaluation_diag` a `is_collaborator = True`. `Evaluation.generate_answers()` sort alors immédiatement : les nouveaux Diag ont 0 question, le client ne peut rien remplir et n'obtient jamais de score.
- **Analyse** : 99 Diag ont des réponses, toutes rattachées à l'entreprise (`collaborator` vide) : le Diag est bien le questionnaire de l'entreprise, conforme à la migration 0360 qui crée ce type avec `is_collaborator=False`. Le drapeau a été modifié après coup. Les seuls Diag vides sont les 3 évaluations de test créées en local (936, 937, 938) : aucun client réel n'est touché dans la copie du 23/10.
- **Fichiers modifiés** : `scoring/migrations/0474_diag_not_collaborator.py` (nouveau) : migration de données qui remet `is_collaborator = False` pour `mixity_evaluation_diag`. Elle s'appliquera seule au déploiement (`release: ... migrate` dans le `Procfile`) ; plus besoin d'intervention manuelle dans l'admin de production.
- **Vérification** :
  - base locale remise à `True` (état de production), `migrate` : `Applying scoring.0474_diag_not_collaborator... OK`, valeur passée à `False` ; `makemigrations --check` : aucune modification détectée.
  - Questions générées pour 936, 937 et 938 (97 à 127 réponses, 6 catégories de score) ; `/scoring/evaluation/937/confirm/` répond 200 pour le propriétaire.
- **À faire après déploiement** : si un Diag de production a été créé vide entre-temps, utiliser l'action d'admin « Regénérer le questionnaire » sur cette évaluation.

### M-2. Fichiers Excel, CSV et PDF sur Cloudinary (complément de M-1) (29/10/2026)
- **Problème** : M-1 ne corrigeait que le stockage par défaut (images). Les champs `pdf_sheet`, `questions_sheet`, `export` et `raw_data` utilisent `RawStorage` (`scoring/models.py:80`), qui héritait directement de la bibliothèque et gardait le dossier dans l'adresse : **tous ces fichiers renvoyaient 404**.
- **Vérification préalable sur le vrai compte Cloudinary (`mixity`)**, par les adresses publiques, sans clé : images 100 % accessibles avec M-1 (logos 157/157, presse 132/132, empreintes 159/159, partages 90/90, vignettes 95/95, labels 20/20, experts 2/2, photos 77/82) ; fichiers bruts 0 % accessibles avant correction. Les PDF sont rangés sur Cloudinary comme des **images** (et non comme fichiers bruts).
- **Fichiers modifiés** :
  - `mixity/storage.py` : nouvelle classe `FlatRawCloudinaryStorage` (même principe que M-1, type `raw`) ; les fichiers `.pdf` sont servis par `image/upload`.
  - `scoring/models.py` : `RawStorage` hérite de `FlatRawCloudinaryStorage` (même nom de classe : aucune migration).
  - `mixity/test_storage.py` : 4 tests ajoutés (10 au total).
- **Vérification (vrai Cloudinary)** : Excel `questions_sheet` 130/337 (les 207 autres n'existent pas sur le compte), exports 2/2, CSV 15/15. PDF : 79 répondent **401** (diffusion des PDF bloquée par le réglage du compte), 16 n'existent pas.
- **Actions du client** :
  - Cloudinary, Settings > Security : cocher « Allow delivery of PDF and ZIP files ».
  - Fichiers absents du nouveau compte (5 photos de profil, 207 questionnaires Excel, 16 PDF) : à recopier depuis l'ancien compte s'il est encore accessible.

### PAY-4. La carte « Start » de l'inscription bloquait sur la page de paiement (29/10/2026)
- **Problème constaté pendant le test d'inscription** : à l'étape « Inscription confirmée ! », la carte « Mesure instantanée… offre Start » crée l'entreprise puis envoie sur `/payments/<id>/pay/`, qui charge Stripe. Sans clé Stripe (`/payments/config/` renvoie une clé vide), la page reste indéfiniment sur « Chargement ». C'est ce qui arriverait en production dès que les clés Stripe seront retirées ou renouvelées (recommandé en P-1), le paiement n'étant plus utilisé.
- **Fichiers modifiés** :
  - `payments/views.py` (`StructurePaymentView.dispatch`) : si `STRIPE_PUBLIC_KEY` est vide, redirection vers le tableau de bord de l'entreprise avec le message « Votre demande a bien été enregistrée. L'équipe Mixity va activer votre offre et vous prévenir par e-mail. ». L'offre reste inactive en attente de « Valider les offres », comme pour le Diag. Avec une clé Stripe, comportement inchangé.
  - `mixity/templates/base_dashboard.html` : les messages Django s'affichent aussi sur les pages sans `dashboard_header` (le tableau de bord React ne les montrait pas).
  - `payments/test_payment_page.py` (nouveau) : 2 tests.
- **Vérification** : avec le compte `testme@gmail.com` (entreprise « org1 », 901) : `/payments/901/pay/` → 302 vers `/org1-main/`, message affiché une fois puis effacé.
- **À décider avec le client** : faut-il garder cette carte (offre Start sans paiement) ou la retirer ? Autre constat : un nouvel utilisateur n'a **aucun bouton** pour créer son entreprise hors de ce parcours ; le lien « Ajouter une structure » (`dashboard_sider.html`) n'est visible que par l'équipe Mixity (staff).

### U-1 (correctif définitif). Adresse de l'API en `https://` écrite en dur (29/10/2026)
- **Problème** : 24 endroits construisaient l'adresse de l'API avec `'https://' + ...` : en HTTP (local), les pages restaient sur « Chargement ».
- **Fichiers modifiés (17 sources)** : `act/js/` (SolutionsList, SolverSolutionsList, BestPracticesList, BestPracticesManagement, FavoritesList, FavoriteBestPracticesList, ElearningsList, ElearningDetails), `lead/js/Lead.js`, `lead/js/Overview.js`, `accounts/dashboard/js/CollaboratorLogin.js`, `scoring/dashboard/js/` (AssessPage, EvaluationSurvey, EvaluationCriteriasPage, CollaboratorScoreCard, includes/AssessSheetDownload, includes/CollaboratorsImporter) : `window.location.protocol + '//' + ...` (le protocole de la page). **Non modifié** : `scoring/pdf_generator` (rendu des rapports PDF inchangé).
- **Compilation** : `webpack --mode production --output-path /tmp/wp_out` dans le conteneur `webpack` ; 12 bundles copiés dans `mixity/static/dist/js` (actbestpractices, actbestpracticesmanagement, actfavoritebestpractices, actfavorites, actsolutions, actsolversolutions, assessdashboardhome, dashboardcollaboratorscorecard, evaluationcriterias, evaluationsurvey, lead, overviewlead). `collaboratorlogincomponents-1.0.0.js` n'est plus produit par la configuration webpack ni utilisé par aucun gabarit : laissé tel quel.
- **Vérification dans Chromium (Playwright)** : 9 pages (tableau de bord, Lead, Overview, 4 pages solutions et bonnes pratiques, évaluation, filtres) chargées en **HTTP** (`localhost:8000`) et en **HTTPS** (proxy `localhost:8443`) : toutes en 200, indicateur de chargement disparu, aucune requête en échec, aucune erreur JavaScript.

### MAIL-1. Les liens des e-mails pointaient vers un domaine inexistant (29/10/2026)
- **Problème** : en production, `ENVIRONMENT_DOMAIN = "www.app.mixity.io"` (`mixity/settings/prod.py`). Ce nom **n'existe pas dans le DNS** (vérifié avec `dig`), alors que l'application répond sur `app.mixity.io` (Heroku). Les liens construits avec ce réglage (mot de passe oublié, e-mails de comptes, factures, `mixity/utils.py`) étaient donc inutilisables. La synthèse PDF chargeait aussi le favicon, les icônes et l'empreinte depuis `www.app.mixity.io` (et l'empreinte depuis un ancien chemin `/mediafiles/...`).
- **Fichiers modifiés** :
  - `mixity/settings/prod.py` : `ENVIRONMENT_DOMAIN` vaut `app.mixity.io` par défaut, modifiable par la variable d'environnement `ENVIRONMENT_DOMAIN`.
  - `scoring/models.py` (`get_synthesis_template`) : l'empreinte utilise directement son adresse Cloudinary (`footprint`, déjà fournie par `get_footprint_url()`) ; favicon et icônes sur `app.mixity.io`.
  - `scoring/templates/scoring/templateSynthesis.html`, `templateSynthesis2.html`, `scoring/management/commands/export_to_webflow.py` : `app.mixity.io`.
- **Vérification** : `https://app.mixity.io/account/login` répond 200 ; `https://app.mixity.io/static/favicon.ico` et `/static/icon/diag.svg` répondent 200 ; `www.app.mixity.io` ne se résout pas.
- **Limite** : `www.app.mixity.io` reste dans `ALLOWED_HOSTS` (sans effet). Envoi réel des e-mails en production toujours à vérifier par le client (V-2).

### CONFIRM-2. « Valider votre évaluation » plantait (erreur 500) pour les Diag récents (29/10/2026)
- **Constaté pendant le test complet avec Yassir** : clic sur « Valider votre évaluation » (évaluation 940, « Parcours Final 29 ») : `AttributeError: 'NoneType' object has no attribute 'subscription_type'` dans `scoring/mails.py` (`alert_evaluation_created_mail`).
- **Cause** : l'e-mail d'alerte envoyé à l'équipe lisait `evaluation.subscription.subscription_type`. Les évaluations récentes sont créées par les options d'abonnement et n'ont plus de `subscription` : **10 Diag sur 104** en base (copie de production) sont dans ce cas, dont tous les récents. **En production, tout client qui valide un Diag récent obtient donc une erreur 500.** La validation elle-même (`do_user_validation`, calcul des scores) avait déjà eu lieu, mais la suite (objectifs, export des réponses, validation automatique éventuelle) n'était pas exécutée.
- **Défauts voisins dans `EvaluationConfirm.form_valid`** (`scoring/views.py`) : `evaluation.sheet.type == "evaluation_collaborateurs_360"` comparait un objet à un texte (toujours faux : un Human était traité comme un Diag) ; `subscription_option.is_trial` plantait si aucune option n'était trouvée.
- **Fichiers modifiés** :
  - `scoring/mails.py` : sans `subscription`, le type affiché est le nom du questionnaire (« Evaluation Mixity Diag »).
  - `scoring/views.py` : comparaison sur `sheet.type.slug` ; garde-fou si aucune option d'abonnement.
  - `scoring/test_alert_mail.py` (nouveau) : 2 tests.
- **Vérification** : tests `scoring.test_alert_mail` et `scoring.test_evaluation_confirm` : 4 tests OK. Clic rejoué avec le compte du test (`parcours.final@example.com`) : POST `/scoring/evaluation/940/confirm/` → 302 vers le tableau de bord, évaluation validée par l'utilisateur. Le worker avait calculé les scores au premier clic (`score = 16.74`, `Job OK`).

### M-3. Images des solutions et des bonnes pratiques absentes (29/10/2026)
- **Constaté pendant le test complet** : sur le tableau de bord, bloc « Solutions », les vignettes ne s'affichaient pas.
- **Cause** : l'application `act` définit ses propres classes `ImageStorage` et `RawStorage` (`act/models.py`), qui héritaient directement de la bibliothèque `cloudinary_storage` : le dossier restait dans l'adresse (même défaut que M-1). Le premier contrôle de M-1 s'était arrêté sur une erreur avant d'atteindre ces modèles. Les mêmes classes existaient dans `mixity/models.py` et `accounts/views.py` (non utilisées).
- **Fichiers modifiés** : `act/models.py`, `mixity/models.py`, `accounts/views.py` : les classes héritent de `FlatCloudinaryStorage` / `FlatRawCloudinaryStorage` (mêmes noms de classe : aucune migration, `makemigrations --check` sans changement).
- **Vérification sur le vrai Cloudinary, tous les champs fichiers de l'application** : photos des solutions **139/149** (avant 0/149 ; 10 absentes du compte), logos des bonnes pratiques **22/22** (avant 0/22). Les autres champs sont inchangés (voir M-1 et M-2).
- **En local** : les images restent absentes, le stockage local étant le disque (Cloudinary n'est configuré qu'en production).

### Constat : bloc « Actions » à 0 % sur le tableau de bord (29/10/2026, pas un bug)
- Le bloc affiche les actions du **plan d'action** (module Pilot / « Lead », modèle `LeadAction`), créées par le client lui-même ; le pourcentage est la part des actions « déployées ». Une entreprise neuve n'en a aucune : 0 % et liste vide sont normaux.
- **À signaler à Mathieu** : les objectifs automatiques (`create_aims`) ne sont générés que pour les questions qui ont une recommandation. Dans le questionnaire Diag actuel (v2.1), **aucune des 171 questions n'a de recommandation** : aucun objectif n'est proposé automatiquement aux nouveaux clients. C'est une question de contenu, pas de code.

### DEV-2. Images affichées en local (29/10/2026)
- **Décision** : demandée par Yassir (« je veux que les images s'affichent en local »).
- **Problème** : en local, les fichiers étaient cherchés sur le disque (`/media/...`) alors que ceux de la base copiée depuis la production sont sur Cloudinary : toutes les images étaient en 404, ce qui empêchait de vérifier M-1 à M-3 à l'œil.
- **Fichiers modifiés** :
  - `mixity/storage_dev.py` (nouveau) : `LocalOrCloudinaryStorage` (et sa variante `Raw`). Les fichiers sont enregistrés sur le disque ; pour l'affichage, un fichier absent du disque est lu sur Cloudinary avec **la même adresse qu'en production** (lecture seule, aucune clé d'API). Sans `cloud_name` configuré (tests), comportement identique au disque.
  - `mixity/settings/dev.py` : `DEFAULT_FILE_STORAGE` sur cette classe ; `cloudinary.config(cloud_name="mixity")` (modifiable par `CLOUDINARY_CLOUD_NAME`).
  - `scoring/models.py`, `act/models.py`, `mixity/models.py`, `accounts/views.py` : la branche de repli (sans Cloudinary) utilise ces classes au lieu de `FileSystemStorage` ; imports devenus inutiles retirés. **Aucun effet en production** (la branche Cloudinary est inchangée).
- **Vérification dans Chromium** (compte `parcours.final@example.com`) : tableau de bord 4/4 images Cloudinary affichées ; « Trouver une solution » 313/323 (les 10 autres n'existent pas sur Cloudinary, cf. M-3) ; « Bonnes pratiques » 14/14. `makemigrations --check` : aucun changement. Suite complète : **174 tests OK**.

### TEST-HUMAN. Parcours Mixity Human vérifié de bout en bout (29/10/2026, aucun bug)
- **Admin** : sur un pack existant, « Ajouter l'option human » crée l'offre **déjà active mais sans évaluation** ; c'est « Valider les offres » sur cette offre qui génère l'évaluation Human (`generate_human_or_scan_evaluation`). Pour un nouveau client qui choisit Human à la création de l'entreprise, « Valider les offres » suffit.
- **Salarié** : lien ouvert (`need_auth = False`) `/collaborator/evaluation/<lien signé>/` : page d'accueil, profil (genre, âge) et questionnaire (183 questions) chargés dans Chromium sans connexion, sans erreur.
- **Essai complet** sur Entrepris1 (évaluation 942) : 12 salariés simulés (`manage.py generate_random_human_answers 942 12`, commande réservée au développement), validation par le propriétaire (« Valider et bloquer les nouvelles réponses ») : tâche du worker en 9 s (`score = 58.10`, `Job OK`), validation Mixity, scores enregistrés (Transversal 58, Genre 52, Handicap 60, Origines 58, Générations 60, LGBTQIA+ 61) ; tableau de bord, page de résultats Human et page des filtres chargées sans erreur.
- Évaluation Human 941 créée pour « Parcours Final 29 » pour le test de Yassir.

### ASSESS-1. La page de résultats Human renvoyait vers le Diag (02/11/2026)
- **Constaté en préparant le test Human** : l'ancienne adresse `/assess/<entreprise>/human/<version>/` (utilisée notamment par la redirection après « Valider » dans `EvaluationValidate`) redirigeait vers la page React **du Diag** : le mot `"diag"` était écrit en dur dans `DashboardAssessView.dispatch` (`scoring/dashboard/views.py`). Une entreprise qui n'a que Human arrivait sur une page vide.
- **Changement** : le produit de la redirection suit l'évaluation (`"human"` si `evaluation.is_human`, sinon `"diag"`).
- **Vérification dans Chromium (clics réels)**, entreprise « Parcours Final 29 », évaluation Human 941 : « Lancer l'évaluation » (alerte de confirmation, `is_started` à vrai) → « Copier le lien du sondage » visible → l'ancienne adresse mène à `/parcours-final-29-main/human/assess/en-cours/` avec « Copier le lien » et « Valider et bloquer les nouvelles réponses » → 12 salariés simulés → clic sur « Valider et bloquer » : scores calculés par le worker en 4 s → validation Mixity → tableau de bord « 58/100 » (Human) à côté de « 14/100 » (Diag) → page de résultats Human sans erreur JavaScript.
- **Précisions sur le parcours Human** (comportement d'origine) : le client doit cliquer sur **« Lancer l'évaluation »** sur la carte Human pour faire apparaître le lien du sondage et le bouton de clôture. « Inviter des collaborateurs » (menu de gauche) ajoute des **collègues à l'équipe** sur la plateforme, pas des répondants au sondage. Le lien « Copier le lien du sondage » ne contient pas `https://` (`window.location.host + ...`), le navigateur le complète au collage.

### COPY-1. Le lien du sondage copié n'avait pas de protocole (02/11/2026)
- **Constaté par Yassir pendant le test Human** : « Copier le lien » donnait `localhost:8443/collaborator/evaluation/...` ; collé dans le navigateur, il était ouvert en `http://`, et le proxy HTTPS local répondait « Client sent an HTTP request to an HTTPS server ». En production, un client qui envoie ce lien à ses salariés leur transmet une adresse incomplète (`app.mixity.io/...`).
- **Changement** : `window.location.host + ...` remplacé par `window.location.origin + ...` (protocole compris) dans `mixity/dashboard/js/Home.js` (« Copier le lien du sondage ») et `scoring/dashboard/js/includes/components/DisplayDownloads.js` (« Copier le lien », 2 endroits). Bundles recompilés et copiés : `dashboardhomecomponents-1.0.0.js`, `assessdashboardhomecomponents-1.0.0.js`.
- **Vérification dans Chromium** (compte `human.demo@example.com`, évaluation 948) : les deux boutons placent dans le presse-papiers `http://localhost:8000/collaborator/evaluation/948:.../` (adresse complète).

### BLOCK-1. « Valider et bloquer les nouvelles réponses » ne rafraîchissait pas la page (02/11/2026)
- **Constaté pendant le test Human de Yassir** : après le clic, la page restait identique (bouton toujours affiché), ce qui laissait croire que rien ne s'était passé ; l'admin refusait ensuite la validation (« L'évaluation n'a pas encore été validée par le client »).
- **Cause** : `blockResponses` (`scoring/dashboard/js/includes/components/DisplayDownloads.js`) appelait `refresh_entity_evaluation`, transmis par `AssessPage.js` sans son contexte : `TypeError: Cannot read properties of undefined (reading 'url')`. La validation côté serveur avait bien lieu, mais l'écran n'était jamais mis à jour.
- **Changement** : après une réponse réussie, la page est rechargée (même comportement que « Lancer l'évaluation » juste au-dessus). Bundle recompilé et copié : `assessdashboardhomecomponents-1.0.0.js`.
- **Vérification dans Chromium, en HTTPS** (`human.demo@example.com`, évaluation 948 remise à « non validée ») : clic → page rechargée, bouton disparu, aucune erreur JavaScript, évaluation validée par le client ; scores calculés par le worker (`score = 58.57`).

### HUMAN-EXPORT-1 et INDIC-1. Page de résultats Human : export Excel et indicateurs en erreur 500 (02/11/2026)
- **Constaté par Yassir** sur `/human-demo-02-main/human/assess/2026-novembre/` : « Télécharger les résultats de votre questionnaire » affichait « Une erreur s'est produite ». Les journaux montraient deux erreurs 500 sur la même page.
- **Export Excel** (`/scoring/evaluation/<id>/react_human_filtered_excel/`) : `KeyError: 'collab_human_criteria'`. Le front (`AssessSheetDownload.js`) n'envoie cette clé que si l'entreprise a des **critères personnalisés** (services, sites…), ce qui n'est pas le cas d'une entreprise neuve. Corrigé en lisant les deux clés avec une valeur par défaut vide à trois endroits : `scoring/views.py` (`react_export_filtered_questions_sheet_with_job` et `ExportReactExcelFileApiView.post`) et `scoring/models.py` (`header_filtered_sheet`).
- **Indicateurs** (`/<entreprise>/human/api/indicators/`) : `KeyError: 'type'`. Deux indicateurs du **questionnaire Human actuel (n° 291)** sont mal paramétrés en base : n° 20 (« Avez-vous connaissance d'un dispositif de sanction interne… », `params` vide `{}`) et n° 13 (« Avez-vous le sentiment d'appartenir à une minorité… », deux objets JSON collés). **En production, la page des indicateurs Human échoue donc pour tous les clients Human.** Corrigé dans `mixity/dashboard/views_api.py` : un indicateur mal paramétré est ignoré et signalé dans les journaux (`Indicateur 20 mal paramétré, ignoré`) au lieu de faire échouer la page.
- **Vérification** (compte `human.demo@example.com`, évaluation 948) : indicateurs → 200 (42 indicateurs, n° 20 ignoré avec avertissement) ; export Excel → 200, e-mail « Votre récapitulatif avec filtres Human Demo 02-main » reçu dans MailHog avec le fichier `.xlsx` joint. Tests `scoring` et `mixity` : 113 OK.
- **À corriger dans l'admin par Mixity** (contenu) : paramètres des indicateurs n° 13 et n° 20 (Scoring → Indicators), pour qu'ils réapparaissent sur la page.

### Constat : « Points forts », « Axes d'amélioration » et « Objectifs recommandés » vides (29/10/2026, pas un bug)
- Ces blocs de la page « Consulter mes évaluations » sont **rédigés par l'équipe Mixity** dans l'admin (fiche de l'évaluation, sections Objectifs / Points forts / Axes d'amélioration : `AimInline`, `StrengthInline`, `WeaknessInline`). Le code ne les crée pas (il ne fait que les recopier lors d'une réouverture), sauf les objectifs automatiques, qui exigent des recommandations absentes du questionnaire actuel.
- Base (copie de production) : 37 des 76 Diag validés ont des points forts saisis ; Piex, Montpellier Business School et Publicis n'en ont aucun.
- **À dire à Mathieu** : la rédaction de l'analyse fait partie du travail de validation, avant « Valider les évaluations ».
- **Score affiché « 14/100 »** : moyenne simple des 6 dimensions (`get_global_score_delta`), différente du score global pondéré enregistré (16,7 pour l'évaluation 940). Comportement d'origine, à confirmer avec Mathieu.

### Bilan du 29/10/2026
- **Suite de tests complète** (`python manage.py test --parallel 4`) : **172 tests, tous OK** (aucun échec, aucune erreur).
- **Tests ajoutés aujourd'hui** : `mixity/test_storage.py` (+4), `payments/test_payment_page.py` (2).
- **Données locales modifiées pour les tests** (base locale uniquement) : mots de passe des comptes de test `test2.email@gmail.com` et `nomember.test@example.com` (`MixityTest2026!`) et du superutilisateur local `hichamgarrad403@gmail.com` (`AdminLocal2026!`) ; évaluation 938 remplie avec les réponses de Piex puis validée (utilisateur et admin).
- **Rien n'est commité ni déployé.**

### ADMIN-STRUCT-1. Une structure créée dans l'administration est inutilisable par le client (03/11/2026)
- **Contexte** : Mathieu confirme que la création des entreprises se fait par Mixity dans l'admin, pas par le client.
- **Constaté** (test Chromium, `/admin/accounts/structure/add/`) : l'enregistrement réussit, mais la structure n'a **ni niveau d'entité, ni entité principale** ; le propriétaire ajouté dans « Appartenances » n'est rattaché à aucune entité. Conséquences : connexion du client → **erreur 500** sur `/account/update_profile/` (`'NoneType' object has no attribute 'is_solver'`) ; action « pack Diag » → aucune évaluation créée ; action « pack Human » → évaluation créée sans entité.
- **Cause** : seule la création côté client (`CreateStructure`, `accounts/dashboard/views_api.py`) crée le niveau « Groupe », l'entité `<nom>-main`, le rattachement du propriétaire et les étiquettes effectif et pays. L'admin enregistre la structure seule.
- **Changement** (`accounts/admin.py`, `StructureAdmin.save_related` → `ensure_main_entity`) : à chaque enregistrement dans l'admin, si l'entité principale manque, elle est créée de la même façon que côté client, et les membres sans entité y sont rattachés. Pas de pack créé automatiquement : les actions « Créer pack Diag / Human / 360 » restent l'étape suivante.
- **Vérification dans Chromium** : création de « Admin Test Structure » avec le propriétaire `admin.test@example.com` → entité `Admin Test Structure-main`, étiquettes `fr` et `small_company` ; action « pack Diag » → évaluation 951 créée ; connexion du client → tableau de bord affiché (200), aucune erreur JavaScript. Tests ajoutés : `accounts/test_admin_structure.py` (2). Suite complète : **176 tests OK**.
- **Données existantes** : 11 anciennes structures sans entité principale et sans membre (Gapsmoov, Crédit Suisse, ANZ, Carrefour, Canal +, Keolis, BBVA, Impulse ×4). Il suffit de les ouvrir et de les enregistrer dans l'admin pour les réparer. Nestlé n'est pas concerné.
- **Marche à suivre côté admin (ADMIN-STRUCT-1)** : 1) Comptes → Structures → Ajouter : nom, slug (recalculé automatiquement), catégorie, secteur, effectif, pays, et le compte du client dans « Appartenances » avec « is owner » coché → Enregistrer. 2) Cocher la structure → action « Créer pack Diag » (ou Human / 360). Le compte client doit exister au préalable (Comptes → Utilisateurs).

## Retours de Mathieu sur le staging (mail du 06/11/2026), traités le 07/11/2026

Chaque point vérifié dans Chromium (compte `admin@mixity.io`, entité `demo-mixity-360`, base locale copie de la production), avec Cloudinary simulé en panne (toutes ses réponses en 404).

### STG-1. Visuels absents de Cloudinary : image par défaut
- **Constat** : un visuel supprimé de Cloudinary laissait une image cassée (fiche solution, cartes, logos des solutionneurs).
- **Changement** : nouveau fichier `mixity/dashboard/js/includes/imageFallback.js` ; si l'image ne se charge pas, affichage de `solvers_catalog/solution.jpg` (solutions), `best_practices_catalog/best_practice.jpg` (bonnes pratiques) ou `icon/buildings.svg` (logos). Appliqué dans `SolutionsList.js`, `FavoritesList.js`, `BestPracticesManagement.js`, `FavoriteBestPracticesList.js`.
- **Vérification** : catalogue des solutions → 357 images, 0 image cassée (183 visuels et 174 logos remplacés).

### STG-2. Logo par défaut des structures
- **Demande** : remplacer le picto par défaut (`img/structure.svg`) par un visuel « entreprise ».
- **Changement** : `Structure.get_logo_url` (`accounts/models.py`) renvoie `icon/buildings.svg` (immeubles, déjà dans la librairie du projet) ; les balises `<img>` des logos (menu « Choix de la structure », pages publiques et pages du sondage Human) passent aussi à ce visuel si le lien Cloudinary est KO.
- **Vérification** : menu latéral → logos en `icon/buildings.svg`, aucune image cassée.

### STG-3. Liens externes dans un nouvel onglet
- **Changement** : `mixity/templates/base_dashboard.html`, un script unique : tout lien vers un autre site s'ouvre dans un nouvel onglet (`target="_blank"`, `rel="noopener noreferrer"`). Couvre les textes des solutions et bonnes pratiques saisis dans l'admin, sans toucher au contenu.
- **Vérification** : clic sur un lien externe → nouvel onglet, la page de l'application reste ouverte.

### STG-4. Texte anglais « deployed » sur l'accueil
- **Cause** : `mixity/dashboard/js/Home.js` affichait la valeur brute du statut (`deployed - 2023-04-19`).
- **Changement** : libellé traduit (« Action déployée », « Action en cours »…) et date au format de la langue (19/04/2023).
- **Constat, pas un bug** : « percentage of women » et « Liked par les emplo » sont des **noms d'indicateurs saisis à la main** sur Demo Mixity 360 (indicateurs n° 16 et 87). À renommer ou supprimer par Mixity.

### STG-5. Aperçu du plan d'action : la page devenait vide après un filtre « Indicateurs »
- **Cause** (`lead/js/Overview.js`) : « Appliquer » renvoyait **tout le profil** de l'utilisateur (PUT) ; quand le prénom ou le nom est vide (cas du compte admin), le serveur refusait (400) et la page prenait le message d'erreur pour l'utilisateur → `Cannot read properties of undefined (reading 'includes')`, page blanche.
- **Changement** : seule la liste des indicateurs est envoyée (PATCH) ; l'affichage se met à jour même si l'enregistrement échoue. À l'ouverture, les indicateurs affichés sont **cochés** (aucun choix enregistré = tous affichés et cochés), comme demandé.
- **Vérification** : 5 cases, 5 cochées ; décocher une case → Appliquer → page affichée, aucune erreur ; après rechargement, 4/5 cochées (choix enregistré).

### STG-6. « Remplir le plan d'action à partir de vos évaluations »
- **Constat** : le bouton fonctionne. Il transforme les **objectifs recommandés** (saisis par Mixity dans l'admin) de la dernière évaluation Diag et Human en objectifs du plan d'action. Pour Demo Mixity 360 : le dernier Diag n'en a aucun et les 6 du Human ont déjà été repris, donc rien ne change à l'écran.
- **Comportement s'il a déjà été utilisé** : il n'ajoute que les objectifs pas encore repris ; il n'écrase ni ne duplique rien.
- **Changement** (`lead/js/Lead.js`) : un message s'affiche sous le bouton : « N objectifs ajoutés au plan d'action » ou « Aucun nouvel objectif à ajouter… ».

### STG-7. Devenir solutionneur : « S'inscrire »
- **Changement** : le bouton ouvre le formulaire de l'application `/<structure>/solver/create/` (adresse calculée dans `landing/dashboard/views.py`) au lieu de https://www.mixity.io/partenaires (gardé seulement si l'utilisateur n'a pas de structure).
- **Vérification** : clic → `/demo-360-dei-structure/solver/create/`, page « Devenir Solutionneur ». Test ajouté : `landing/test_landing.py` (`SolverLandingSignUpTest`).

### Constats sans changement de code
- **Mesure ethnique, évaluation précédente** : fonctionne (vérifié sur Ogury : « 2023-Novembre » affiche 539 salariés, indice de confiance 70 %). Pour Demo Mixity 360, aucun CSV n'a été importé sur « 2021-Mai » : la page affiche « Pas de résultats disponibles » (le dessin en bas de la capture de Mathieu).
- **Catalogue E-learning vide** : contenu saisi dans l'admin (Act → Elearnings). La table est vide dans la base de production (0 e-learning), aucune source externe ni import dans le code.

Bundles recompilés et copiés : `actsolutions`, `actfavorites`, `actbestpracticesmanagement`, `actfavoritebestpractices`, `dashboardhome`, `lead`, `overviewlead`, `dashboardlandingsolver`.

## Retours de Mathieu sur le staging (mail du 10/11/2026), traités le 10/11/2026

### STG-8. Bouton « PDF » des résultats : lien Cloudinary cassé
- **Cause** : le bouton pointait directement vers le fichier `pdf_sheet` stocké sur Cloudinary (ex. `pdf_zukymc.pdf`, évaluation 149 « 2021-Mai » de Demo Mixity 360), qui n'existe plus. Le moteur de régénération existant ne pouvait pas fonctionner hors Docker : il appelle l'hôte `webpack` (`get_webpack_ip`), et sa page `/<slug>/<produit>/assess/pdf/` était masquée par la route `assess/<version>/` (« pdf » lu comme une version → erreur 500).
- **Changement** :
  - Le bouton passe par `scoring/evaluation/<pk>/pdf-sheet/<langue>/` (`EvaluationPdfSheetView`). Si le fichier stocké répond, redirection vers lui ; sinon un job `regenerate_pdf_sheet_with_job` imprime la page de résultats avec Chromium (menu et boutons masqués), enregistre le nouveau PDF sur l'évaluation et l'envoie par mail. Le message « Préparation d'export… » s'affiche comme pour l'Excel. Les clics suivants ouvrent directement le nouveau fichier.
  - Le worker joint l'application via `PDF_RENDER_BASE_URL` (vide = adresse du site ; en local `http://web:8000/`).
  - Route `assess/pdf/` placée avant `assess/<version>/` dans `mixity/dashboard/urls.py`.
- **Vérification** : clic PDF sur l'évaluation 149 → message, job OK en ~13 s, mail reçu avec le PDF joint, nouveau fichier enregistré, 2e clic → redirection vers le fichier. Tests ajoutés : `scoring/test_pdf_sheet.py` (4 tests).

### STG-9. Export Excel : message affiché mais pas de mail reçu
- **Constat** : en local, toute la chaîne fonctionne (clic → job RQ → fichier → mail reçu dans MailHog). Le code n'est pas en cause. Sur Heroku, à vérifier :
  1. le dyno `worker` doit être démarré (`heroku ps:scale worker=1`), sinon les jobs restent en file ;
  2. `EMAIL_HOST_PASSWORD` doit être défini (OVH, support@mixity.io) ;
  3. le mail part à l'adresse du compte connecté : avec `admin@mixity.io`, il arrive dans cette boîte.
- Même remarque pour le PDF régénéré (STG-8) : il passe par le même worker et le même envoi de mail. Chromium doit aussi être disponible sur le worker : `playwright install chromium` dans la phase `release` du `Procfile` n'est pas conservé sur les autres dynos Heroku. Un buildpack Playwright est nécessaire si la génération échoue.

### STG-10. Indicateurs sans donnée : affichage incohérent
- **Cause** : seuls 3 types de graphique (GapChart, ScanCircularChart, TextChart) affichaient « Cette donnée n'est pas disponible », et seulement quand la valeur manquait dans la liste. Une valeur vide (`[]`, `null`, `""`) ou les 7 autres types donnaient un cadre vide.
- **Changement** : contrôle unique dans `scoring/dashboard/js/EvaluationIndicator.js`. Sans aucune valeur, tous les types affichent le même message.
- **Vérification** : Human 2021-Juillet de Demo Mixity 360 → « Répartition des répondants par Exemple » (valeurs `[]`) affiche le message au lieu d'un cadre vide ; les 37 autres graphiques sont inchangés, aucune erreur JS.
- **Reste** : les indicateurs du Diag sont dessinés par ~40 gabarits Django (`scoring/templates/includes/indicators/`), non modifiés faute d'exemple précis. Exemples demandés à Mathieu.

### Constat sans changement de code : « Liked par les emplo » et « percentage of women »
- Ce sont deux indicateurs personnalisés saisis à la main sur Demo Mixity 360 (ActionKpi 87 du 27/04/2023 et 16 du 28/03/2023), pas des libellés de l'application. À renommer ou supprimer dans l'admin : Lead → Action kpis.

Bundles recompilés et copiés : `assessdashboardhomecomponents`, `assessdashboardhomePDF`.

<!-- SUIVANT -->

(Les corrections suivantes sont ajoutées ci-dessus, avant ce repère, au fur et à mesure.)

## Changements déjà présents avant le début des corrections

Ces modifications datent de la mise en route de l'environnement local. Elles sont décrites ici pour mémoire.

| Fichier | Modification | Raison |
|---|---|---|
| `Dockerfile` | image `python:3.10.14-bullseye`, dépôts Debian d'archive, installation allégée, `playwright install chromium` | l'image d'origine (Python 3.9, Debian Buster) ne se construisait plus |
| `subscriptions/migrations/0026_subscriptiontype_slug.py` | ignore les types de questionnaire absents | permettre la migration sur une base vide |
| `docker-compose.override.yml` (fichier local ignoré par git) | base locale en `postgres:17` | s'aligner sur la production (Heroku, PostgreSQL 17.10) |
| `start_webpack.sh` | droits du fichier | sans effet sur le contenu |

Base locale : restaurée à partir d'un dump de production du 23/10/2026. Comptes de test créés en local : `audit.test@example.com`, `client.test@example.com`, `signup.check@example.com`, plus un compte administrateur créé avec `createsuperuser`.

---

## BUG-CONFIRM — « Reprendre le questionnaire » plante (KeyError / AttributeError)

**Symptôme** : sur une entreprise toute neuve, le bouton « Reprendre le questionnaire » du Mixity Diag renvoie une erreur 500
(`KeyError: 583` sur `/scoring/evaluation/938/confirm/`, puis `'function' object has no attribute 'category'`).

**Causes** (`scoring/views.py`, `EvaluationConfirm.get_context_data`) :
1. `last_global_evaluations[ellemm.id]` : l'entité n'a aucune évaluation « non collaborateur » → `KeyError`.
2. Branche « plus de question à remplir » : `scores_categories.first` utilisé **sans parenthèses** (méthode, pas un objet).
3. Un utilisateur sans lien avec l'entreprise provoquait une 500 (`membership` vaut `None`) au lieu d'un refus.
4. Le JSON du sélecteur d'entités était construit par concaténation de chaînes.

**Correction** : repli sur l'évaluation affichée, entités sans évaluation ignorées, `json.dumps` (apostrophes échappées),
`.first()` avec garde-fou, 403 (`PermissionDenied`) si aucun droit. Test : `scoring/test_evaluation_confirm.py`.

**Cause de fond (donnée, à traiter avec Mathieu)** : en base, le type `mixity_evaluation_diag` a `is_collaborator = true`
alors que la migration 0360 le crée à `False`. Conséquence : `Evaluation.generate_answers()` sort immédiatement et les
nouveaux Diag (936, 937, 938…) ont **0 réponse**. À corriger dans l'admin de production
(Scoring → Question sheet types → décocher « is collaborator » pour `mixity_evaluation_diag`) puis régénérer les réponses
des évaluations vides. Non modifié en production.
