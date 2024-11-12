DOCKER_COMPOSE = ./srcs/docker-compose.yml

all: create_path update_env build up wait_server

DOCKER_VERSION := $(shell docker --version | awk '{print $$3}' | sed 's/,//')
DOCKER_MAJOR := $(shell echo $(DOCKER_VERSION) | cut -d. -f1)
DOCKER_MINOR := $(shell echo $(DOCKER_VERSION) | cut -d. -f2)

# Définir la commande docker compose en fonction de la version de Docker
ifeq ($(shell [ $(DOCKER_MAJOR) -gt 20 ] || { [ $(DOCKER_MAJOR) -eq 20 ] && [ $(DOCKER_MINOR) -ge 10 ]; } && echo "yes"),yes)
    dockercompose = docker compose
else
    dockercompose = docker-compose
endif

HOSTNAME=$(shell hostname -I | cut -d' ' -f1)

build: check-env
	@$(dockercompose) -f $(DOCKER_COMPOSE) build
	@echo "Transcendence is ready for up"

up: check-env
	@$(dockercompose) -f $(DOCKER_COMPOSE) up -d

down: 
	@$(dockercompose) -f $(DOCKER_COMPOSE) down
	@echo "Transcendence is down"

logs:
	@$(dockercompose) -f $(DOCKER_COMPOSE) logs

logs-f:
	@$(dockercompose) -f $(DOCKER_COMPOSE) logs -f

clear: down
	@docker volume rm srcs_static 
	@docker volume rm srcs_media
	@docker volume rm srcs_postgres_data
# launching a docker for clear the transcendance folder
	@docker run --rm -v ~/transcendence:/transcendence alpine sh -c "rm -rf /transcendence/*"
	@echo "Transcendence is cleaned"

check-env:
	@if [ ! -f ./srcs/.baseenv ]; then \
		echo ".env file does not exist!"; \
		exit 1; \
	fi

update_env: check-env
	@echo	"Updating environment..."
	@cp 	./srcs/.baseenv ./srcs/.env
	@sed -i '/SERVER_NAME=/c\SERVER_NAME=$(HOSTNAME)' ./srcs/.env
	@sed -i '/DJANGO_ALLOWED_HOSTS=/c\DJANGO_ALLOWED_HOSTS=$(HOSTNAME)' ./srcs/.env
	@sed -i '/DJANGO_CSRF_TRUSTED_ORIGINS=/c\DJANGO_CSRF_TRUSTED_ORIGINS=https://$(HOSTNAME):4433' ./srcs/.env

create_path:
	@mkdir -p ~/transcendence/postgres_data
	@mkdir -p ~/transcendence/media
	@mkdir -p ~/transcendence/static


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