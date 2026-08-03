from datetime import date
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


def record_code(prefix):
    return f"{prefix}-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}"


def normalize_phone(value):
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits


def lead_code():
    return record_code("LEAD")


def customer_code():
    return record_code("CUST")


def reminder_code():
    return record_code("REM")


def visit_code():
    return record_code("VISIT")


def technician_code():
    return record_code("TECH")


def service_code():
    return record_code("SRV")


def quotation_code():
    return record_code("QUO")


def quotation_share_token():
    return uuid4()


def daily_activity_code():
    return record_code("DAY")


def work_task_code():
    return record_code("TASK")


def sales_person_code():
    return record_code("SALESP")


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin / Manager"
        CRM_MANAGER = "CRM_MANAGER", "CRM manager"
        SALES_EXECUTIVE = "SALES_EXECUTIVE", "Sales executive"
        SERVICE_STAFF = "SERVICE_STAFF", "Service staff"
        STAFF = "STAFF", "Staff / Employee"

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.STAFF)
    phone = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=80, blank=True)

    @property
    def is_manager(self):
        return self.is_superuser or self.role in {self.Roles.ADMIN, self.Roles.CRM_MANAGER}


class SalesTeamMember(models.Model):
    class Roles(models.TextChoices):
        MANAGER = "MANAGER", "Sales manager"
        CRM_MANAGER = "CRM_MANAGER", "CRM manager"
        EXECUTIVE = "EXECUTIVE", "Sales executive"
        TELECALLER = "TELECALLER", "Telecaller"
        OTHER = "OTHER", "Other"

    code = models.CharField(max_length=32, unique=True, default=sales_person_code)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="sales_profile")
    manager = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="team_members")
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=15, choices=Roles.choices, default=Roles.EXECUTIVE)
    is_active = models.BooleanField(default=True)
    joined_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["is_active", "name"]
        indexes = [models.Index(fields=["manager", "is_active"])]

    def __str__(self):
        return f"{self.name} - {self.get_role_display()}"


class Lead(models.Model):
    class Stages(models.TextChoices):
        NEW = "NEW", "New"
        CONTACTED = "CONTACTED", "Contacted"
        QUALIFIED = "QUALIFIED", "Qualified"
        VISIT = "VISIT", "Showroom visit"
        QUOTE = "QUOTE", "Quotation shared"
        BOOKING = "BOOKING", "Booking"
        WON = "WON", "Won"
        LOST = "LOST", "Lost"

    class Ratings(models.TextChoices):
        HOT = "HOT", "Hot"
        WARM = "WARM", "Warm"
        COLD = "COLD", "Cold"

    class Sources(models.TextChoices):
        WHATSAPP = "WHATSAPP", "WhatsApp"
        WALK_IN = "WALK_IN", "Walk-in"
        PHONE = "PHONE", "Phone"
        WEBSITE = "WEBSITE", "Website"
        REFERRAL = "REFERRAL", "Referral"
        SOCIAL = "SOCIAL", "Social media"
        OTHER = "OTHER", "Other"

    code = models.CharField(max_length=32, unique=True, default=lead_code)
    customer = models.ForeignKey("Customer", null=True, blank=True, on_delete=models.SET_NULL, related_name="leads")
    customer_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    source = models.CharField(max_length=20, choices=Sources.choices, default=Sources.WHATSAPP)
    stage = models.CharField(max_length=20, choices=Stages.choices, default=Stages.NEW)
    rating = models.CharField(max_length=10, choices=Ratings.choices, default=Ratings.WARM)
    interested_model = models.CharField(max_length=120, blank=True)
    preferred_color = models.CharField(max_length=60, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    next_followup = models.DateTimeField(null=True, blank=True)
    lost_reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_leads")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_leads")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["stage", "next_followup"]),
            models.Index(fields=["assigned_to", "updated_at"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.customer_name}"


class Customer(models.Model):
    code = models.CharField(max_length=32, unique=True, default=customer_code)
    source_lead = models.OneToOneField(Lead, null=True, blank=True, on_delete=models.SET_NULL, related_name="converted_customer")
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    phone_key = models.CharField(max_length=20, unique=True, editable=False)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    vehicle_model = models.CharField(max_length=120, blank=True)
    vehicle_number = models.CharField(max_length=30, blank=True)
    vin = models.CharField(max_length=60, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["updated_at"])]

    def save(self, *args, **kwargs):
        self.phone_key = normalize_phone(self.phone)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.phone})"


class FollowUp(models.Model):
    class Types(models.TextChoices):
        CALL = "CALL", "Call"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        VISIT = "VISIT", "Visit"
        SERVICE = "SERVICE", "Service reminder"
        PAYMENT = "PAYMENT", "Payment"
        OTHER = "OTHER", "Other"

    class Statuses(models.TextChoices):
        OPEN = "OPEN", "Open"
        DONE = "DONE", "Completed"
        MISSED = "MISSED", "Missed"
        CANCELLED = "CANCELLED", "Cancelled"

    code = models.CharField(max_length=32, unique=True, default=reminder_code)
    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.CASCADE, related_name="followups")
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE, related_name="followups")
    title = models.CharField(max_length=180)
    kind = models.CharField(max_length=15, choices=Types.choices, default=Types.CALL)
    due_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Statuses.choices, default=Statuses.OPEN)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="followups")
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["status", "due_at"]
        indexes = [
            models.Index(fields=["status", "due_at"]),
            models.Index(fields=["assigned_to", "status"]),
        ]

    @property
    def is_overdue(self):
        return self.status == self.Statuses.OPEN and self.due_at < timezone.now()

    def __str__(self):
        return f"{self.title} - {self.due_at:%d %b %Y %H:%M}"


class DailyActivity(models.Model):
    class Types(models.TextChoices):
        CALL = "CALL", "Daily call"
        BOOKING = "BOOKING", "Daily booking"
        SALE = "SALE", "Daily sale"
        SERVICE = "SERVICE", "Daily service completed"
        PROBLEM = "PROBLEM", "Problem resolved"

    class Statuses(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        PENDING = "PENDING", "Pending"
        RESOLVED = "RESOLVED", "Resolved"
        CANCELLED = "CANCELLED", "Cancelled"

    code = models.CharField(max_length=32, unique=True, default=daily_activity_code)
    activity_date = models.DateField(default=timezone.localdate)
    activity_type = models.CharField(max_length=12, choices=Types.choices)
    title = models.CharField(max_length=180)
    customer = models.ForeignKey("Customer", null=True, blank=True, on_delete=models.SET_NULL, related_name="daily_activities")
    lead = models.ForeignKey("Lead", null=True, blank=True, on_delete=models.SET_NULL, related_name="daily_activities")
    quotation = models.ForeignKey("Quotation", null=True, blank=True, on_delete=models.SET_NULL, related_name="daily_activities")
    service_ticket = models.ForeignKey("ServiceTicket", null=True, blank=True, on_delete=models.SET_NULL, related_name="daily_activities")
    sales_member = models.ForeignKey(SalesTeamMember, null=True, blank=True, on_delete=models.SET_NULL, related_name="daily_activities")
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="recorded_daily_activities")
    status = models.CharField(max_length=12, choices=Statuses.choices, default=Statuses.COMPLETED)
    outcome = models.TextField(blank=True)
    next_followup = models.DateTimeField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-activity_date", "-created_at"]
        indexes = [
            models.Index(fields=["activity_date", "activity_type"]),
            models.Index(fields=["sales_member", "activity_date"]),
            models.Index(fields=["customer", "activity_date"]),
        ]

    def __str__(self):
        return f"{self.activity_date} - {self.get_activity_type_display()} - {self.title}"


class WorkTask(models.Model):
    class Statuses(models.TextChoices):
        TODO = "TODO", "To do"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        DONE = "DONE", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class Priorities(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    code = models.CharField(max_length=32, unique=True, default=work_task_code)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(SalesTeamMember, on_delete=models.PROTECT, related_name="tasks")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="assigned_tasks")
    customer = models.ForeignKey("Customer", null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks")
    lead = models.ForeignKey("Lead", null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks")
    due_date = models.DateField()
    status = models.CharField(max_length=15, choices=Statuses.choices, default=Statuses.TODO)
    priority = models.CharField(max_length=10, choices=Priorities.choices, default=Priorities.NORMAL)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "due_date", "-created_at"]
        indexes = [
            models.Index(fields=["assigned_to", "status", "due_date"]),
            models.Index(fields=["due_date", "status"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}"


class ShowroomVisit(models.Model):
    class Statuses(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        ARRIVED = "ARRIVED", "Arrived"
        COMPLETED = "COMPLETED", "Completed"
        NO_SHOW = "NO_SHOW", "No show"
        CANCELLED = "CANCELLED", "Cancelled"

    code = models.CharField(max_length=32, unique=True, default=visit_code)
    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.SET_NULL, related_name="showroom_visits")
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="showroom_visits")
    visitor_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    visit_at = models.DateTimeField()
    purpose = models.CharField(max_length=180, default="New vehicle enquiry")
    interested_model = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=12, choices=Statuses.choices, default=Statuses.SCHEDULED)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="showroom_visits")
    outcome = models.TextField(blank=True)
    next_followup = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-visit_at"]
        indexes = [models.Index(fields=["visit_at", "status"]), models.Index(fields=["assigned_to", "visit_at"])]

    def __str__(self):
        return f"{self.code} - {self.visitor_name}"


class ServiceTeamMember(models.Model):
    class Roles(models.TextChoices):
        ADVISOR = "ADVISOR", "Service advisor"
        TECHNICIAN = "TECHNICIAN", "Technician"
        HELPER = "HELPER", "Helper"
        MANAGER = "MANAGER", "Service manager"

    code = models.CharField(max_length=32, unique=True, default=technician_code)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="service_profile")
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=15, choices=Roles.choices, default=Roles.TECHNICIAN)
    skills = models.CharField(max_length=250, blank=True)
    is_active = models.BooleanField(default=True)
    joined_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["is_active", "name"]

    def __str__(self):
        return f"{self.name} - {self.get_role_display()}"


class ServicePlan(models.Model):
    name = models.CharField(max_length=120)
    sequence = models.PositiveSmallIntegerField(default=1)
    due_km = models.PositiveIntegerField(null=True, blank=True)
    due_days = models.PositiveIntegerField(null=True, blank=True)
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["sequence", "due_km"]

    def __str__(self):
        return self.name


class ServiceTicket(models.Model):
    class Statuses(models.TextChoices):
        OPEN = "OPEN", "Open"
        CHECKED_IN = "CHECKED_IN", "Checked in"
        DIAGNOSIS = "DIAGNOSIS", "Diagnosis"
        APPROVAL = "APPROVAL", "Awaiting customer approval"
        IN_PROGRESS = "IN_PROGRESS", "Repair in progress"
        READY = "READY", "Ready for delivery"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    class Priorities(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    number = models.CharField(max_length=32, unique=True, default=service_code)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="service_tickets")
    service_plan = models.ForeignKey(ServicePlan, null=True, blank=True, on_delete=models.SET_NULL, related_name="tickets")
    vehicle_model = models.CharField(max_length=120, blank=True)
    vehicle_number = models.CharField(max_length=30, blank=True)
    vin = models.CharField(max_length=60, blank=True)
    odometer_km = models.PositiveIntegerField(null=True, blank=True)
    complaint = models.TextField()
    diagnosis = models.TextField(blank=True)
    work_done = models.TextField(blank=True)
    technician_notes = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=Priorities.choices, default=Priorities.NORMAL)
    status = models.CharField(max_length=15, choices=Statuses.choices, default=Statuses.OPEN)
    assigned_to = models.ForeignKey(ServiceTeamMember, null=True, blank=True, on_delete=models.SET_NULL, related_name="tickets")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_service_tickets")
    appointment_at = models.DateTimeField(null=True, blank=True)
    promised_at = models.DateTimeField(null=True, blank=True)
    estimate_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    customer_approved = models.BooleanField(default=False)
    pickup_required = models.BooleanField(default=False)
    next_followup = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "updated_at"]),
            models.Index(fields=["customer", "created_at"]),
            models.Index(fields=["assigned_to", "status"]),
        ]

    def __str__(self):
        return f"{self.number} - {self.customer.name}"


class ServiceUpdate(models.Model):
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name="updates")
    status = models.CharField(max_length=15, choices=ServiceTicket.Statuses.choices)
    note = models.TextField()
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Quotation(models.Model):
    class Statuses(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent to customer"
        ACCEPTED = "ACCEPTED", "Accepted"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"

    number = models.CharField(max_length=32, unique=True, default=quotation_code)
    share_token = models.UUIDField(default=quotation_share_token, unique=True, editable=False)
    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.SET_NULL, related_name="quotations")
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="quotations")
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=20, blank=True)
    model_name = models.CharField(max_length=120)
    ex_showroom = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    central_subsidy = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    state_subsidy = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    rto_registration = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    insurance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    accessories = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    valid_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Statuses.choices, default=Statuses.DRAFT)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="quotations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"]), models.Index(fields=["customer", "created_at"])]

    @property
    def total(self):
        return self.ex_showroom - self.central_subsidy - self.state_subsidy + self.rto_registration + self.insurance + self.accessories - self.discount

    def __str__(self):
        return f"{self.number} - {self.customer_name}"
