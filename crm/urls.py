from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("leads/", views.LeadListView.as_view(), name="leads"),
    path("leads/new/", views.LeadCreateView.as_view(), name="lead-create"),
    path("leads/<slug:code>/edit/", views.LeadUpdateView.as_view(), name="lead-edit"),
    path("followups/", views.FollowUpListView.as_view(), name="followups"),
    path("followups/new/", views.FollowUpCreateView.as_view(), name="followup-create"),
    path("followups/<int:pk>/complete/", views.complete_followup, name="followup-complete"),
    path("daily/", views.DailyActivityListView.as_view(), name="daily-activities"),
    path("daily/new/", views.DailyActivityCreateView.as_view(), name="daily-activity-create"),
    path("tasks/", views.WorkTaskListView.as_view(), name="tasks"),
    path("tasks/new/", views.task_create, name="task-create"),
    path("tasks/<int:pk>/complete/", views.complete_task, name="task-complete"),
    path("showroom/", views.ShowroomVisitListView.as_view(), name="showroom"),
    path("showroom/new/", views.ShowroomVisitCreateView.as_view(), name="showroom-create"),
    path("showroom/<int:pk>/edit/", views.ShowroomVisitUpdateView.as_view(), name="showroom-edit"),
    path("customers/", views.customer_list, name="customers"),
    path("customers/new/", views.customer_create, name="customer-create"),
    path("customers/<int:pk>/edit/", views.customer_edit, name="customer-edit"),
    path("services/", views.service_dashboard, name="services"),
    path("services/new/", views.ServiceTicketCreateView.as_view(), name="service-create"),
    path("services/<int:pk>/edit/", views.ServiceTicketUpdateView.as_view(), name="service-edit"),
    path("services/team/", views.team_list, name="team"),
    path("services/team/new/", views.team_create, name="team-create"),
    path("sales-team/", views.sales_team, name="sales-team"),
    path("sales-team/new/", views.sales_team_create, name="sales-team-create"),
    path("quotations/", views.QuotationListView.as_view(), name="quotations"),
    path("quotations/new/", views.QuotationCreateView.as_view(), name="quotation-create"),
    path("quotations/<int:pk>/edit/", views.QuotationUpdateView.as_view(), name="quotation-edit"),
    path("quotations/<int:pk>/pdf/", views.quotation_pdf, name="quotation-pdf"),
    path("quotations/share/<uuid:token>/pdf/", views.quotation_public_pdf, name="quotation-public-pdf"),
    path("users/", views.user_list, name="users"),
    path("users/new/", views.user_create, name="user-create"),
]
