include .env

GREEN = \033[0;32m
COLOR_OFF = \033[0m

all: build

volumes:
	@echo "$(GREEN)<+> CREATING VOLUMES <+>$(COLOR_OFF)"
	@mkdir -p $(POSTGRESQL_VOLUME_PATH)

build: volumes
	@echo "$(GREEN)<+> BUILDING CONTAINERS <+>$(COLOR_OFF)"
	@docker compose -f $(DOCKER_COMPOSE) up --build -d

postgresql: volumes
	@echo "$(GREEN)<+> BUILDING POSTGRESQL CONTAINER <+>$(COLOR_OFF)"
	@docker compose -f $(DOCKER_COMPOSE) up --build -d postgresql

frontend: volumes
	@echo "$(GREEN)<+> BUILDING FRONTEND CONTAINER <+>$(COLOR_OFF)"
	@docker compose -f $(DOCKER_COMPOSE) up --build -d frontend

backend: volumes
	@echo "$(GREEN)<+> BUILDING BACKEND CONTAINER <+>$(COLOR_OFF)"
	@docker compose -f $(DOCKER_COMPOSE) up --build -d backend

restart: down
	@echo "$(GREEN)<+> STARTING CONTAINERS <+>$(COLOR_OFF)"
	@docker compose -f $(DOCKER_COMPOSE) up -d

stop:
	@echo "$(GREEN)<+> STOPPING CONTAINERS <+>$(COLOR_OFF)"
	@docker compose -f $(DOCKER_COMPOSE) stop

down: stop
	@echo "$(GREEN)<+> DELETING BUILD <+>$(COLOR_OFF)"
	@docker compose -f $(DOCKER_COMPOSE) down -v

destroy: down
	@echo "$(GREEN)<+> REMOVING ALL IMAGES <+>$(COLOR_OFF)"
	@rm -rf $(POSTGRESQL_VOLUME_PATH)
	@docker system prune -af

re: destroy build
	@echo "$(GREEN)<+> RESETTING CONTAINERS <+>$(COLOR_OFF)"

.PHONY: all build stop down destroy restart volumes re postgresql frontend backend
