# OptimusApi

![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9-3776AB?style=flat-square&logo=python&logoColor=white)
![Linux](https://img.shields.io/badge/Oracle_Linux-ARM_A1-FCC624?style=flat-square&logo=linux&logoColor=black)

---

- [Español](#español)
- [English](#english)

---

## Español

- [Estructura del proyecto](#estructura-del-proyecto)
- [Respuesta de la ruta raíz](#respuesta-de-la-ruta-raíz)
- [Scripts](#scripts)
- [Setup local (Windows)](#setup-local-windows)
- [Deploy local (Windows)](#deploy-local-windows)
- [Deploy en VPS](#deploy-en-vps)
- [Agregar una nueva versión de la API](#agregar-una-nueva-versión-de-la-api)
- [Variables de entorno](#variables-de-entorno)

Plantilla base de OptimusApi con soporte para versionado de endpoints y configuración lista para producción en Linux.

### Estructura del proyecto

```
vps_optimus_api/
├── app/
│   ├── main.py              # Entry point: app FastAPI + ruta raíz
│   ├── core/
│   │   └── config.py        # Settings via pydantic-settings (.env)
│   └── api/
│       └── v1/
│           └── router.py    # Router v1 — agrega endpoints aquí
├── scripts/
│   ├── linux/
│   │   ├── setup.sh         # Inicialización única en el VPS
│   │   └── deploy.sh        # Pull + actualización de paquetes + restart
│   └── windows/
│       ├── setup.ps1        # Inicialización única en Windows (local)
│       └── deploy.ps1       # Pull + actualización de paquetes + restart local
├── requirements.txt
├── .env.example
└── README.md
```

### Respuesta de la ruta raíz

```
GET /
→ {"name": "OptimusApi", "version": "1.0.0", "status": "ok"}
```

### Scripts

| Script | Plataforma | Propósito |
|---|---|---|
| `scripts/linux/setup.sh` | VPS (Linux) | Crea `.venv`, instala dependencias, copia `.env` |
| `scripts/linux/deploy.sh` | VPS (Linux) | `git pull` → verifica paquetes → reinicia el servicio |
| `scripts/linux/start.sh` | VPS (Linux) | Inicia el servicio systemd |
| `scripts/linux/stop.sh` | VPS (Linux) | Detiene el servicio systemd |
| `scripts/windows/setup.ps1` | Windows (local) | Crea `.venv`, instala dependencias, copia `.env` |
| `scripts/windows/deploy.ps1` | Windows (local) | `git pull` → verifica paquetes → reinicia uvicorn |
| `scripts/windows/start.ps1` | Windows (local) | Inicia uvicorn en primer plano con auto-reload (Ctrl+C para detener) |

> Los scripts de deploy comparan un hash SHA-256 del `requirements.txt`. Solo reinstalan paquetes si el archivo cambió — el resto de deploys son rápidos.

### Setup local (Windows)

```powershell
# Solo la primera vez:
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

.\scripts\windows\setup.ps1

# Iniciar servidor de desarrollo:
.venv\Scripts\uvicorn.exe app.main:app --reload
```

### Deploy local (Windows)

```powershell
.\scripts\windows\deploy.ps1
```

### Deploy en VPS

#### 1. Instalar Python 3.9

```bash
sudo dnf install python3.9 python3.9-pip -y
```

#### 2. Clonar el proyecto

```bash
cd /srv
git clone <tu-repo> optimusapi
cd optimusapi
```

#### 3. Inicialización única

```bash
chmod +x scripts/linux/setup.sh scripts/linux/deploy.sh
./scripts/linux/setup.sh
# → crea .venv, instala paquetes, copia .env
```

#### 4. Editar variables de entorno

```bash
nano .env
# Asegúrate de que DEBUG=false en producción
```

#### 5. Servicio systemd

Crear `/etc/systemd/system/optimusapi.service`:

```ini
[Unit]
Description=OptimusApi
After=network.target

[Service]
User=<your-user>
WorkingDirectory=/srv/optimusapi
EnvironmentFile=-/srv/optimusapi/.env
ExecStart=/srv/optimusapi/.venv/bin/gunicorn app.main:app \
    -w 2 -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now optimusapi
sudo systemctl status optimusapi
```

> 2 workers es un buen punto de partida para la mayoría de entornos.
> El `-` en `EnvironmentFile` hace que systemd ignore el archivo si no existe.

#### 6. Nginx como proxy reverso

```bash
sudo dnf install nginx -y
sudo systemctl enable --now nginx
```

```nginx
server {
    listen 80;
    server_name api.tudominio.com;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

#### 7. Futuros deploys

```bash
./scripts/linux/deploy.sh
# → git pull → verifica paquetes → reinicia el servicio
```

### Agregar una nueva versión de la API

1. Crear `app/api/v2/` con `__init__.py` y `router.py`
2. Registrar en `app/main.py`:

```python
from app.api.v2.router import router as v2_router
app.include_router(v2_router, prefix="/api/v2")
```

> Un solo `.venv` para todas las versiones. Los paquetes se instalan **una sola vez**.

### Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `PROJECT_NAME` | `OptimusApi` | Nombre de la API |
| `API_VERSION` | `1.0.0` | Versión reportada en `/` |
| `DEBUG` | `false` | Activa `/docs`, `/redoc`, `/openapi.json` |

> `DEBUG=false` en producción desactiva la documentación automática — no expone la estructura interna de la API.

---

## English

- [Project structure](#project-structure)
- [Root route response](#root-route-response)
- [Scripts](#scripts-1)
- [Local setup (Windows)](#local-setup-windows)
- [Local deploy (Windows)](#local-deploy-windows)
- [VPS deploy](#vps-deploy)
- [Adding a new API version](#adding-a-new-api-version)
- [Environment variables](#environment-variables)

FastAPI base template with versioned endpoint support, ready for production on Linux.

### Project structure

```
vps_optimus_api/
├── app/
│   ├── main.py              # Entry point: FastAPI app + root route
│   ├── core/
│   │   └── config.py        # Settings via pydantic-settings (.env)
│   └── api/
│       └── v1/
│           └── router.py    # v1 router — add endpoints here
├── scripts/
│   ├── linux/
│   │   ├── setup.sh         # One-time VPS setup
│   │   └── deploy.sh        # Pull + package check + service restart
│   └── windows/
│       ├── setup.ps1        # One-time local setup (Windows)
│       └── deploy.ps1       # Pull + package check + local restart
├── requirements.txt
├── .env.example
└── README.md
```

### Root route response

```
GET /
→ {"name": "OptimusApi", "version": "1.0.0", "status": "ok"}
```

### Scripts

| Script | Platform | Purpose |
|---|---|---|
| `scripts/linux/setup.sh` | VPS (Linux) | Creates `.venv`, installs deps, copies `.env` |
| `scripts/linux/deploy.sh` | VPS (Linux) | `git pull` → checks packages → restarts the service |
| `scripts/linux/start.sh` | VPS (Linux) | Starts the systemd service |
| `scripts/linux/stop.sh` | VPS (Linux) | Stops the systemd service |
| `scripts/windows/setup.ps1` | Windows (local) | Creates `.venv`, installs deps, copies `.env` |
| `scripts/windows/deploy.ps1` | Windows (local) | `git pull` → checks packages → restarts uvicorn |
| `scripts/windows/start.ps1` | Windows (local) | Starts uvicorn in foreground with auto-reload (Ctrl+C to stop) |

> Deploy scripts compare a SHA-256 hash of `requirements.txt`. Packages are only reinstalled when the file changes — all other deploys are fast.

### Local setup (Windows)

```powershell
# First time only:
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

.\scripts\windows\setup.ps1

# Start dev server:
.venv\Scripts\uvicorn.exe app.main:app --reload
```

### Local deploy (Windows)

```powershell
.\scripts\windows\deploy.ps1
```

### VPS deploy

#### 1. Install Python 3.9

```bash
sudo dnf install python3.9 python3.9-pip -y
```

#### 2. Clone the project

```bash
cd /srv
git clone <your-repo> optimusapi
cd optimusapi
```

#### 3. One-time setup

```bash
chmod +x scripts/linux/setup.sh scripts/linux/deploy.sh
./scripts/linux/setup.sh
# → creates .venv, installs packages, copies .env
```

#### 4. Configure environment variables

```bash
nano .env
# Make sure DEBUG=false in production
```

#### 5. systemd service

Create `/etc/systemd/system/optimusapi.service`:

```ini
[Unit]
Description=OptimusApi
After=network.target

[Service]
User=<your-user>
WorkingDirectory=/srv/optimusapi
EnvironmentFile=-/srv/optimusapi/.env
ExecStart=/srv/optimusapi/.venv/bin/gunicorn app.main:app \
    -w 2 -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now optimusapi
sudo systemctl status optimusapi
```

> 2 workers is a good starting point for most environments.
> The `-` in `EnvironmentFile` makes systemd ignore the file if it does not exist.

#### 6. Nginx reverse proxy

```bash
sudo dnf install nginx -y
sudo systemctl enable --now nginx
```

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

#### 7. Future deploys

```bash
./scripts/linux/deploy.sh
# → git pull → checks packages → restarts the service
```

### Adding a new API version

1. Create `app/api/v2/` with `__init__.py` and `router.py`
2. Register it in `app/main.py`:

```python
from app.api.v2.router import router as v2_router
app.include_router(v2_router, prefix="/api/v2")
```

> Single `.venv` for all versions. Packages are installed **once**, no duplication.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `PROJECT_NAME` | `OptimusApi` | API name |
| `API_VERSION` | `1.0.0` | Version reported at `/` |
| `DEBUG` | `false` | Enables `/docs`, `/redoc`, `/openapi.json` |

> `DEBUG=false` in production disables auto-generated docs — keeps the API structure hidden.
