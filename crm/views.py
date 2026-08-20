from io import BytesIO
from functools import wraps
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView
from django.core.paginator import Paginator
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .forms import CustomerForm, DailyActivityForm, FollowUpForm, LeadForm, QuotationForm, SalesTeamMemberForm, ServiceTeamMemberForm, ServiceTicketForm, ShowroomVisitForm, StaffCreationForm, WorkTaskForm
from .models import Customer, DailyActivity, FollowUp, Lead, Quotation, SalesTeamMember, ServiceTeamMember, ServicePlan, ServiceTicket, ServiceUpdate, ShowroomVisit, User, WorkTask, normalize_phone


def admin_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_manager:
            messages.error(request, "This area is available to administrators and managers only.")
            return redirect("dashboard")
        return view(request, *args, **kwargs)

    return wrapped


@login_required
def dashboard(request):
    now = timezone.now()
    today = now.date()
    daily_today = DailyActivity.objects.filter(activity_date=today)
    context = {
        "lead_count": Lead.objects.exclude(stage=Lead.Stages.LOST).count(),
        "hot_leads": Lead.objects.filter(rating=Lead.Ratings.HOT).exclude(stage=Lead.Stages.LOST).count(),
        "overdue_count": FollowUp.objects.filter(status=FollowUp.Statuses.OPEN, due_at__lt=now).count(),
        "today_count": FollowUp.objects.filter(status=FollowUp.Statuses.OPEN, due_at__date=now.date()).count(),
        "open_tickets": ServiceTicket.objects.exclude(status__in=[ServiceTicket.Statuses.DELIVERED, ServiceTicket.Statuses.CANCELLED]).count(),
        "visits_today": ShowroomVisit.objects.filter(visit_at__date=now.date()).count(),
        "calls_today": daily_today.filter(activity_type=DailyActivity.Types.CALL).count(),
        "bookings_today": daily_today.filter(activity_type=DailyActivity.Types.BOOKING).count(),
        "sales_today": daily_today.filter(activity_type=DailyActivity.Types.SALE).count(),
        "services_today": daily_today.filter(activity_type=DailyActivity.Types.SERVICE).count(),
        "daily_revenue": daily_today.filter(activity_type=DailyActivity.Types.SALE).aggregate(total=Sum("amount"))["total"] or 0,
        "recent_leads": Lead.objects.select_related("assigned_to")[:8],
        "next_reminders": FollowUp.objects.filter(status=FollowUp.Statuses.OPEN).select_related("lead", "customer").order_by("due_at")[:8],
        "recent_tickets": ServiceTicket.objects.select_related("customer", "assigned_to")[:6],
        "today_activities": daily_today.select_related("customer", "lead", "sales_member").order_by("-created_at")[:8],
        "my_tasks": WorkTask.objects.select_related("assigned_to", "customer").filter(assigned_to__user=request.user, status__in=[WorkTask.Statuses.TODO, WorkTask.Statuses.IN_PROGRESS])[:6],
    }
    return render(request, "dashboard.html", context)


class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = "leads/list.html"
    context_object_name = "leads"
    paginate_by = 25

    def get_queryset(self):
        qs = Lead.objects.select_related("assigned_to")
        query = self.request.GET.get("q", "").strip()
        stage = self.request.GET.get("stage", "")
        if query:
            qs = qs.filter(Q(customer_name__icontains=query) | Q(phone__icontains=query) | Q(code__icontains=query) | Q(interested_model__icontains=query))
        if stage:
            qs = qs.filter(stage=stage)
        return qs


class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "form.html"
    extra_context = {"title": "Create lead", "section": "Lead intake"}

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self._link_master_customer(form.instance)
        if form.instance.next_followup:
            FollowUp.objects.create(lead=form.instance, title=f"Follow up with {form.instance.customer_name}", kind=FollowUp.Types.CALL, due_at=form.instance.next_followup, assigned_to=form.instance.assigned_to or self.request.user)
        messages.success(self.request, "Lead created and follow-up reminder scheduled.")
        return response

    def _link_master_customer(self, lead):
        if lead.customer_id:
            customer = lead.customer
        else:
            customer = Customer.objects.filter(phone_key=normalize_phone(lead.phone)).first()
            if not customer:
                customer = Customer.objects.create(name=lead.customer_name, phone=lead.phone, email=lead.email, city=lead.city, vehicle_model=lead.interested_model, source_lead=lead)
            lead.customer = customer
            lead.save(update_fields=["customer", "updated_at"])
        if customer and customer.source_lead_id is None:
            customer.source_lead = lead
            customer.save(update_fields=["source_lead", "updated_at"])

    def get_success_url(self):
        return "/leads/"


class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "form.html"
    slug_field = "code"
    slug_url_kwarg = "code"
    extra_context = {"title": "Update lead", "section": "Lead intake"}

    def form_valid(self, form):
        response = super().form_valid(form)
        if not form.instance.customer_id:
            customer = Customer.objects.filter(phone_key=normalize_phone(form.instance.phone)).first()
            if not customer:
                customer = Customer.objects.create(name=form.instance.customer_name, phone=form.instance.phone, email=form.instance.email, city=form.instance.city, vehicle_model=form.instance.interested_model)
            form.instance.customer = customer
            form.instance.save(update_fields=["customer", "updated_at"])
        return response

    def get_success_url(self):
        return "/leads/"


class FollowUpListView(LoginRequiredMixin, ListView):
    model = FollowUp
    template_name = "followups/list.html"
    context_object_name = "followups"
    paginate_by = 30

    def get_queryset(self):
        qs = FollowUp.objects.select_related("lead", "customer", "assigned_to")
        if not self.request.user.is_manager:
            qs = qs.filter(assigned_to=self.request.user)
        status = self.request.GET.get("status", "OPEN")
        if status:
            qs = qs.filter(status=status)
        return qs


class DailyActivityListView(LoginRequiredMixin, ListView):
    model = DailyActivity
    template_name = "daily/list.html"
    context_object_name = "activities"
    paginate_by = 40

    def get_queryset(self):
        qs = DailyActivity.objects.select_related("customer", "lead", "sales_member", "recorded_by")
        if not self.request.user.is_manager:
            qs = qs.filter(Q(sales_member__user=self.request.user) | Q(recorded_by=self.request.user)).distinct()
        date_filter = self.request.GET.get("date", "")
        activity_type = self.request.GET.get("type", "")
        if date_filter:
            qs = qs.filter(activity_date=date_filter)
        if activity_type:
            qs = qs.filter(activity_type=activity_type)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context["daily_total"] = qs.count()
        context["daily_revenue"] = qs.filter(activity_type=DailyActivity.Types.SALE).aggregate(total=Sum("amount"))["total"] or 0
        context["activity_types"] = DailyActivity.Types.choices
        return context


class DailyActivityCreateView(LoginRequiredMixin, CreateView):
    model = DailyActivity
    form_class = DailyActivityForm
    template_name = "form.html"
    extra_context = {"title": "Record daily activity", "section": "Daily operations"}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.is_manager:
            form.fields["sales_member"].queryset = SalesTeamMember.objects.filter(user=self.request.user, is_active=True)
        return form

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        if not form.instance.sales_member_id:
            profile = getattr(self.request.user, "sales_profile", None)
            if profile:
                form.instance.sales_member = profile
        response = super().form_valid(form)
        if form.instance.next_followup:
            FollowUp.objects.create(lead=form.instance.lead, customer=form.instance.customer, title=f"Follow up: {form.instance.title}", kind=FollowUp.Types.CALL, due_at=form.instance.next_followup, assigned_to=self.request.user)
        messages.success(self.request, "Daily activity recorded.")
        return response

    def get_success_url(self):
        return "/daily/"


class WorkTaskListView(LoginRequiredMixin, ListView):
    model = WorkTask
    template_name = "tasks/list.html"
    context_object_name = "tasks"
    paginate_by = 40

    def get_queryset(self):
        qs = WorkTask.objects.select_related("assigned_to", "created_by", "customer", "lead")
        if not self.request.user.is_manager:
            qs = qs.filter(assigned_to__user=self.request.user)
        return qs


@admin_required
def task_create(request):
    form = WorkTaskForm(request.POST or None)
    if form.is_valid():
        task = form.save(commit=False)
        task.created_by = request.user
        task.save()
        messages.success(request, "Task assigned to the sales team.")
        return redirect("tasks")
    return render(request, "form.html", {"form": form, "title": "Assign team task", "section": "Manager task queue"})


@login_required
@require_POST
def complete_task(request, pk):
    task = get_object_or_404(WorkTask, pk=pk)
    allowed = request.user.is_manager or task.assigned_to.user_id == request.user.id
    if not allowed:
        messages.error(request, "You can only update tasks assigned to you.")
        return redirect("tasks")
    task.status = WorkTask.Statuses.DONE
    task.completed_at = timezone.now()
    task.save(update_fields=["status", "completed_at", "updated_at"])
    messages.success(request, "Task marked completed.")
    return redirect("tasks")


class FollowUpCreateView(LoginRequiredMixin, CreateView):
    model = FollowUp
    form_class = FollowUpForm
    template_name = "form.html"
    extra_context = {"title": "Create reminder", "section": "Follow-up reminders"}

    def form_valid(self, form):
        if not form.instance.assigned_to:
            form.instance.assigned_to = self.request.user
        messages.success(self.request, "Reminder created.")
        return super().form_valid(form)

    def get_success_url(self):
        return "/followups/"


@require_POST
@login_required
def complete_followup(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)
    followup.status = FollowUp.Statuses.DONE
    followup.completed_at = timezone.now()
    followup.save(update_fields=["status", "completed_at"])
    messages.success(request, "Reminder marked completed.")
    return redirect("followups")


class ShowroomVisitListView(LoginRequiredMixin, ListView):
    model = ShowroomVisit
    template_name = "showroom/list.html"
    context_object_name = "visits"
    paginate_by = 30

    def get_queryset(self):
        qs = ShowroomVisit.objects.select_related("lead", "customer", "assigned_to")
        if not self.request.user.is_manager:
            qs = qs.filter(assigned_to=self.request.user)
        return qs


class ShowroomVisitCreateView(LoginRequiredMixin, CreateView):
    model = ShowroomVisit
    form_class = ShowroomVisitForm
    template_name = "form.html"
    extra_context = {"title": "Register showroom visit", "section": "Showroom visits"}

    def form_valid(self, form):
        if not form.instance.customer_id:
            phone = form.instance.phone
            customer = Customer.objects.filter(phone_key=normalize_phone(phone)).first()
            if not customer:
                customer = Customer.objects.create(name=form.instance.visitor_name, phone=phone, vehicle_model=form.instance.interested_model)
            form.instance.customer = customer
        response = super().form_valid(form)
        if form.instance.next_followup:
            FollowUp.objects.create(lead=form.instance.lead, customer=form.instance.customer, title=f"Visit follow-up: {form.instance.visitor_name}", kind=FollowUp.Types.VISIT, due_at=form.instance.next_followup, assigned_to=form.instance.assigned_to or self.request.user)
        messages.success(self.request, "Showroom visit registered.")
        return response

    def get_success_url(self):
        return "/showroom/"


class ShowroomVisitUpdateView(LoginRequiredMixin, UpdateView):
    model = ShowroomVisit
    form_class = ShowroomVisitForm
    template_name = "form.html"
    extra_context = {"title": "Update showroom visit", "section": "Showroom visits"}

    def get_success_url(self):
        return "/showroom/"


@login_required
def service_dashboard(request):
    if not ServicePlan.objects.exists():
        for sequence, km in enumerate((500, 1500, 3500), start=1):
            ServicePlan.objects.create(name=f"Free Service {sequence} - {km:,} km", sequence=sequence, due_km=km, is_free=True)
    tickets = ServiceTicket.objects.select_related("customer", "assigned_to", "service_plan")
    if not request.user.is_manager:
        tickets = tickets.filter(assigned_to__user=request.user)
    context = {
        "tickets": tickets[:40],
        "team": ServiceTeamMember.objects.all(),
        "plans": ServicePlan.objects.all(),
        "open_count": ServiceTicket.objects.exclude(status__in=[ServiceTicket.Statuses.DELIVERED, ServiceTicket.Statuses.CANCELLED]).count(),
        "ready_count": ServiceTicket.objects.filter(status=ServiceTicket.Statuses.READY).count(),
        "team_count": ServiceTeamMember.objects.filter(is_active=True).count(),
    }
    return render(request, "services/dashboard.html", context)


class ServiceTicketCreateView(LoginRequiredMixin, CreateView):
    model = ServiceTicket
    form_class = ServiceTicketForm
    template_name = "form.html"
    extra_context = {"title": "Create service ticket", "section": "Service management"}

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        ServiceUpdate.objects.create(ticket=form.instance, status=form.instance.status, note="Ticket created", created_by=self.request.user)
        messages.success(self.request, f"Service ticket {form.instance.number} created.")
        return response

    def get_success_url(self):
        return "/services/"


class ServiceTicketUpdateView(LoginRequiredMixin, UpdateView):
    model = ServiceTicket
    form_class = ServiceTicketForm
    template_name = "form.html"
    extra_context = {"title": "Update service ticket", "section": "Service management"}

    def form_valid(self, form):
        response = super().form_valid(form)
        ServiceUpdate.objects.create(ticket=form.instance, status=form.instance.status, note=f"Ticket updated to {form.instance.get_status_display()}", created_by=self.request.user)
        if form.instance.status == ServiceTicket.Statuses.DELIVERED and not form.instance.closed_at:
            form.instance.closed_at = timezone.now()
            form.instance.save(update_fields=["closed_at"])
        return response

    def get_success_url(self):
        return "/services/"


@admin_required
def team_list(request):
    return render(request, "services/team.html", {"team": ServiceTeamMember.objects.all()})


@admin_required
def team_create(request):
    form = ServiceTeamMemberForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Service team member added.")
        return redirect("team")
    return render(request, "form.html", {"form": form, "title": "Add service team member", "section": "Service team"})


@admin_required
def sales_team(request):
    return render(request, "sales_team/list.html", {"team": SalesTeamMember.objects.select_related("user", "manager")})


@admin_required
def sales_team_create(request):
    form = SalesTeamMemberForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Sales team member registered.")
        return redirect("sales-team")
    return render(request, "form.html", {"form": form, "title": "Register sales team member", "section": "Sales team"})


class QuotationListView(LoginRequiredMixin, ListView):
    model = Quotation
    template_name = "quotations/list.html"
    context_object_name = "quotations"
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for quote_record in context["quotations"]:
            public_url = self.request.build_absolute_uri(f"/quotations/share/{quote_record.share_token}/pdf/")
            message = quote(f"Hello {quote_record.customer_name}, your quotation {quote_record.number} for {quote_record.model_name} is ready: {public_url}")
            phone = normalize_phone(quote_record.customer_phone)
            quote_record.whatsapp_url = f"https://wa.me/91{phone}?text={message}" if phone else ""
        return context


class QuotationCreateView(LoginRequiredMixin, CreateView):
    model = Quotation
    form_class = QuotationForm
    template_name = "form.html"
    extra_context = {"title": "Create quotation", "section": "Quotations"}

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if not form.instance.customer_id and form.instance.customer_phone:
            customer = Customer.objects.filter(phone_key=normalize_phone(form.instance.customer_phone)).first()
            if not customer:
                customer = Customer.objects.create(name=form.instance.customer_name, phone=form.instance.customer_phone, vehicle_model=form.instance.model_name)
            form.instance.customer = customer
        messages.success(self.request, "Quotation created. You can download the PDF from the quotation list.")
        return super().form_valid(form)

    def get_success_url(self):
        return "/quotations/"


class QuotationUpdateView(LoginRequiredMixin, UpdateView):
    model = Quotation
    form_class = QuotationForm
    template_name = "form.html"
    extra_context = {"title": "Update quotation", "section": "Quotations"}

    def get_success_url(self):
        return "/quotations/"


@login_required
def quotation_pdf(request, pk):
    quote = get_object_or_404(Quotation, pk=pk)
    response = HttpResponse(build_quotation_pdf(quote), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{quote.number}.pdf"'
    return response


def quotation_public_pdf(request, token):
    quote = get_object_or_404(Quotation, share_token=token)
    response = HttpResponse(build_quotation_pdf(quote), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{quote.number}.pdf"'
    return response


def build_quotation_pdf(quote):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = [Paragraph("VEHICLE QUOTATION", styles["Title"]), Spacer(1, 8), Paragraph(f"Quotation: {quote.number}<br/>Date: {quote.created_at:%d %b %Y}<br/>Valid until: {quote.valid_until or 'Not specified'}", styles["Normal"]), Spacer(1, 12)]
    story.append(Paragraph(f"Customer: {quote.customer_name}<br/>Phone: {quote.customer_phone}<br/>Vehicle: {quote.model_name}", styles["Normal"]))
    story.append(Spacer(1, 14))
    rows = [["Description", "Amount (INR)"], ["Ex-showroom", f"{quote.ex_showroom:,.2f}"], ["Central subsidy", f"- {quote.central_subsidy:,.2f}"], ["State subsidy", f"- {quote.state_subsidy:,.2f}"], ["RTO and registration", f"{quote.rto_registration:,.2f}"], ["Insurance", f"{quote.insurance:,.2f}"], ["Accessories", f"{quote.accessories:,.2f}"], ["Dealer discount", f"- {quote.discount:,.2f}"], ["Final on-road price", f"{quote.total:,.2f}"]]
    table = Table(rows, colWidths=[110 * mm, 55 * mm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324d")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b6c3cf")), ("ALIGN", (1, 1), (-1, -1), "RIGHT"), ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f1f4")), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.extend([table, Spacer(1, 16), Paragraph(quote.notes or "Prices and subsidies are subject to confirmation at the time of booking.", styles["Normal"])])
    doc.build(story)
    quote.pdf_generated_at = timezone.now()
    quote.save(update_fields=["pdf_generated_at"])
    return buffer.getvalue()


@admin_required
def user_list(request):
    return render(request, "users/list.html", {"users": User.objects.order_by("role", "username")})


@admin_required
def user_create(request):
    form = StaffCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "User profile created.")
        return redirect("users")
    return render(request, "form.html", {"form": form, "title": "Create user profile", "section": "User management"})


@login_required
def customer_list(request):
    query = request.GET.get("q", "").strip()
    customers = Customer.objects.all()
    if query:
        customers = customers.filter(Q(name__icontains=query) | Q(phone__icontains=query) | Q(vehicle_number__icontains=query) | Q(vin__icontains=query))
    paginator = Paginator(customers, 50)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "customers/list.html", {"customers": page_obj.object_list, "page_obj": page_obj, "is_paginated": page_obj.has_other_pages()})


@login_required
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        if Customer.objects.filter(phone_key=normalize_phone(form.cleaned_data["phone"])).exists():
            form.add_error("phone", "A customer with this phone number already exists. Search the catalog and use that record.")
        else:
            form.save()
            messages.success(request, "Customer added to the master catalog.")
            return redirect("customers")
    return render(request, "form.html", {"form": form, "title": "Register master customer", "section": "Customer catalog"})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        messages.success(request, "Master customer updated.")
        return redirect("customers")
    return render(request, "form.html", {"form": form, "title": "Update master customer", "section": "Customer catalog"})
