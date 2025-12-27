.PHONY: help build build-dev build-prod up up-dev up-prod down down-dev down-prod restart logs shell migrate makemigrations createsuperuser test clean

help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make build-dev      - Build development Docker images"
	@echo "  make up-dev         - Start development containers"
	@echo "  make down-dev       - Stop development containers"
	@echo ""
	@echo "Production:"
	@echo "  make build-prod     - Build production Docker images"
	@echo "  make up-prod        - Start production containers"
	@echo "  make down-prod      - Stop production containers"
	@echo ""
	@echo "Common:"
	@echo "  make logs           - Show logs (dev)"
	@echo "  make shell          - Access Django shell (dev)"
	@echo "  make migrate        - Run migrations (dev)"
	@echo "  make makemigrations - Create migrations (dev)"
	@echo "  make createsuperuser - Create superuser (dev)"
	@echo "  make test           - Run tests (dev)"
	@echo "  make clean          - Remove containers and volumes (dev)"

# Development commands
build-dev:
	DOCKER_BUILDKIT=1 docker-compose -f docker-compose.dev.yml build

up-dev:
	DOCKER_BUILDKIT=1 docker-compose -f docker-compose.dev.yml up -d

down-dev:
	docker-compose -f docker-compose.dev.yml down

restart-dev:
	docker-compose -f docker-compose.dev.yml restart

logs-dev:
	docker-compose -f docker-compose.dev.yml logs -f web

shell-dev:
	docker-compose -f docker-compose.dev.yml exec web python manage.py shell

migrate-dev:
	docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

makemigrations-dev:
	docker-compose -f docker-compose.dev.yml exec web python manage.py makemigrations

createsuperuser-dev:
	docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

test-dev:
	docker-compose -f docker-compose.dev.yml exec web python manage.py test

clean-dev:
	docker-compose -f docker-compose.dev.yml down -v

# Production commands
build-prod:
	docker-compose -f docker-compose.prod.yml build

up-prod:
	docker-compose -f docker-compose.prod.yml up -d

down-prod:
	docker-compose -f docker-compose.prod.yml down

restart-prod:
	docker-compose -f docker-compose.prod.yml restart

logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f web

migrate-prod:
	docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

createsuperuser-prod:
	docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

clean-prod:
	docker-compose -f docker-compose.prod.yml down -v

# Default to development (backward compatibility)
build: build-dev
up: up-dev
down: down-dev
restart: restart-dev
logs: logs-dev
shell: shell-dev
migrate: migrate-dev
makemigrations: makemigrations-dev
createsuperuser: createsuperuser-dev
test: test-dev
clean: clean-dev

