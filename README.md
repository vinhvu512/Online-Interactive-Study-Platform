# LMS monorepo

This repository is a **multi-service learning platform**: a **Next.js** app (courses, teacher tools, Clerk auth, Prisma/MySQL), a **Django** API (PDF → lecture video pipeline and related endpoints under `/watching/`), and an optional **Chainlit** RAG assistant over generated lecture text files.

Treat the three runtimes as independent processes during development; they communicate over HTTP and shared folders, not a single bundled server.

---

## Architecture

| Service | Technology | Typical URL | Purpose |
|--------|------------|-------------|---------|
| **Frontend** | Next.js 14, Prisma, MySQL | `http://localhost:3000` | UI, course CRUD, uploads (UploadThing), Clerk auth |
| **Backend** | Django 5, SQLite (default) | `http://localhost:8000` | Video generation, media storage, `/watching/` API |
| **Assistant** | Chainlit + LlamaIndex | `http://localhost:8501` | Chat over `media/generated_contents/*.txt` (embedded in the course UI via iframe) |

```mermaid
flowchart LR
  subgraph fe [frontend]
    Next[Next.js]
    Prisma[Prisma / MySQL]
    Next --- Prisma
  end
  subgraph be [repo root]
    Django[Django]
    SQLite[(db.sqlite3)]
    Media[(media/)]
    Django --- SQLite
    Django --- Media
  end
  subgraph cl [learning/]
    Chainlit[Chainlit RAG]
    Chainlit --> Media
  end
  Next -->|HTTP API| Django
  Next -->|iframe| Chainlit
```

---

## Prerequisites

Install on your machine before following the steps below:

- **Node.js 20+** and npm (for `frontend/`)
- **Python 3.11+** (for Django, Chainlit, and the video stack)
- **MySQL 8+** (for Prisma; create an empty database you control)
- **FFmpeg** (required by MoviePy for video encoding; `brew install ffmpeg` on macOS)
- Accounts/keys as needed: **Clerk**, **UploadThing**, **OpenAI** (RAG + slide narration), and optionally **AWS** (S3 uploads from Django—see `learning/views.py`)

---

## Repository layout

| Path | Description |
|------|-------------|
| `config/` | Django project settings, root `urls.py`, WSGI/ASGI (`DJANGO_SETTINGS_MODULE=config.settings`). |
| `learning/` | Django app (`learning`): models, `/watching/` routes, GPT/video pipeline, Chainlit entrypoint (`chatbot.py`). |
| `frontend/` | Next.js application; `schema.prisma` and SQL migrations under `frontend/migrations/`. |
| `media/` | Django `MEDIA_ROOT`: generated videos, `generated_contents/` (RAG text), uploads. |
| `manage.py` | Django CLI entry (run from **repository root**). |

---

## Environment variables

Never commit real secrets. Copy the examples into local files that are already gitignored.

### `frontend/.env`

Create `frontend/.env` with at least:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | MySQL connection string, e.g. `mysql://USER:PASSWORD@localhost:3306/DATABASE_NAME` |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key |
| `CLERK_SECRET_KEY` | Clerk secret |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | e.g. `/sign-in` |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | e.g. `/sign-up` |
| `NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL` | e.g. `/` |
| `NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL` | e.g. `/` |
| `NEXT_PUBLIC_APP_URL` | Base URL of the Next app (e.g. `http://localhost:3000`) for image proxying |
| `NEXT_PUBLIC_CHAINLIT_URL` | Chainlit origin for the iframe (default in code is `http://localhost:8501`) |
| `UPLOADTHING_SECRET`, `UPLOADTHING_APP_ID`, `UPLOADTHING_TOKEN` | UploadThing (file uploads in the UI) |

Regenerate the Prisma client after changing `schema.prisma`:

```bash
cd frontend && npx prisma generate --schema schema.prisma
```

### Django / Chainlit / video pipeline

From the **repository root**, use a `.env` file or export variables in your shell. Common cases:

| Variable | Used by |
|----------|---------|
| `OPENAI_API_KEY` | `learning/gpt_processor.py`, `learning/chatbot.py` |
| `S3_BUCKET_NAME`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | S3 video upload in `learning/views.py` |
| `S3_PUBLIC_BASE_URL` | Optional CDN/public base for video URLs |

`python-dotenv` is loaded in relevant modules; placing `.env` in `learning/` works when processes start with that as the working directory, or set variables globally.

---

## Onboarding: step by step

Complete these once per machine (order matters where noted).

### 1. Clone and Python environment (backend + Chainlit + video)

```bash
cd /path/to/LMS
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Apply Django migrations and create a superuser if you use the admin:

```bash
python manage.py migrate
python manage.py createsuperuser   # optional
```

This uses **SQLite** at the repo root (`db.sqlite3` by default in `config/settings.py`). The file is gitignored; each developer maintains a local database.

### 2. MySQL and Prisma (frontend)

Create a database (example name `nextjs_prisma`):

```sql
CREATE DATABASE nextjs_prisma CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Set `DATABASE_URL` in `frontend/.env` to point at it.

Install JS dependencies and apply existing migrations. Migrations live next to the schema: `frontend/migrations/` (same directory as `schema.prisma`).

```bash
cd frontend
npm install
npx prisma generate --schema schema.prisma
npx prisma migrate deploy --schema schema.prisma
```

For **local schema iteration** (creates a new migration from Prisma schema changes), prefer:

```bash
npx prisma migrate dev --schema schema.prisma
```

Use a dedicated database or backup first; `migrate dev` can reset data depending on options.

### 3. Seed Prisma reference data (categories)

The script `frontend/scripts/seed.ts` upserts **Category** rows (required for sensible course filters in the UI). Run it from `frontend/` with a TS runner:

```bash
cd frontend
npx --yes tsx scripts/seed.ts
```

If you prefer a npm script, add one locally (not required for the repo to function):

```json
"scripts": {
  "db:seed": "tsx scripts/seed.ts"
}
```

### 4. Clerk, UploadThing, and other frontend secrets

Without valid **Clerk** keys, authenticated routes and middleware will fail at runtime. Add the keys from the Clerk dashboard to `frontend/.env`. Configure the same application URLs (sign-in, sign-up, allowed origins) in the Clerk dashboard to match `http://localhost:3000`.

Configure **UploadThing** in their dashboard and mirror the tokens in `frontend/.env`.

### 5. Media directory

Ensure Django can write generated assets:

```bash
mkdir -p media/generated_contents media/generated_videos
```

Django serves `/media/` in `DEBUG` (see `config/urls.py`).

---

## Running the stack (three terminals)

Use **three terminals** from the repository root (or adjust paths consistently).

**Terminal A — Django**

```bash
source .venv/bin/activate
python manage.py runserver
```

Default: `http://127.0.0.1:8000`. API prefix for this app: `http://127.0.0.1:8000/watching/`.

**Terminal B — Next.js**

```bash
cd frontend
npm run dev
```

Default: `http://localhost:3000`.

**Terminal C — Chainlit**

```bash
cd learning
chainlit run chatbot.py --port 8501
```

Default: `http://localhost:8501`. The chatbot reads lecture text from `../media/generated_contents` relative to `learning/`.

CORS and CSRF for `http://localhost:3000` are already allowed in `config/settings.py` for local development.

---

## Scripts reference

| Goal | Command |
|------|---------|
| Frontend dev server | `cd frontend && npm run dev` |
| Frontend production build | `cd frontend && npm run build && npm start` |
| Prisma Client after schema change | `cd frontend && npx prisma generate --schema schema.prisma` |
| Apply committed SQL migrations | `cd frontend && npx prisma migrate deploy --schema schema.prisma` |
| Seed categories | `cd frontend && npx tsx scripts/seed.ts` |
| Django shell / admin | `python manage.py shell` / `python manage.py runserver` then `/admin/` |
| Lint frontend | `cd frontend && npm run lint` |

---

## Troubleshooting

- **Prisma cannot connect** — Verify MySQL is running, `DATABASE_URL` credentials and database name, and that `migrate deploy` completed without errors.
- **Clerk / auth loops** — Check `NEXT_PUBLIC_*` URLs match routes under `frontend/app/(auth)/` and dashboard URLs in the Clerk dashboard.
- **Django `ModuleNotFoundError` (e.g. moviepy, corsheaders)** — Activate `.venv` and run `pip install -r requirements.txt` from the repo root.
- **Chainlit iframe empty** — Confirm Chainlit is listening on the port in `NEXT_PUBLIC_CHAINLIT_URL` and that the browser can reach it (same host or CORS/embed policy).
- **Video upload errors** — Confirm S3-related environment variables and bucket policy; see `learning/views.py` for expected names.
- **RAG answers unrelated to a lecture** — Retrieval is global over `media/generated_contents/` unless you add filtering; see `learning/chatbot.py`.

---

## Historical renames

The Django project package was renamed to `config` and the primary app to `learning` (formerly `tes`). The Next.js app directory is `frontend` (formerly `bk-innovation`). If you restore an **old** SQLite file that still references the `tes` app label in `django_migrations` or `django_content_type`, run the SQL updates described in older internal notes or delete `db.sqlite3` and run `python manage.py migrate` again.

---

## License / security

`config/settings.py` ships with a **development-only** `SECRET_KEY`. Replace it and set `DEBUG=False` before any production deployment. Rotate any key that was ever committed or shared.
