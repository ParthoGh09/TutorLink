from datetime import date, datetime

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Application, DemoClass

STAT_ORDER = [
    Application.PENDING,
    Application.SHORTLISTED,
    Application.DEMO_REQUESTED,
    Application.DEMO_SCHEDULED,
    Application.DEMO_COMPLETED,
    Application.ACCEPTED,
]
LABELS = dict(Application.STATUS_CHOICES)

CURRENT_STUDENT = {"name": "Ayesha Rahman", "role": "Student", "initials": "AR"}


def home(_request):
    return redirect("applications")


def applications(request):
    """Screen 12 - Applications (Student)."""
    status = request.GET.get("status", "")
    all_apps = Application.objects.select_related("tutor", "post")
    apps = all_apps.filter(status=status) if status in LABELS else all_apps

    stats = [
        {"key": s, "label": LABELS[s], "count": all_apps.filter(status=s).count()}
        for s in STAT_ORDER
    ]
    first_app = all_apps.first()
    context = {
        "student": CURRENT_STUDENT,
        "apps": apps,
        "stats": stats,
        "active_status": status,
        "total": all_apps.count(),
        "demo_today": DemoClass.objects.filter(date=date.today(), status=DemoClass.SCHEDULED).count(),
        "flow": [(s, LABELS[s]) for s in STAT_ORDER[:5]] + [("accepted", "Accepted / Rejected")],
        "post_title": first_app.post.title if first_app is not None else "",
    }
    return render(request, "tuition/applications.html", context)


@require_POST
def application_action(request, pk, action):
    app = get_object_or_404(Application, pk=pk)
    name = app.tutor.name
    actions = {
        "shortlist": (app.shortlist, f"{name} shortlisted."),
        "request_demo": (app.request_demo, f"Demo requested from {name}."),
        "cancel": (app.cancel, f"Demo with {name} cancelled."),
        "accept": (app.accept, f"{name} accepted. Tuition can start."),
        "reject": (app.reject, f"{name} rejected."),
    }
    if action not in actions:
        messages.error(request, "Unknown action.")
        return redirect("applications")
    func, ok_msg = actions[action]
    if func():
        messages.success(request, ok_msg)
    else:
        messages.error(request, "That action is not available for this application right now.")
    return redirect("applications")


def demo_class(request, pk=None):
    """Screen 13 - Demo Class (Student / Tutor)."""
    demos = DemoClass.objects.select_related("application__tutor", "application__post")
    if pk:
        demo = get_object_or_404(demos, pk=pk)
    else:
        demo = (demos.filter(status=DemoClass.COMPLETED).first()
                or demos.filter(status__in=[DemoClass.SCHEDULED, DemoClass.REQUESTED]).first()
                or demos.first())

    context = {
        "student": CURRENT_STUDENT,
        "demo": demo,
        "demos": demos,
        "completed_count": demos.filter(status__in=[DemoClass.COMPLETED, DemoClass.ACCEPTED]).count(),
        "upcoming_count": demos.filter(status__in=[DemoClass.REQUESTED, DemoClass.SCHEDULED]).count(),
        "timeline": demo.timeline() if demo else [],
        "dev_tools": settings.DEBUG,
    }
    return render(request, "tuition/demo_class.html", context)


@require_POST
def demo_action(request, pk, action):
    demo = get_object_or_404(DemoClass, pk=pk)
    app = demo.application

    if action == "reschedule":
        try:
            new_date = datetime.strptime(request.POST["date"], "%Y-%m-%d").date()
            new_time = datetime.strptime(request.POST["time"], "%H:%M").time()
        except (KeyError, ValueError):
            messages.error(request, "Please choose a valid date and time.")
            return redirect("demo_class", pk=pk)
        demo.schedule_demo(new_date, new_time)
        messages.success(request, "Demo rescheduled.")
    elif action == "cancel":
        if app.cancel():
            messages.success(request, "Demo cancelled.")
        else:
            messages.error(request, "This demo cannot be cancelled now.")
    elif action == "accept":
        if app.accept():
            messages.success(request, f"{app.tutor.name} accepted.")
        else:
            messages.error(request, "Finish the demo before deciding.")
    elif action == "reject":
        if app.reject():
            messages.success(request, f"{app.tutor.name} rejected.")
        else:
            messages.error(request, "Cannot reject now.")
    elif action == "dev_confirm" and settings.DEBUG:
        # Stand-in for the tutor side (not built yet): tutor confirms the time.
        demo.schedule_demo(demo.date, demo.time)
        messages.info(request, "Dev tool: tutor confirmed the demo time.")
    elif action == "dev_complete" and settings.DEBUG:
        demo.status = DemoClass.COMPLETED
        demo.completed_on = date.today()
        demo.save()
        app.status = Application.DEMO_COMPLETED
        app.save()
        messages.info(request, "Dev tool: demo marked as completed.")
    else:
        messages.error(request, "Unknown action.")
    return redirect("demo_class", pk=pk)
