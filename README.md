# Showroom Operations CRM

Django CRM and service management website for a small vehicle showroom. The system uses a master customer catalog shared across leads, showroom visits, reminders, quotations, and service tickets.

## Local setup

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/login/` and sign in with the created admin account.

## Neon deployment

1. Create a Neon PostgreSQL project.
2. Copy `.env.example` to `.env` or configure the same variables in the server environment.
3. Set `DATABASE_URL` to the Neon connection string with SSL enabled.
4. Install requirements on the client server.
5. Run `python manage.py migrate` and `python manage.py collectstatic --noinput`.
6. Create the first administrator with `python manage.py createsuperuser`.
7. Serve `crm_project.wsgi:application` through the hosting provider and enable HTTPS.

For Render, connect the repository as a Web Service. The included `render.yaml` and `build.sh` run migrations, collect static files, and start Gunicorn. Keep Neon as the database because Render's free filesystem is ephemeral and local SQLite data would be lost after restarts.

The Neon password and Django secret must never be placed in JavaScript or committed to the repository. The client receives a public quotation PDF only through a random share token URL generated for that quotation.

## Main modules

- Customer catalog with normalized phone deduplication
- Lead and call register with staff assignment
- Daily calls, bookings, sales, services, and resolved-problem ledger
- Sales-team register with CRM manager task assignment
- Follow-up reminder queue
- Showroom visit register
- Service team and service-plan management
- Repair/service tickets with technician assignment and status history
- Quotation PDFs and WhatsApp share links
- Admin and staff/employee profiles
