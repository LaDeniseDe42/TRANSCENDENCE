DOCKER_COMPOSE = ./srcs/docker-compose.yml

all: create_path update_env build up wait_server

HOSTNAME=$(shell hostname | sed "s/.42mulhouse.fr//g")# Get the hostname without the .42mulhouse.fr

build: check-env
	@docker-compose -f $(DOCKER_COMPOSE) build
	@echo "Transcendence is ready for up"

up: check-env
	@docker-compose -f $(DOCKER_COMPOSE) up -d

down: 
	@docker-compose -f $(DOCKER_COMPOSE) down
	@echo "Transcendence is down"

logs:
	@docker-compose -f $(DOCKER_COMPOSE) logs

logs-f:
	@docker-compose -f $(DOCKER_COMPOSE) logs -f

clear: down
	@docker volume rm srcs_static 
	@docker volume rm srcs_media
	@docker volume rm srcs_postgres_data
# launching a docker for clear the transcendance folder
	@docker run --rm -v /goinfre/${USER}/transcendence:/goinfre/${USER}/transcendence alpine sh -c "rm -rf /goinfre/${USER}/transcendence/*"
	@echo "Transcendence is cleaned"

check-env:
	@if [ ! -f ./srcs/.baseenv ]; then \
		echo ".env file does not exist!"; \
		exit 1; \
	fi

update_env: check-env
	@echo "Updating environment..."
	@cp 		./srcs/.baseenv ./srcs/.env
	@sed -i '/SERVER_NAME=/c\SERVER_NAME=$(HOSTNAME)' ./srcs/.env
	@sed -i '/DJANGO_ALLOWED_HOSTS=/c\DJANGO_ALLOWED_HOSTS=$(HOSTNAME)' ./srcs/.env
	@sed -i '/DJANGO_CSRF_TRUSTED_ORIGINS=/c\DJANGO_CSRF_TRUSTED_ORIGINS=https://$(HOSTNAME):4433' ./srcs/.env

create_path:
	@mkdir -p /goinfre/${USER}/transcendence/postgres_data
	@mkdir -p /goinfre/${USER}/transcendence/media
	@mkdir -p /goinfre/${USER}/transcendence/static


URL=https://$(HOSTNAME):4433
wait_server:
	@echo "Attente du serveur..."
	@while : ; do \
		http_code=$$(curl --insecure -s -o /dev/null -w "%{http_code}" $(URL)); \
		if [ "$$http_code" != "502" ]; then \
			printf "\rBackend actif, arrêt de la boucle.\033[K; \n"; \
			break; \
		fi; \
		printf "\rBackend encore inactif, nouvelle tentative dans quelques secondes..."; \
		sleep 1; \
	done
	@echo "Le serveur est prêt !"


re: clear all

.PHONY: all build up down logs clear check-env update_env re   # Prevent make from doing something with a file named like the target