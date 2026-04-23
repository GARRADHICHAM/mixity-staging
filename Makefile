# Force execute all targets
.PHONY: *
# All commands in a single shell
.ONESHELL:
# Stop on error
.SHELLFLAGS=-ec

# Global
APP				= $(shell git config --get remote.heroku.url | sed -n "s|.*/\(.*\\).git|\1|p")
ECHO 			= echo
SED		 		= sed
DOCKER_EXE		= docker exec -i
DOCKER_EXE_TTY	= docker exec -it
DCO_EXE			= docker compose
PYTHON			= ${DOCKER_EXE_TTY} mixity-web-1 python
BASH			= ${DOCKER_EXE_TTY} mixity-web-1 /bin/bash -c "source /root/.bashrc; $(1)"
YARN			= $(call BASH, yarn $(1))
BRANCH			= $(shell git rev-parse --abbrev-ref HEAD)
RELEASE_BRANCH	= develop
VERSION_FILE    = "mixity/settings/base.py"
GET_VERSION		= $(shell $(SED) -nE 's/^VERSION = "(.+)"$$/\1/p' $(VERSION_FILE))
GET_LAST_TAG	= $(shell git describe --tags)

# Coverage
COVERAGE        = ${DOCKER_EXE_TTY} mixity-web-1 coverage
COVERAGE_OUTPUT = .coverage-html

# Cleaning
RM_EXTS			= '*~' '*\#'
RM_PATHS		= .coverage coverage.xml htmlcov dist ${COVERAGE_OUTPUT}

# I18N
TEMPLATE_EXTS	   = html,txt,xml,json,py
TEMPLATE_IGNORES	= --ignore=.heroku/* --ignore=assets/* --ignore=tmp/* --ignore=venv/* --ignore=node_modules/*
TEMPLATE_LANGUAGES  = -l fr -l en -l es -l it -l zh_Hans -l zh_Hant -l ja

# Colors
C_BLACK	 	= \\033[0;30m
C_RED	   	= \\033[1;31m
C_GREEN		= \\033[0;32m
C_YELLOW	= \\033[0;33m
C_BLUE	  	= \\033[1;34m
C_PURPLE	= \\033[0;35m
C_CYAN	  	= \\033[0;36m
C_WHITE	 	= \\033[0;37m
C_BOLD	 	= \\033[1;37m
C_END		= \\033[0m


##### GLOBAL #####

config:
	$(ECHO) "Heroku app: $(C_YELLOW)$(APP)$(C_END)"
	$(ECHO) "Server version: $(C_YELLOW)$(GET_VERSION)$(C_END)"
	$(ECHO) "Git branch: $(C_YELLOW)$(BRANCH)@$(GET_LAST_TAG)$(C_END)"
	$(ECHO) "Python: $(C_YELLOW)$(shell $(PYTHON) --version)$(C_END)"
	$(ECHO) "User: $(C_YELLOW)$(USER)$(C_END)"

help:
	$(ECHO) "Usage: make <command>"
	$(ECHO) "- assets: compile JS using yarn"
	$(ECHO) "- clean: remove build artifacts and editor temporary files"
	$(ECHO) "- config: display usefull environment informations"
	$(ECHO) "- deploy: deploy branch $(RELEASE_BRANCH) on $(APP) (release + push)"
	$(ECHO) "- import_app_db: create, download and apply to local DB an app backup"
	$(ECHO) "- install: initialize dev environment"
	$(ECHO) "- migrate: apply django migrations"
	$(ECHO) "- migrations: generate django migrations"
	$(ECHO) "- permissions: restore default file and folder permissions and owner"
	$(ECHO) "- release: generate a new release on branch $(RELEASE_BRANCH) (version + tag + release notes)"
	$(ECHO) "- reset_db: apply old backup to local DB"
	$(ECHO) "- rs: start Mixity server and database"
	$(ECHO) "- shell: open django shell"
	$(ECHO) "- update: update docker image (download apt/pip/yarn packages and dependencies)"
	$(ECHO) "- export_to_webflow: export evaluations data to webflow"

# MUST NOT BE THE FIRST TARGET
ifndef VERBOSE
# Silent the Makefile. Use VERBOSE to disable.
.SILENT:
endif

confirm:
	$(ECHO) "Entrez $(C_BOLD)$(MSG)$(C_END) pour valider"
	read -p "> " ANSWER; \
	case "$$ANSWER" in \
		$(MSG) ) exit 0;; \
		* ) $(ECHO) "$(C_RED)CANCELLED$(C_END)"; exit 1;; \
	esac

clean:
	$(ECHO) "$(C_BLUE)rm -rf $(C_YELLOW)$(RM_PATHS)$(C_END)"
	rm -rf $(RM_PATHS)
	for ext in $(RM_EXTS); \
	do \
		$(ECHO) "$(C_BLUE)find . -type f -name $(C_YELLOW)$$ext $(C_BLUE)-delete$(C_END)"; \
		find . -type f -name "$$ext" -delete; \
	done
	$(ECHO) "$(C_BLUE)Cleaning git branches$(C_END)"
	git branch --merged | egrep -v "(^\*|master|dev)" | xargs git branch -d
	git fetch --prune origin


##### Docker #####

up:
	${DCO_EXE} up

up_web: up_d
	docker attach mixity-web-1

up_cache: up_d
	docker attach mixity-cache-1

up_d:
	${DCO_EXE} up -d

rs:
	${DCO_EXE} restart && docker attach mixity-web-1

rs_d:
	${DCO_EXE} restart

ps:
	docker ps

shell:
	${PYTHON} manage.py shell_plus

migrate:
	${PYTHON} manage.py migrate $(ARGS)

show:
	${PYTHON} manage.py showmigrations

migrations:
	${PYTHON} manage.py makemigrations $(ARGS)
	make permissions

permissions:
	sudo chown -R ${USER}:${USER} .
	find . -type d -exec chmod 755 {} \;
	find . -name "*migrations*" -type f -exec chmod 644 {} \;

createadminsuperuser:
# Superuser
	${PYTHON} manage.py shell -c "from accounts.models import MixityUser; MixityUser.objects.create_superuser('admin', 'admin@example.com', 'admin')"

reset_db:
	$(ECHO) "\n$(C_BLUE)Destroy local database $(C_END)"
	docker-compose down -v
	$(ECHO) "\n$(C_BLUE)Drop local database $(C_END)"
	docker volume rm -f postgresql
	$(ECHO) "\n$(C_BLUE)Up local database $(C_END)"
	docker-compose up -d db
	sleep 5
	$(ECHO) "\n$(C_BLUE)Apply backup $(C_YELLOW)$(DUMPFILE)$(C_BLUE) to local database $(C_END)"
	- ${DOCKER_EXE} mixity-db-1 pg_restore --exit-on-error --verbose --no-acl --no-owner -U user -d db --schema=public < $(DUMPFILE)
	make up_d

import_app_db:
	$(eval DUMPFILE := $(shell $(ECHO) backup_$(APP)_`date +%Y%m%d_%H%M`.dump))
	make hk:download_backup APP=$(APP) DUMPFILE=$(DUMPFILE)
	make reset_db DUMPFILE=$(DUMPFILE)

dump_db:
	${DOCKER_EXE} mixity-db-1 ./pg_manager.sh dump

load_db:
	${DOCKER_EXE} mixity-db-1 ./pg_manager.sh load

update build:
	${DCO_EXE} build

install:
	make update
	$(ECHO) "$(C_YELLOW)Lancez la commande 'make up' dans un autre terminal puis tapez entrée pour continuer l'installation.$(C_END)"
	read ANSWER;
	make import_app_db APP=mixity-staging
	make assets I18N migrate
	$(call YARN, )
	$(call BASH, cd dashboard && yarn)
	$(call BASH, cd collaborator_evaluation && yarn)

import:
	${PYTHON} manage.py import_sheets_questions --society

sass:
	$(call BASH, npm rebuild node-sass)
assets static: sass
	$(call YARN, build)

watch:
	$(call YARN, start)

bash ssh:
	${DOCKER_EXE_TTY} mixity-web-1 bash

allow_release:
# Checking release type
ifndef TYPE
	$(ECHO) "$(C_RED)You must specify a release type $(C_YELLOW)major $(C_RED)|$(C_YELLOW) minor $(C_RED)|$(C_YELLOW) patch$(C_RED) (example: $(C_BLUE)make release TYPE=patch$(C_RED))$(C_END)"
	exit 1
endif
# Checking branch
ifneq ($(BRANCH), $(RELEASE_BRANCH))
	$(ECHO) "$(C_RED)You need to be on $(C_YELLOW)$(RELEASE_BRANCH)$(C_RED) to release$(C_END)"
	exit 1
endif
# Checking git
# Thanks to https://stackoverflow.com/a/57510633
	git update-index -q --ignore-submodules --refresh
ifneq ($(shell git diff-files --quiet --ignore-submodules; $(ECHO) $$?), 0)
	$(ECHO) "$(C_RED)Your git repository is dirty, please commit/stash/checkout before release$(C_END)"
	exit 1
endif
ifneq ($(shell git diff-index --cached --quiet --ignore-submodules HEAD -- 2>&1 > /dev/null; $(ECHO) $$?), 0)
	$(ECHO) "$(C_RED)Your git repository is outdated, please pull before release$(C_END)"
	exit 1
endif
# Checking migrations
ifneq ($(shell $(PYTHON) manage.py makemigrations --check --noinput --dry-run 2>&1 > /dev/null; $(ECHO) $$?), 0)
	$(ECHO) "$(C_RED)You have missing, unapplied or conflicting migrations, please fix them before release$(C_END)"
	exit 1
endif

release: allow_release I18N\:generate I18N\:check I18N\:compile test
# Thanks to and https://stackoverflow.com/a/54776239 and https://stackoverflow.com/a/1909390 and https://unix.stackexchange.com/a/575097
	VERSION=$(shell ./inc_version.sh $(TYPE) $(VERSION_FILE)) && \
	$(ECHO) "$(C_RED)Generating version $(C_YELLOW)$$VERSION$(C_RED) on branch $(C_YELLOW)$(BRANCH)$(C_END)" && \
	make assets && \
	git commit -am "Makefile: creating release $$VERSION" && \
	git tag -fa "$$VERSION" && \
	git push origin && \
	git push origin "$$VERSION"

deploy: release
	make hk:deploy

export_to_webflow:
	${PYTHON} manage.py export_to_webflow

##### TEST #####

profile_test:
	$(PYTHON) -m cProfile -o profile.out -s cumulative manage.py test --keepdb $(ARGS)

test:
ifdef ARGS
	$(ECHO) "$(C_BLUE)python manage.py test --keepdb $(C_YELLOW)$(ARGS)$(C_END)"
	$(PYTHON) manage.py test --keepdb $(ARGS)
else
	$(ECHO) "$(C_BLUE)python manage.py test $(C_YELLOW)--noinput --parallel$(C_END)"
	$(PYTHON) manage.py test --noinput --parallel
endif

coverage\:run:
	${COVERAGE} run --source='.' manage.py test

coverage: coverage\:run
	${COVERAGE} report

coverage\:web:
	${MAKE} coverage\:run; ${COVERAGE} html -d $(COVERAGE_OUTPUT); xdg-open $(COVERAGE_OUTPUT)/index.html


##### I18N #####

I18N\:generate:
# Create the .po files used for i18n
	$(ECHO) "$(C_BLUE)make template and python messages $(C_YELLOW)$(TEMPLATE_EXTS)$(C_END)"
	$(PYTHON) manage.py makemessages $(TEMPLATE_LANGUAGES) $(TEMPLATE_IGNORES) --extension=$(TEMPLATE_EXTS)
	$(ECHO) "$(C_BLUE)make DB messages $(C_YELLOW)Category, Subcategory, FAQCategory, NamsorEthnicity$(C_END)"
	$(PYTHON) manage.py db_pofiles
	$(ECHO) "$(C_BLUE)make JS messages $(C_YELLOW)djangojs$(C_END)"
	$(PYTHON) manage.py makemessages $(TEMPLATE_LANGUAGES) $(TEMPLATE_IGNORES) --extension=js -d djangojs
# $(ECHO) "$(C_BLUE)autotranslate messages with $(C_YELLOW)GoogleTranslate$(C_END)"
# $(PYTHON) manage.py autotranslate_pofiles

I18N\:check:
	$(ECHO) "$(C_BLUE)check messages $(C_END)"
	$(PYTHON) manage.py check_pofiles

I18N\:compile:
# Compile the gettext files
	$(ECHO) "$(C_BLUE)compilemessages $(C_YELLOW)$(TEMPLATE_LANGUAGES)$(C_END)"
	$(PYTHON) manage.py compilemessages $(TEMPLATE_LANGUAGES)

I18N\:starify:
	make I18N:generate
	$(PYTHON) manage.py starify_pofile
	make I18N:compile

I18N\:unstarify:
	git checkout mixity/locale/fr/

I18N:
	make I18N:generate && make I18N:check && make I18N:compile


##### HEROKU #####

hk\:shell:
	heroku run python manage.py shell_plus --app $(APP)

hk\:bash hk\:ssh:
	heroku run bash --app $(APP)

hk\:maintenance_on:
	$(ECHO) "$(C_BLUE)heroku $(C_YELLOW)maintenance:on$(C_BLUE) --app $(C_YELLOW)$(APP)$(C_END)"
	heroku maintenance:on --app $(APP)

hk\:maintenance_off:
	$(ECHO) "$(C_BLUE)heroku $(C_YELLOW)maintenance:off$(C_BLUE) --app $(C_YELLOW)$(APP)$(C_END)"
	heroku maintenance:off --app $(APP)

hk\:configure:
	$(ECHO) "\n$(C_BLUE)Current buildpacks on app $(C_YELLOW)$(APP)$(C_END)"
	heroku buildpacks --app $(APP)
	make confirm MSG=y
	heroku buildpacks:clear --app $(APP)
# heroku buildpacks:add --index 1 heroku-community/apt --app $(APP)
	heroku buildpacks:add --index 1 https://github.com/grauwoelfchen/heroku-buildpack-gettext --app $(APP)
	heroku buildpacks:add --index 2 heroku/python --app $(APP)
	$(ECHO) "\n$(C_BLUE)New buildpacks on app $(C_YELLOW)$(APP)$(C_END)"
	heroku buildpacks --app $(APP)

hk\:allow_deploy:
ifneq ($(shell git describe --exact-match --tags 2>&1 > /dev/null; $(ECHO) $$?), 0)
	$(ECHO) "$(C_RED)You can't deploy without having HEAD exactly on a tag, make a release first$(C_END)"
	exit 1
endif

hk\:deploy: hk\:allow_deploy hk\:hotfix

hk\:hotfix:
	VERSION=$(GET_VERSION) && \
	$(ECHO) "$(C_RED)Deploying version $(C_YELLOW)$$VERSION$(C_RED) on app $(C_YELLOW)$(APP)$(C_END)" && \
	git push heroku $(BRANCH):master && \
	$(ECHO) "$(C_RED)Deployment of version $(C_YELLOW)$$VERSION$(C_RED) on app $(C_YELLOW)$(APP)$(C_RED) completed !$(C_END)"

hk\:download_backup:
	$(ECHO) "\n$(C_BLUE)Create backup $(C_END)"
	heroku pg:backups:capture --app $(APP)
	$(ECHO) "\n$(C_BLUE)Download backup $(C_END)"
	heroku pg:backups:download --app $(APP)
	$(ECHO) "\n$(C_BLUE)Rename backup $(C_END)"
	if [ -z "$(DUMPFILE)" ]; then \
		mv latest.dump backup_$(APP)_`date +%Y%m%d_%H%M`.dump; \
	else \
		mv latest.dump $(DUMPFILE); \
	fi

hk\:restore_db:
	$(ECHO) "$(C_RED)Restoring PostgreSql database backup $(C_YELLOW)$(BACKUP_NAME)$(C_RED) on heroku app $(C_YELLOW)$(APP)$(C_RED)"
	$(ECHO) "$(C_RED)THIS WILL DESTROY EVERYTHING AND LOSSE ALL DATA ADDED AFTER THIS BACKUP"
	make confirm MSG=$(APP)
	heroku pg:backups:restore $(BACKUP_NAME) --app $(APP)
