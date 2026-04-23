[![pipeline status](https://gitlab.com/dantooin_devs/mixity/badges/develop/pipeline.svg)](https://gitlab.com/dantooin_devs/mixity/-/commits/develop)
[![coverage report](https://gitlab.com/dantooin_devs/mixity/badges/develop/coverage.svg)](https://gitlab.com/dantooin_devs/mixity/-/commits/develop)

# Initialise your development environment

All following commands must be run only once at project installation.


## First clone

```sh
git clone --recursive ssh://git@gitlab.com/dantooin_devs/mixity
```

## Format code
  - Python code => [Black](https://black.readthedocs.io/en/stable/editor_integration.html)
  - JSON, SCSS and CSS => Prettier/Beautify

## Install docker and docker compose

Follow official procedures for
  [docker](https://docs.docker.com/install/#releases) and
  [docker-compose](https://docs.docker.com/compose/install/).

## ⚠️ For Windows users

if you prefer to stay in Windows and use a GNU/Linux environment without installing any virtual machine, you can use WSL which is a Windows Subsystem for Linux.

### Install WSL

```PowerShell
wsl --install
```
Then you have to restart your computer.
By default, it installes WSL 2 and Ubuntu as a Linux distribution. If you want to change the installed distribution execute the following command :
 ```PowerShell
wsl --install -d <Distribution Name>
 ```
 To view the list of Linux distributions available, use the following command :
 ```PowerShell
 wsl --list --online
 ```

### Docker

Follow this official documentation for installing [Docker Desktop for Windows](https://docs.docker.com/desktop/windows/install/)

### Black in PyCharm

#### Installation

1. Create a virtual environment where you are going to place black formatter inside it in order to not mess with the system Python or other applications
```PowerShell
python -m venv C:\Users\<user_name>\<venv_name>
```
2. Navigate to `\Scripts` inside the newly created directory
```PowerShell
cd C:\Users\<user_name>\<venv_name>\Scripts
```
3. Activate your virtual environment in Windows

```PowerShell
.\<venv_name>\Scripts\activate
```
4. Install the black formatter
```PowerShell
pip install black
```
5. Get the location of black on Windows *it's going to be used later*
```PowerShell
where black
```

#### Configuration

1. In your PyCharm IDE, go to `Settings/Tools/External Tools`
2. Press the `+` button to add a new external tool
3. Fill the necessary fields with :
    * Name : Black
    * Tool Settings :
        - Program : put the location that you get earlier using the `where black`
        - Arguments : "$FilePath$"
        - Working directory : $ProjectFileDir$
    * Advanced Options : make sure that the`Synchronize files after execution` and `Open console for tool output` functionalities are enabled
4. Go to `Settings/Plugins`,type `File Watchers` and enable it in the `Installed` tab
5. Go to `Settings/Tools/File Watchers` and press the `+` button to add a new file watcher
6. Fill the following fields :
    * Name : Black
    * Files to Watch :
        - File type : Python
        - Scope : Project Files
    * Tool to Run on Changes :
        - Program : put the location that you get earlier using the `where black`
        - Arguments : $FilePath$
        - Output paths to refresh : $FilePath$
        - Working directory : $ProjectFileDir$
    * Advanced Options : enable the `Trigger the watcher on external changes` and `Auto-save edited files to trigger the watcher` functionalities
~~~~
**NOTE**
Docker Compose may cause you a problem of converting *underscores* into *dashes* in your containers names, this is due to the difference in naming convention between Docker Compose versions. To avoid this :
- Navigate to `Settings\General` in your Docker desktop
- Disable the functionality `Use Docker Compose V2`~~~~

### Configuration of Python Interpreter in PyCharm with Docker

1. In your PyCharm IDE, go to `Settings` and search `Python Interpreter`
2. In `Python Interpreter` field , click ⚙️ and add a new interpreter
3. In the opened page dialog, choose Docker Compose in the sidebar nav menu
4. Fill the following fields :

	* Server : Docker
	* Configuration files : `./docker-compose.yml`
	* Service : choose `web`
	* Environment variables : `DJANGO_SETTINGS_MODULE=mixity.settings.dev`
	* Python interpreter path : python
5. Press OK, then select the newly created interpreter in the Python interpreter field and Apply the changes


# Use your development environment

## Start the stack for the first time

After a last verification of the files, to run with docker, just type:

```bash
# First time you download the app, or sometime to refresh the image
docker build .
docker-compose build # Build when dependencies have changed
docker-compose up # Should be launched once each time you want to start the stack
docker exec -it mixity_web_1 python manage.py migrate # Execute when database relations have changed
docker exec -it mixity_web_1 python manage.py createsuperuser # Execute to create your user
docker exec -it mixity_web_1 python manage.py import_sheets_questions --society # Execute to import Sheet datas
```

## Start a shell inside the django container

```sh
docker exec -it mixity_web_1 python manage.py shell_plus
```

## Create a `docker-compose.override.yml` :

```yml
version: '3.7'

services:
  web:
    tty: yes
    stdin_open: yes
```

## Rebuild/Refresh local docker image in dev

```sh
docker-compose up
```

## To see only web return and use pdb

```sh
docker-compose up -d && docker attach mixity_web_1
```

## Calling Django manage commands

```sh
docker exec -it mixity_web_1 python manage.py [command]
# For instance:
docker exec -it mixity_web_1 python manage.py makemigrations
docker exec -it mixity_web_1 python manage.py migrate
docker exec -it mixity_web_1 python manage.py shell
docker exec -it mixity_web_1 python manage.py createsuperuser
docker exec -it mixity_web_1 python manage.py test
...
```

## URLs

Here are the different URLs to access the project :

https://localhost:8080/ : Main URL. S Uses webpack-dev-server and reload JS/CSS automatically. **HTTPS** only.<br>
https://localhost:3009/ : Another webpack URL but doesn't reload JS/CSS automatically (for now). **HTTPS** only.<br>
http://localhost:8000/ : Django Web Server URL. JS/CSS will not automatically reload. **HTTP** only.<br>
http://localhost:3001/ : Browsersync settings page

You can access these URLs over the network, but be sure to use port 3009 if you do so
because it's the only one using HTTPS. It will also be the only one working with
Secure Contexts functions outside of localhost (Unsecure localhost is whitelisted for Secure Contexts).
Secure Contexts are currently used in Mixity Human Poll at the time of writing this


## Docker volumes

Your application extensivly use docker volumes. From times to times you may
need to erase them (eg: burn the db to start from fresh)

```sh
docker volume ls  # hint: |grep \$app
docker volume rm $id
```


## Theme HTML / CSS / JS

Theme sources are loacted in `/theme`. Node is required to build and develop, node version is specified in `/theme.package.json` in `engines` (actually <10).

### Develop / build theme (/!\ inside container, so use `make bash`)

Install sources :

```sh
yarn
```

Launch node dev server :

```sh
yarn start
```

To build production static (will generate minified css and js bundles in `/mixity/static/dist`) :

```sh
yarn build
```

### Methodology

CSS uses BEM methodology : http://getbem.com/introduction/. Please follow these rules for better maintenability.

JS is compiled through Babel, so you can write ES2015+ javascript.


## Doc for deployment on environments
- Git push will deploy on staging
- Use heroku to deploy staging on demo / pilote / prod

- Push to master / demo
```sh
git push production master
git push demo master
git push demo develop:master --force-with-lease
```

## Heroku

- Login to Heroku by browser
```sh
heroku login
```

or by CLI

```sh
heroku login -i
```

- Create app DB dump
```sh
heroku pg:backups:capture --app mixity-staging
```

- Download app DB dump
```sh
heroku pg:backups:download --app mixity-staging
```

- Copy DB from prod to staging
```sh
heroku pg:copy mixity::HEROKU_POSTGRESQL_RED postgresql-triangular-76379 --app mixity-staging
```

# Makefile (combine Shell, Docker and Heroku command)

## Database
- To know all targets
```sh
make help
```

- Create and download app (staging, demo or prod) backup
```sh
make hk:download_backup APP=mixity
```

- Create, download and apply to local DB an app backup
```sh
make import_app_db APP=mixity
```

- Apply old backup to local DB
```sh
make reset_db DUMPFILE=backup_mixity_20210506_1419.dump
```

## Translations

Read the django documentation : https://docs.djangoproject.com/fr/2.2/topics/i18n/translation/

Useful commands:
```sh
make I18N:generate  # Search for strings to translate, merge with existing, and put them in mixity/locale/<lang>/LC_MESSAGES/*.po
make I18N:check  # Control translated file to detect lost beacons, invalid HTML and missing variables
make I18N:compile  # Transforms the strings into a dictionnary in mixity/locale/<lang>/LC_MESSAGES/*.mo
```

## Stripe payments

You need to set in your dev environnements values for STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY, STRIPE_ENDPOINT_SECRET
The first two values are either linked to the "Mixity Test" account if you want to use the sames infos as staging and demo or you can use your own if you create your own account.
The last value can be generated by using stripe-cli to test your webhook. More infos here : https://testdriven.io/blog/django-stripe-tutorial/#testing-the-webhook

Useful commands:
```sh
make I18N:generate  # Search for strings to translate, merge with existing, and put them in mixity/locale/<lang>/LC_MESSAGES/*.po
make I18N:check  # Control translated file to detect lost beacons, invalid HTML and missing variables
make I18N:compile  # Transforms the strings into a dictionnary in mixity/locale/<lang>/LC_MESSAGES/*.mo
```

### Process:

1. Edit a code file containing text to translate
2. Generate the translations (make I18N:generate)
3. Give the PO file to the translator
*** DO NOT EDIT THE FILE DURING THIS TIME ***
4. Once its translated, overwrite the PO file of the project with the new one translated
5. Run the check command (make I18N:check) and fix errors
6. Commit the resulting file in the project
7. Merge Pull Request

Note: the compilation of all messages will be done upon deployment (see Dockerfile)


## Update the questionnaire

1. Download the questionnaire on Google Sheet (Ask Sandrine or Nicolas for the link) in .csv format with commas as separator
2. Put the file in `mixity/static/csv` then in the right directory in function of the questionnaire, for example : an international questionnaire -> directory 'international'
3. Rename the file following this pattern : `questionnaire_name_yyyymmdd_hhmm.csv`, for example : `international_questionnaire_20210310_1458.csv`
4.  Create manually a migration in `scoring/migrations` based on a migration of a questionnaire import, for example : `0130_import_internationalbeta.py` . In this migration, change :
	* If needed, the python import of the questionnaire import script.The scripts are in `scoring/importsheets` .Make sure to use the right updated script in function of the questionnaire to import.
	* The file .csv to import
	* The migration dependencies
5. Launch the migration :
```sh
docker exec -it mixity_web_1 python manage.py migrate
```
6. If everything is OK, commit and push.

# Deploy

You need to add a new remote on your repository. The Heroku cli provide a tool to do that: heroku git:remote -a <heroku-app>.
Once it's done, run this command to let the magix happen:

	make hk:deploy

# Mailing in the development environment

In the development environment, the sending of emails is done with **MailHog** (or **Mailtrap**) in order to avoid spam in personal emails or to use them completely.
To configure this in your dev environment, you should:
## A) Use MailHog (recommended)
Nothing to configure. You just need to make sure `EMAIL_HOST` and `EMAIL_PORT` are either unset or set to `mailhog` and
`1025` respectively (in `mixity/settings/.env`). You can then access your inbox at the address http://localhost:8025/
<br>MailHog runs inside the Docker (see `docker-compose.yml`). Logs are disabled by default because MailHog doesn't have log
scopes so it prints everything including message content, attachments and WebUi requests.
## B) Use Mailtrap (deprecated)
1. Create an account on **Mailtrap**
2. Create a file in `mixity/settings/.env` where you have to define two environment variables **EMAIL_HOST_USER** and
**EMAIL_HOST_PASSWORD**
3. Get the values of these two environment variables from **username** and **password** fields after navigating to `Testing/Inboxes/SMTP Settings >> Show Credentials`
4. Set `EMAIL_HOST` and `EMAIL_PORT` to `smtp.mailtrap.io` and `2525` respectively (in `mixity/settings/.env`).

**/!\ Your Mailtrap account can be suspended at any time since Mixity is a company. Mailtrap is however more complete.**
