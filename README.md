# OptimusApi

![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9-3776AB?style=flat-square&logo=python&logoColor=white)
![Nginx](https://img.shields.io/badge/nginx-1.x-009639?style=flat-square&logo=nginx&logoColor=white)
![Linux](https://img.shields.io/badge/Oracle_Linux-ARM_A1-FCC624?style=flat-square&logo=linux&logoColor=black)

---

- [Español](#español)
- [English](#english)

---

## Español

- [Estructura del proyecto](#estructura-del-proyecto)
- [Endpoints](#endpoints)
- [Autenticación](#autenticación)
- [Scripts](#scripts)
- [Setup local (Windows)](#setup-local-windows)
- [Deploy local (Windows)](#deploy-local-windows)
- [Deploy en VPS](#deploy-en-vps)
- [Configuración de Nginx](#6-nginx-como-proxy-reverso)
- [HTTPS con Cloudflare (subdominio)](#7-https-con-cloudflare-origin-certificate)
- [Seguridad y rate limiting](#9-seguridad-y-rate-limiting)
- [Gestión de concurrencia](#gestión-de-concurrencia)
- [Variables de entorno](#variables-de-entorno)

API de compresión de imágenes y videos desplegada en Oracle Linux ARM (Ampere A1). Comprime imágenes en memoria sin archivos temporales, soporta lotes de hasta 10 archivos y devuelve el resultado como archivo directo o ZIP. Los videos se comprimen de forma asíncrona mediante subida por chunks, cola de procesamiento FFmpeg y descarga directa.

### Estructura del proyecto

```
vps_optimus_api/
├── app/
│   ├── main.py              # Entry point: app FastAPI + rutas raíz y guide
│   ├── guide.py             # HTML guide bilingüe servida en GET /guide
│   ├── core/
│   │   ├── config.py        # Settings via pydantic-settings (.env)
│   │   └── security.py      # Dependencia verify_api_key (X-API-Key header)
│   ├── api/
│   │   └── v1/
│   │       ├── router.py    # Router v1
│   │       └── media/
│   │           └── router.py  # Endpoints de compresión de imágenes y videos
│   └── services/
│       └── image_compressor.py  # Lógica de compresión en memoria (Pillow)
├── scripts/
│   ├── linux/
│   │   ├── setup.sh         # Inicialización única en el VPS
│   │   └── deploy.sh        # Pull + actualización de paquetes + restart
│   └── windows/
│       ├── setup.ps1        # Inicialización única en Windows (local)
│       └── deploy.ps1       # Pull + actualización de paquetes + restart local
├── requirements.txt
├── optimus-api.service      # Archivo de referencia del servicio systemd
└── README.md
```

### Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `GET` | `/` | No | Estado de la API |
| `GET` | `/guide` | No | Guía interactiva bilingüe (HTML) |
| `GET` | `/api/v1/status` | Sí | Estado del servidor y colas de procesamiento |
| `POST` | `/api/v1/media/images/compress` | Sí | Compresión de imágenes |
| `POST` | `/api/v1/media/videos/upload/init` | Sí | Inicia la subida de un video · devuelve `upload_id` |
| `POST` | `/api/v1/media/videos/upload/chunk` | Sí | Sube un fragmento del video (≤90 MB) |
| `POST` | `/api/v1/media/videos/upload/finalize` | Sí | Finaliza la subida y encola la compresión · devuelve `job_id` |
| `GET` | `/api/v1/media/videos/status/{job_id}` | Sí | Consulta el estado del job · retorna `progress_pct` (0–100) para barra de carga |
| `GET` | `/api/v1/media/videos/download/{job_id}` | Sí | Descarga el video comprimido |

**POST `/api/v1/media/images/compress`** — multipart/form-data

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `files` | `File[]` | Sí | Hasta 10 imágenes (jpg, png, webp). Máx 50 MB/archivo, 200 MB total |
| `out` | `string` | No | Formato de salida: `jpg`, `webp`, `png` |
| `size` | `int` | No | Dimensión máxima en píxeles del lado más largo (1–8000) |

Respuesta: archivo único → `StreamingResponse` directo · múltiples → ZIP.

Headers de respuesta:
```
X-Optimus-Status: complete | partial | timeout
X-Optimus-Processed: <int>
X-Optimus-Total: <int>
```

### Autenticación

Todos los endpoints bajo `/api/v1/` requieren el header `X-API-Key`:

```
X-API-Key: tu_api_key
```

El valor se configura en `.env` como `API_KEY`. Si falta o es incorrecto, se devuelve 401.

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

#### 2. Instalar FFmpeg y ffprobe (requerido para compresión de video)

Los repositorios ARM64 de Oracle Linux no incluyen FFmpeg. Se usa el binario estático de [johnvansickle.com](https://johnvansickle.com/ffmpeg/):

```bash
# Descargar y extraer en /tmp
wget -P /tmp https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz
tar xf /tmp/ffmpeg-release-arm64-static.tar.xz -C /tmp

# Copiar ambos binarios al sistema
sudo cp /tmp/ffmpeg-*-arm64-static/ffmpeg  /usr/local/bin/ffmpeg
sudo cp /tmp/ffmpeg-*-arm64-static/ffprobe /usr/local/bin/ffprobe
sudo chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe

# Limpiar
rm -rf /tmp/ffmpeg-*-arm64-static /tmp/ffmpeg-release-arm64-static.tar.xz

# Verificar
ffmpeg -version
ffprobe -version
```

> Versión instalada en producción: **ffmpeg 7.0.2** / **ffprobe 7.0.2** (static ARM64)

#### 3. Clonar el proyecto

```bash
cd /srv
git clone <tu-repo> optimusapi
cd optimusapi
```

#### 4. Inicialización única

```bash
chmod +x scripts/linux/setup.sh scripts/linux/deploy.sh
./scripts/linux/setup.sh
# → crea .venv, instala paquetes, copia .env
```

#### 5. Editar variables de entorno

```bash
nano .env
# Asegúrate de que DEBUG=false en producción
```

#### 6. Servicio systemd

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

#### 7. Nginx como proxy reverso

Instalar y habilitar:

```bash
sudo dnf install nginx -y
sudo systemctl enable --now nginx
```

Crear el archivo de configuración del sitio:

```bash
sudo nano /etc/nginx/conf.d/optimus.conf
```

Contenido del archivo:

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

Validar y recargar:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Abrir puertos en el firewall:

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

Verificar que todo responde:

```bash
curl http://127.0.0.1:8000      # directo a gunicorn
curl http://api.tudominio.com   # a través de nginx
```

#### 8. HTTPS con Cloudflare Origin Certificate

> **Aplica cuando:** el VPS sirve desde un subdominio (ej. `api.tudominio.com`) y el dominio raíz (`tudominio.com`) ya tiene otra app (Vercel, Netlify, etc.) con el proxy de Cloudflare activo. Cambiar el modo SSL de la zona afectaría el dominio principal; esta solución habilita HTTPS solo en el subdominio del VPS.

**Por qué el modo Flexible no es suficiente**

Con Cloudflare en modo **Full (Strict)** (recomendado), el edge de Cloudflare exige que el servidor de origen también hable HTTPS. Si el dominio raíz tiene otra app, cambiar el modo global a Flexible la rompería. La solución es instalar un **Cloudflare Origin Certificate** en nginx — es gratuito, válido 15 años y solo funciona entre Cloudflare y el servidor.

**Paso 1 — Generar el certificado en Cloudflare**

1. Cloudflare → tu zona → **SSL/TLS** → **Origin Server**
2. Clic en **Create Certificate**
3. Deja los hostnames por defecto (`*.tudominio.com` y `tudominio.com`)
4. Validity: **15 years**
5. Clic **Create**
6. Copia el **Certificate** y la **Private Key** — solo se muestran una vez

**Paso 2 — Guardar el cert en el VPS**

```bash
sudo mkdir -p /etc/nginx/ssl
sudo nano /etc/nginx/ssl/origin.crt   # pega el Certificate
sudo nano /etc/nginx/ssl/origin.key   # pega la Private Key
sudo chmod 600 /etc/nginx/ssl/origin.key
```

**Paso 3 — Actualizar la configuración de nginx**

```bash
sudo nano /etc/nginx/conf.d/optimus.conf
```

Reemplaza el contenido con:

```nginx
server {
    listen 80;
    server_name api.tudominio.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name api.tudominio.com;

    ssl_certificate     /etc/nginx/ssl/origin.crt;
    ssl_certificate_key /etc/nginx/ssl/origin.key;

    client_max_body_size 200m;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

**Paso 4 — Habilitar conexiones de red en nginx (SELinux)**

En Oracle Linux con SELinux en modo `enforcing`, nginx necesita permiso explícito para conectarse a procesos locales:

```bash
sudo setsebool -P httpd_can_network_connect 1
```

**Paso 5 — Configurar el modo SSL en Cloudflare**

Cloudflare → SSL/TLS → Overview → cambiar a **Full (Strict)**

> Esto no afecta otras apps en el dominio raíz siempre que también tengan certificados válidos (Vercel y Netlify los incluyen por defecto).

**Verificar:**

```bash
curl https://api.tudominio.com
# → {"name":"OptimusApi","version":"1.0.0","status":"ok"}
```

#### 9. Futuros deploys

```bash
./scripts/linux/deploy.sh
# → git pull → verifica paquetes → reinicia el servicio
```

#### 10. Seguridad y rate limiting

**Límite de tamaño de request**

Ya incluido en el bloque `listen 443 ssl` del paso 7 como `client_max_body_size 200m;`. nginx devuelve 413 antes de que el request llegue a la app.

**Rate limiting con nginx**

Crea el archivo de zona (los archivos en `conf.d/` se incluyen dentro del bloque `http {}` de nginx.conf):

```bash
sudo tee /etc/nginx/conf.d/rate-limit.conf <<'EOF'
limit_req_zone $http_cf_connecting_ip zone=api:10m rate=5r/s;
EOF
```

Agrega `limit_req` dentro del bloque `location /` en `optimus.conf`:

```nginx
location / {
    limit_req zone=api burst=20 nodelay;

    proxy_pass         http://127.0.0.1:8000;
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

> Se usa `$http_cf_connecting_ip` en lugar de `$binary_remote_addr` porque nginx está detrás de Cloudflare — ese header contiene la IP real del usuario. `5r/s` con `burst=20 nodelay` permite picos cortos sin demora extra, luego rechaza con 429.

**fail2ban — protección SSH contra fuerza bruta**

Requiere habilitar el repo EPEL primero (Oracle Linux 9):

```bash
sudo dnf config-manager --set-enabled ol9_developer_EPEL
sudo dnf install -y fail2ban
sudo systemctl enable --now fail2ban
```

Habilitar la jail de SSH:

```bash
sudo tee /etc/fail2ban/jail.local <<'EOF'
[sshd]
enabled = true
EOF

sudo systemctl restart fail2ban
sudo fail2ban-client status sshd
```

> Configuración por defecto: 5 intentos fallidos → ban de 10 minutos.
> Oracle Cloud ya deshabilita la autenticación por contraseña vía `50-cloud-init.conf` — solo funciona la clave privada.

### Gestión de concurrencia

El servidor corre con **1 worker Uvicorn** y gestión de concurrencia vía `asyncio`:

- Las compresiones de imagen se procesan en un `ThreadPoolExecutor` (2 threads) — Pillow no bloquea el event loop.
- Máximo **6 imágenes simultáneas**. Si se supera, el servidor responde `503` con `retry_after_seconds: 5`.
- Los jobs de video se procesan de uno en uno (FFmpeg) con una cola de hasta **5 jobs**. Si la cola está llena, responde `503` con `retry_after_seconds: 60`.
- Al arrancar, el servidor limpia automáticamente archivos temporales de sesiones anteriores.

**Estado del servidor:**
```bash
curl -H "X-API-Key: TU_API_KEY" https://api.tudominio.com/api/v1/status
```
```json
{
  "status": "ok",
  "images_in_flight": 0,
  "images_capacity": 6,
  "video_jobs_queued": 0,
  "video_jobs_processing": 0,
  "video_queue_capacity": 5
}
```

### Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `PROJECT_NAME` | `OptimusApi` | Nombre de la API |
| `API_VERSION` | `1.0.0` | Versión reportada en `/` |
| `DEBUG` | `false` | Activa `/docs`, `/redoc`, `/openapi.json` |
| `API_KEY` | `` | Clave de autenticación para los endpoints protegidos |

> `DEBUG=false` en producción desactiva la documentación automática — no expone la estructura interna de la API.
> `API_KEY` debe ser un string aleatorio y suficientemente largo (recomendado: 32+ caracteres hex).

---

## English

- [Project structure](#project-structure)
- [Endpoints](#endpoints-1)
- [Authentication](#authentication)
- [Scripts](#scripts-1)
- [Local setup (Windows)](#local-setup-windows)
- [Local deploy (Windows)](#local-deploy-windows)
- [VPS deploy](#vps-deploy)
- [Nginx configuration](#6-nginx-reverse-proxy)
- [HTTPS with Cloudflare (subdomain)](#7-https-with-cloudflare-origin-certificate)
- [Security & rate limiting](#9-security--rate-limiting)
- [Concurrency management](#concurrency-management)
- [Environment variables](#environment-variables)

Image and video compression API deployed on Oracle Linux ARM (Ampere A1). Compresses images in-memory without temporary files, supports batches of up to 10 files, and returns the result as a direct file or ZIP. Videos are compressed asynchronously via chunked upload, FFmpeg processing queue, and direct download.

### Project structure

```
vps_optimus_api/
├── app/
│   ├── main.py              # Entry point: FastAPI app + root and guide routes
│   ├── guide.py             # Bilingual HTML guide served at GET /guide
│   ├── core/
│   │   ├── config.py        # Settings via pydantic-settings (.env)
│   │   └── security.py      # verify_api_key dependency (X-API-Key header)
│   ├── api/
│   │   └── v1/
│   │       ├── router.py    # v1 router
│   │       └── media/
│   │           └── router.py  # Image and video compression endpoints
│   └── services/
│       └── image_compressor.py  # In-memory compression logic (Pillow)
├── scripts/
│   ├── linux/
│   │   ├── setup.sh         # One-time VPS setup
│   │   └── deploy.sh        # Pull + package check + service restart
│   └── windows/
│       ├── setup.ps1        # One-time local setup (Windows)
│       └── deploy.ps1       # Pull + package check + local restart
├── requirements.txt
├── optimus-api.service      # systemd service file reference
└── README.md
```

### Endpoints

| Method | Route | Auth | Description |
|---|---|---|---|
| `GET` | `/` | No | API status |
| `GET` | `/guide` | No | Interactive bilingual guide (HTML) |
| `GET` | `/api/v1/status` | Yes | Server status and processing queues |
| `POST` | `/api/v1/media/images/compress` | Yes | Image compression |
| `POST` | `/api/v1/media/videos/upload/init` | Yes | Start a video upload · returns `upload_id` |
| `POST` | `/api/v1/media/videos/upload/chunk` | Yes | Upload one video chunk (≤90 MB) |
| `POST` | `/api/v1/media/videos/upload/finalize` | Yes | Finalize upload and queue compression · returns `job_id` |
| `GET` | `/api/v1/media/videos/status/{job_id}` | Yes | Query compression job status |
| `GET` | `/api/v1/media/videos/download/{job_id}` | Yes | Download compressed video |

**POST `/api/v1/media/images/compress`** — multipart/form-data

| Field | Type | Required | Description |
|---|---|---|---|
| `files` | `File[]` | Yes | Up to 10 images (jpg, png, webp). Max 50 MB/file, 200 MB total |
| `out` | `string` | No | Output format: `jpg`, `webp`, `png` |
| `size` | `int` | No | Max pixel dimension on longest side (1–8000) |

Response: single file → direct `StreamingResponse` · multiple → ZIP.

Response headers:
```
X-Optimus-Status: complete | partial | timeout
X-Optimus-Processed: <int>
X-Optimus-Total: <int>
```

### Authentication

All endpoints under `/api/v1/` require the `X-API-Key` header:

```
X-API-Key: your_api_key
```

The value is set in `.env` as `API_KEY`. Missing or incorrect key returns 401.

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

#### 2. Install FFmpeg and ffprobe (required for video compression)

ARM64 Oracle Linux repositories do not include FFmpeg. Use the static build from [johnvansickle.com](https://johnvansickle.com/ffmpeg/):

```bash
# Download and extract to /tmp
wget -P /tmp https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz
tar xf /tmp/ffmpeg-release-arm64-static.tar.xz -C /tmp

# Copy both binaries to the system
sudo cp /tmp/ffmpeg-*-arm64-static/ffmpeg  /usr/local/bin/ffmpeg
sudo cp /tmp/ffmpeg-*-arm64-static/ffprobe /usr/local/bin/ffprobe
sudo chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe

# Clean up
rm -rf /tmp/ffmpeg-*-arm64-static /tmp/ffmpeg-release-arm64-static.tar.xz

# Verify
ffmpeg -version
ffprobe -version
```

> Version installed in production: **ffmpeg 7.0.2** / **ffprobe 7.0.2** (static ARM64)

#### 3. Clone the project

```bash
cd /srv
git clone <your-repo> optimusapi
cd optimusapi
```

#### 4. One-time setup

```bash
chmod +x scripts/linux/setup.sh scripts/linux/deploy.sh
./scripts/linux/setup.sh
# → creates .venv, installs packages, copies .env
```

#### 5. Configure environment variables

```bash
nano .env
# Make sure DEBUG=false in production
```

#### 6. systemd service

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

#### 7. Nginx reverse proxy

Install and enable:

```bash
sudo dnf install nginx -y
sudo systemctl enable --now nginx
```

Create the site configuration file:

```bash
sudo nano /etc/nginx/conf.d/optimus.conf
```

File contents:

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

Validate and reload:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Open firewall ports:

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

Verify everything responds:

```bash
curl http://127.0.0.1:8000     # direct to gunicorn
curl http://api.yourdomain.com # through nginx
```

#### 8. HTTPS with Cloudflare Origin Certificate

> **Applies when:** the VPS is served from a subdomain (e.g. `api.yourdomain.com`) and the root domain (`yourdomain.com`) already has another app (Vercel, Netlify, etc.) behind Cloudflare's proxy. Changing the zone-wide SSL mode would affect the main domain; this approach enables HTTPS only for the VPS subdomain.

**Why Flexible mode is not enough**

With Cloudflare in **Full (Strict)** mode (recommended), the Cloudflare edge requires the origin server to also speak HTTPS. If the root domain hosts another app, switching the global mode to Flexible would break it. The solution is to install a **Cloudflare Origin Certificate** in nginx — it's free, valid for 15 years, and only works between Cloudflare and your server.

**Step 1 — Generate the certificate in Cloudflare**

1. Cloudflare → your zone → **SSL/TLS** → **Origin Server**
2. Click **Create Certificate**
3. Leave default hostnames (`*.yourdomain.com` and `yourdomain.com`)
4. Validity: **15 years**
5. Click **Create**
6. Copy the **Certificate** and the **Private Key** — they are only shown once

**Step 2 — Save the cert on the VPS**

```bash
sudo mkdir -p /etc/nginx/ssl
sudo nano /etc/nginx/ssl/origin.crt   # paste the Certificate
sudo nano /etc/nginx/ssl/origin.key   # paste the Private Key
sudo chmod 600 /etc/nginx/ssl/origin.key
```

**Step 3 — Update the nginx configuration**

```bash
sudo nano /etc/nginx/conf.d/optimus.conf
```

Replace the contents with:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate     /etc/nginx/ssl/origin.crt;
    ssl_certificate_key /etc/nginx/ssl/origin.key;

    client_max_body_size 200m;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

**Step 4 — Allow nginx network connections in SELinux**

On Oracle Linux with SELinux in `enforcing` mode, nginx needs explicit permission to connect to local processes:

```bash
sudo setsebool -P httpd_can_network_connect 1
```

**Step 5 — Set the SSL mode in Cloudflare**

Cloudflare → SSL/TLS → Overview → switch to **Full (Strict)**

> This does not affect other apps on the root domain as long as they also have valid certificates (Vercel and Netlify include them by default).

**Verify:**

```bash
curl https://api.yourdomain.com
# → {"name":"OptimusApi","version":"1.0.0","status":"ok"}
```

#### 9. Future deploys

```bash
./scripts/linux/deploy.sh
# → git pull → checks packages → restarts the service
```

#### 10. Security & rate limiting

**Request body size limit**

Already included in the `listen 443 ssl` block from step 7 as `client_max_body_size 200m;`. nginx returns 413 before the request reaches the app.

**nginx rate limiting**

Create the zone file (files in `conf.d/` are included inside nginx.conf's `http {}` block):

```bash
sudo tee /etc/nginx/conf.d/rate-limit.conf <<'EOF'
limit_req_zone $http_cf_connecting_ip zone=api:10m rate=5r/s;
EOF
```

Add `limit_req` inside the `location /` block in `optimus.conf`:

```nginx
location / {
    limit_req zone=api burst=20 nodelay;

    proxy_pass         http://127.0.0.1:8000;
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

> `$http_cf_connecting_ip` is used instead of `$binary_remote_addr` because nginx sits behind Cloudflare — that header carries the real user IP. `5r/s` with `burst=20 nodelay` allows short bursts without extra delay, then rejects with 429.

**fail2ban — SSH brute force protection**

Requires enabling the EPEL repository first (Oracle Linux 9):

```bash
sudo dnf config-manager --set-enabled ol9_developer_EPEL
sudo dnf install -y fail2ban
sudo systemctl enable --now fail2ban
```

Enable the SSH jail:

```bash
sudo tee /etc/fail2ban/jail.local <<'EOF'
[sshd]
enabled = true
EOF

sudo systemctl restart fail2ban
sudo fail2ban-client status sshd
```

> Default: 5 failed attempts → 10-minute ban.
> Oracle Cloud already disables password-based SSH authentication via `50-cloud-init.conf` — only the private key works.

### Concurrency management

The server runs with **1 Uvicorn worker** and `asyncio`-based concurrency:

- Image compression runs in a `ThreadPoolExecutor` (2 threads) — Pillow does not block the event loop.
- Maximum **6 simultaneous images**. If exceeded, the server responds `503` with `retry_after_seconds: 5`.
- Video jobs are processed one at a time (FFmpeg) with a queue of up to **5 jobs**. If the queue is full, responds `503` with `retry_after_seconds: 60`.
- On startup, the server automatically cleans up temporary files left from previous sessions.

**Server status:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" https://api.yourdomain.com/api/v1/status
```
```json
{
  "status": "ok",
  "images_in_flight": 0,
  "images_capacity": 6,
  "video_jobs_queued": 0,
  "video_jobs_processing": 0,
  "video_queue_capacity": 5
}
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `PROJECT_NAME` | `OptimusApi` | API name |
| `API_VERSION` | `1.0.0` | Version reported at `/` |
| `DEBUG` | `false` | Enables `/docs`, `/redoc`, `/openapi.json` |
| `API_KEY` | `` | Authentication key for protected endpoints |

> `DEBUG=false` in production disables auto-generated docs — keeps the API structure hidden.
> `API_KEY` should be a random string of sufficient length (recommended: 32+ hex characters).
