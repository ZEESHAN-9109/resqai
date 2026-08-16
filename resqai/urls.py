from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

app_pages = [
    ("", "index.html"),
    ("login/", "login.html"),
    ("register/", "register.html"),
    ("dashboard/", "dashboard.html"),
    ("live-situation/", "live-situation.html"),
    ("disaster-map/", "disaster-map.html"),
    ("disaster-details/", "disaster-details.html"),
    ("create-disaster/", "create-disaster.html"),
    ("image-analysis/", "image-analysis.html"),
    ("priority-zones/", "priority-zones.html"),
    ("verification/", "verification.html"),
    ("reports/", "reports.html"),
    ("response-coordination/", "response-coordination.html"),
    ("response-management/", "response-management.html"),
    ("route-planner/", "route-planner.html"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
]

for route, template in app_pages:
    urlpatterns.append(
        path(route, TemplateView.as_view(template_name=template),
             name=template.replace(".html", ""))
    )

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])