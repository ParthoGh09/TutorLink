# TutorLink – Applications & Demo Class (Django)

Screens built from the UI Design Document: **12 – Applications** and **13 – Demo Class**.

## Run locally (Windows)
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations tuition
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```
Open http://127.0.0.1:8000/

## Structure
- `tuition/models.py` – Tutor, TuitionPost, Application (accept/reject/cancel), DemoClass (schedule_demo)
- `tuition/views.py`, `tuition/urls.py` – page logic
- `templates/` – HTML, `static/css/style.css` – design (Navy / Coral / Mint, Lora + Poppins)
