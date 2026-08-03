from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Customer, DailyActivity, FollowUp, Lead, Quotation, SalesTeamMember, ServiceTeamMember, ServiceTicket, ShowroomVisit, User, WorkTask, normalize_phone


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("rows", 4)
            field.widget.attrs.setdefault("class", "form-control")


class LeadForm(StyledModelForm):
    next_followup = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"])

    class Meta:
        model = Lead
        fields = ["customer", "customer_name", "phone", "alternate_phone", "email", "city", "pincode", "source", "stage", "rating", "interested_model", "preferred_color", "budget", "assigned_to", "next_followup", "lost_reason", "notes"]


class CustomerForm(StyledModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "email", "address", "city", "vehicle_model", "vehicle_number", "vin", "purchase_date", "notes"]
        widgets = {"purchase_date": forms.DateInput(attrs={"type": "date"})}

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        matches = Customer.objects.filter(phone_key=normalize_phone(phone))
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise forms.ValidationError("A master customer with this phone number already exists.")
        return phone


class FollowUpForm(StyledModelForm):
    due_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"])

    class Meta:
        model = FollowUp
        fields = ["lead", "customer", "title", "kind", "due_at", "status", "assigned_to", "notes"]


class DailyActivityForm(StyledModelForm):
    class Meta:
        model = DailyActivity
        fields = ["activity_date", "activity_type", "title", "customer", "lead", "quotation", "service_ticket", "sales_member", "status", "outcome", "next_followup", "amount"]
        widgets = {
            "activity_date": forms.DateInput(attrs={"type": "date"}),
            "next_followup": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class WorkTaskForm(StyledModelForm):
    class Meta:
        model = WorkTask
        fields = ["title", "description", "assigned_to", "customer", "lead", "due_date", "status", "priority"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}


class SalesTeamMemberForm(StyledModelForm):
    class Meta:
        model = SalesTeamMember
        fields = ["user", "manager", "name", "phone", "email", "role", "is_active", "joined_on", "notes"]
        widgets = {"joined_on": forms.DateInput(attrs={"type": "date"})}


class ShowroomVisitForm(StyledModelForm):
    visit_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"])
    next_followup = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"])

    class Meta:
        model = ShowroomVisit
        fields = ["lead", "customer", "visitor_name", "phone", "visit_at", "purpose", "interested_model", "status", "assigned_to", "outcome", "next_followup"]


class ServiceTeamMemberForm(StyledModelForm):
    class Meta:
        model = ServiceTeamMember
        fields = ["user", "name", "phone", "role", "skills", "is_active", "joined_on", "notes"]
        widgets = {"joined_on": forms.DateInput(attrs={"type": "date"})}


class ServiceTicketForm(StyledModelForm):
    appointment_at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"])
    promised_at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"])
    next_followup = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"])

    class Meta:
        model = ServiceTicket
        fields = ["customer", "service_plan", "vehicle_model", "vehicle_number", "vin", "odometer_km", "complaint", "diagnosis", "work_done", "technician_notes", "priority", "status", "assigned_to", "appointment_at", "promised_at", "estimate_amount", "final_amount", "customer_approved", "pickup_required", "next_followup"]


class QuotationForm(StyledModelForm):
    class Meta:
        model = Quotation
        fields = ["lead", "customer", "customer_name", "customer_phone", "model_name", "ex_showroom", "central_subsidy", "state_subsidy", "rto_registration", "insurance", "accessories", "discount", "valid_until", "status", "notes"]
        widgets = {"valid_until": forms.DateInput(attrs={"type": "date"})}


class StaffCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "designation", "role", "password1", "password2"]
