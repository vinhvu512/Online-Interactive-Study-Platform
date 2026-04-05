# LMS monorepo

Learning stack: **Django** (video / context generation), **Next.js** (course UI), **Chainlit** (RAG chat over `media/generated_contents/`).

## Repository layout

| Path | Role |
|------|------|
| `config/` | Django **project** package: `settings.py`, root `urls.py`, `wsgi.py` / `asgi.py`. |
| `learning/` | Django **app**: models, `watching/` API routes, PDF → video pipeline, Chainlit entrypoint. |
| `frontend/` | Next.js app (courses, teacher dashboard, Chainlit iframe). |
| `media/` | `generated_contents/` (lecture text for RAG + pipeline), `generated_videos/`, uploads per `settings.MEDIA_ROOT`. |
| `pdfs/` | Local PDF inputs for development. |
| `learning/.chainlit/` | Chainlit config when you run the chatbot from `learning/`. |
| `learning/storage/` | LlamaIndex vector index (created on chat start; gitignored). |

## Run locally

**Django** (from repo root, venv + `pip install -r requirements.txt`):

```bash
python manage.py runserver
```

**Next.js**:

```bash
cd frontend && npm install && npm run dev
```

**Chainlit** (RAG bot; reads `../media/generated_contents` relative to `learning/`):

```bash
cd learning && chainlit run chatbot.py --port 8501
```

Point the frontend at Chainlit with `NEXT_PUBLIC_CHAINLIT_URL` in `frontend/.env` if needed.

## Renames (maintainers)

- Django project: `lms-proj` → **`config`** (`DJANGO_SETTINGS_MODULE=config.settings`).
- Django app: **`tes`** → **`learning`**.
- Next.js app: **`bk-innovation`** → **`frontend`**.

### After pulling this refactor

- Run Django from repo root: `pip install -r requirements.txt` then `python manage.py migrate` (and recreate `db.sqlite3` if you no longer have a local DB).
- If you keep an **old** SQLite file that still has `django_migrations.app = 'tes'`, run:  
  `UPDATE django_migrations SET app='learning' WHERE app='tes';`  
  and the same for `django_content_type.app_label`, or delete the DB and `migrate` again.
- Chainlit: `cd learning && chainlit run chatbot.py --port 8501`.
