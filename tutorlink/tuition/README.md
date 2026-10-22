# `tuition` app – screens 09, 10, 11

| Screen | URL | Who | View |
|---|---|---|---|
| 09 Create Tuition Post | `/tuition/posts/create/` | Student | `create_post` |
| (My Posts, target of "Back to My Posts") | `/tuition/posts/mine/` | Student | `my_posts` |
| 10 Find Tuition | `/tuition/find/` | Tutor | `find_tuition` |
| 11 Tuition Post Detail | `/tuition/posts/<id>/` | Student / Tutor / Admin | `post_detail` |

## 1. Drop the files into the repo

```
tutorlink/                      <- the folder that has manage.py
├── tuition/                    <- copy this whole folder
└── templates/
    └── tuition/                <- copy this folder (next to templates/accounts)
```

## 2. Register the app (two small edits)

`tutorlink/settings.py`
```python
INSTALLED_APPS = [
    ...,
    "accounts",
    "tuition",          # <- add
]
# make sure templates/ is picked up (probably already there for accounts):
TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]
```

`tutorlink/urls.py`
```python
from django.urls import include, path

urlpatterns = [
    ...,
    path("tuition/", include("tuition.urls")),   # <- add
]
```

## 3. Migrate

```bash
python manage.py migrate
```
The migration (`0001_initial`) is included and depends on `settings.AUTH_USER_MODEL`,
so it works with whatever the accounts app defines.

## 4. How it uses `accounts`

* Imports `role_required` and `get_effective_role` from `accounts.views`, so wrong-role users are redirected to their dashboard with the same message as everywhere else.
* Reads `User.is_verified` – a tutor must be verified (admin panel) before **Apply** works.
* Smart Match uses `User.area / district / division` and `is_verified`; subject, salary, availability and rating are neutral (50%) until the tutor profile has those fields (names probed are listed at the top of `matching.py`).
* Links use the URL name `role_dashboard`.

## 4b. Wire the dashboards (edit the `href="#"` links)

`templates/accounts/dashboards/student_dashboard.html`
* "Post a Tuition Need" (sidebar + hero button) -> `{% url 'tuition:create_post' %}`
* "Applications" can point to `{% url 'tuition:my_posts' %}`

`templates/accounts/dashboards/tutor_dashboard.html`
* "Find Tuition" (sidebar + big button) -> `{% url 'tuition:find_tuition' %}`

## 5. Hooks left for teammates

* **Notifications (17):** `matching.find_matching_tutors(post)` is called on publish; plug your `Notification` model in there.
* **Messages (14) / Report:** the *Message* and *Report* buttons on the detail page and the bell/chat icons in the top bar are `href="#"`.
* **Subjects:** `constants.SUBJECTS` is a plain list until the admin `Subject` model exists.
* **Base layout:** `templates/tuition/base_tuition.html` is self-contained. If the team wants one shared layout, make it extend `accounts/dashboards/base_dashboard.html` instead.

## 6. Tests

```bash
python manage.py test tuition
```
