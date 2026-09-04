# Deploy en PythonAnywhere — GimApp

## 1. Prerrequisitos

- Cuenta PythonAnywhere (plan Hacker o superior para custom domain / always-on)
- Repo Git accesible (GitHub/GitLab/Bitbucket)
- Python 3.12 disponible en PA

---

## 2. Primer deploy desde cero

### 2.1 Crear Web App

1. Pestaña **Web** → **Add a new web app**
2. Domain: `tu-usuario.pythonanywhere.com` (o custom domain)
3. **Manual configuration** (no Django preset)
4. Python version: **3.12**
5. Path: `/home/tu-usuario/Gim-app` (se crea en siguiente paso)

### 2.2 Virtualenv — descubrir y activar

```bash
# En consola Bash de PA
# 1. Ver virtualenvs existentes
lsvirtualenv
#    ó
ls ~/.virtualenvs/

# 2. Si no existe "gimnasio", créalo con Python 3.12
mkvirtualenv --python=/usr/bin/python3.12 gimnasio

# 3. Activar (usa el nombre REAL que aparezca en lsvirtualenv)
workon gimnasio
```

> **Nota**: El nombre del virtualenv puede variar. Siempre usa `lsvirtualenv` primero y luego `workon <nombre_exacto>`.

### 2.3 Clonar repo

```bash
cd ~
git clone https://github.com/TU_USUARIO/Gim-App.git Gim-app
cd Gim-app
```

### 2.4 Instalar dependencias

```bash
workon gimnasio
pip install -r requirements.txt
```

### 2.5 Variables de entorno

Crear `.env` en la raíz del proyecto (`/home/tu-usuario/Gim-app/.env`):

```env
SECRET_KEY=tu-secret-key-larga-y-aleatoria
DEBUG=False
ALLOWED_HOSTS=tu-usuario.pythonanywhere.com
```

> Generar `SECRET_KEY`:
> `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

### 2.6 Configurar Web App (pestaña Web)

**Code:**
- Source code: `/home/tu-usuario/Gim-app`
- Working directory: `/home/tu-usuario/Gim-app`

**WSGI file** (`/var/www/tu-usuario_pythonanywhere_com_wsgi.py`):
```python
import os
import sys

path = '/home/tu-usuario/Gim-app'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Static files:**
| URL | Directory |
|-----|-----------|
| `/static/` | `/home/tu-usuario/Gim-app/staticfiles` |

### 2.7 Base de datos, estáticos y datos iniciales

```bash
cd ~/Gim-app
workon gimnasio
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_inicial  # crea admin, turnos, planes
```

### 2.8 Reload

Click **Reload** (botón verde arriba a la derecha en pestaña Web).

---

## 3. Redeploy (actualizaciones posteriores)

```bash
cd ~/Gim-app
workon gimnasio
git pull origin master
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
# Reload en pestaña Web
```

---

## 4. Comandos útiles en PA

| Tarea | Comando |
|-------|---------|
| Shell Django | `python manage.py shell` |
| Crear superuser manual | `python manage.py createsuperuser` |
| Ver logs | Pestaña **Web → Log files** (error.log / server.log) |
| Backup DB | `cp db.sqlite3 db_backup_$(date +%F).sqlite3` |
| Ejecutar tests | `python manage.py test` |

---

## 5. Checklist post-deploy

- [ ] Admin accesible en `https://tu-usuario.pythonanywhere.com/admin/`
- [ ] Login funciona (profesor / dueño)
- [ ] Estilos CSS cargan (WhiteNoise)
- [ ] HTMX requests responden (200/204)
- [ ] Reportes solo visible para dueño
- [ ] Import/Export (XML/Excel/CSV) funciona
- [ ] `DEBUG=False` confirmado
- [ ] `ALLOWED_HOSTS` correcto

---

## 6. Troubleshooting común

| Síntoma | Causa | Solución |
|---------|-------|----------|
| Admin sin estilos | `collectstatic` no corrido o Static files mal mapeado | Revisar mapping `/static/` → `staticfiles`, correr `collectstatic` |
| `DisallowedHost` | `ALLOWED_HOSTS` incorrecto | Agregar dominio exacto en `.env` |
| `SECRET_KEY` error | No seteada en `.env` | Generar y agregar a `.env` |
| Axes bloquea admin | `AXES_ENABLE_ADMIN = True` | Cambiar a `False` en `settings.py` |
| Import falla XXE | `defusedxml` no instalado | `pip install defusedxml` (ya en requirements) |
| Error 500 sin logs | `DEBUG=False` oculta traceback | Revisar `error.log` en pestaña Web |

---

## 7. Archivos clave en prod

```
/home/tu-usuario/Gim-app/
├── .env                    # Variables de entorno (NO commitear)
├── db.sqlite3              # Base de datos (backup regular)
├── staticfiles/            # collectstatic output (servido por WhiteNoise)
├── config/settings.py      # AXES_ENABLE_ADMIN = False
└── requirements.txt        # Whitenoise, axes, defusedxml, etc.
```

---

## 8. Referencias

- [PythonAnywhere Django Guide](https://help.pythonanywhere.com/pages/DeployingDjango/)
- [WhiteNoise Django](http://whitenoise.evans.io/en/stable/django.html)
- [django-axes](https://django-axes.readthedocs.io/)