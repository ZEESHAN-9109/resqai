from django.urls import path

from . import views

urlpatterns = [
    # auth
    path("auth/register/", views.register),
    path("auth/login/", views.login),
    path("auth/logout/", views.logout),
    path("auth/me/", views.me),
    path("users/", views.responders),

    # dashboard
    path("dashboard/stats/", views.dashboard_stats),

    # disasters
    path("disasters/", views.disasters),
    path("disasters/<int:pk>/", views.disaster_detail),
    path("disasters/<int:pk>/timeline/", views.disaster_timeline),

    # live situation
    path("situations/live/", views.live_situation),

    # image analysis
    path("images/analyses/", views.image_analyses),
    path("images/analyze/", views.analyze_image),

    # verification
    path("verification/queue/", views.verification_queue),
    path("verification/<int:pk>/", views.verify_finding),

    # priority
    path("priority-zones/", views.priority_zones),
    path("priority-zones/<int:pk>/", views.priority_zone_detail),

    # reports
    path("reports/", views.reports),

    # responses
    path("responses/assignments/", views.assignments),
    path("responses/assignments/<int:pk>/", views.assignment_detail),

    # routes
    path("routes/plan/", views.plan_route),

    # live external feeds
    path("live/earthquakes/", views.earthquakes),
    path("live/fires/", views.fires),
    path("system/status/", views.system_status),
]