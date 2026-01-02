.PHONY: help migrate makemigrations createsuperuser test runserver collectstatic

help:
	@echo "Available commands:"
	@echo ""
	@echo "  make runserver      - Run Django development server"
	@echo "  make migrate        - Run database migrations"
	@echo "  make makemigrations - Create new migrations"
	@echo "  make createsuperuser - Create Django superuser"
	@echo "  make test           - Run tests"
	@echo "  make collectstatic  - Collect static files"

runserver:
	python manage.py runserver

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

createsuperuser:
	python manage.py createsuperuser

test:
	python manage.py test

collectstatic:
	python manage.py collectstatic --noinput
