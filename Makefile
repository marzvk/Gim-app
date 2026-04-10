# Variables para facilitar cambios
PYTHON = python3
MANAGE = $(PYTHON) manage.py

help:
	@echo "Comandos disponibles:"
	@echo "  make run        - Iniciar el servidor de desarrollo"
	@echo "  make migrations - Crear nuevas migraciones"
	@echo "  make migrate    - Aplicar migraciones a la base de datos"
	@echo "  make freeze     - Actualizar el archivo requirements.txt"
	@echo "  make shell      - Entrar a la shell de Django"
	@echo "  make tree       - Genera archivo txt con el arbol del project"


run:
	$(MANAGE) runserver

migrations:
	$(MANAGE) makemigrations

migrate:
	$(MANAGE) migrate

freeze:
	pip freeze > requirements.txt

shell:
	$(MANAGE) shell
tree:
	tree > tree.txt

