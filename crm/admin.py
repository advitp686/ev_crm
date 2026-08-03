from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Customer, DailyActivity, FollowUp, Lead, Quotation, SalesTeamMember, ServicePlan, ServiceTeamMember, ServiceTicket, ServiceUpdate, ShowroomVisit, User, WorkTask


@admin.register(User)
class CrmUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("CRM profile", {"fields": ("role", "phone", "designation")}),)
    list_display = ("username", "first_name", "last_name", "role", "designation", "is_active")
    list_filter = ("role", "is_active")


@admin.register(SalesTeamMember)
class SalesTeamMemberAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "role", "manager", "user", "phone", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("code", "name", "phone", "email")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("code", "customer_name", "phone", "stage", "rating", "assigned_to", "next_followup", "updated_at")
    list_filter = ("stage", "rating", "source")
    search_fields = ("code", "customer_name", "phone", "interested_model")


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "kind", "due_at", "status", "assigned_to")
    list_filter = ("kind", "status")
    search_fields = ("code", "title")


@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = ("code", "activity_date", "activity_type", "title", "sales_member", "status", "amount")
    list_filter = ("activity_date", "activity_type", "status")
    search_fields = ("code", "title", "outcome")


@admin.register(WorkTask)
class WorkTaskAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "assigned_to", "due_date", "priority", "status", "created_by")
    list_filter = ("status", "priority", "due_date")
    search_fields = ("code", "title", "description")


@admin.register(ShowroomVisit)
class ShowroomVisitAdmin(admin.ModelAdmin):
    list_display = ("code", "visitor_name", "phone", "visit_at", "status", "assigned_to")
    list_filter = ("status",)
    search_fields = ("code", "visitor_name", "phone")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "phone", "vehicle_model", "vehicle_number", "vin", "updated_at")
    search_fields = ("code", "name", "phone", "vehicle_number", "vin")


@admin.register(ServiceTeamMember)
class ServiceTeamAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "user", "role", "phone", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("code", "name", "phone")


@admin.register(ServicePlan)
class ServicePlanAdmin(admin.ModelAdmin):
    list_display = ("sequence", "name", "due_km", "is_free", "price", "is_active")
    list_filter = ("is_free", "is_active")


@admin.register(ServiceTicket)
class ServiceTicketAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "service_plan", "status", "priority", "assigned_to", "promised_at")
    list_filter = ("status", "priority", "service_plan")
    search_fields = ("number", "customer__name", "customer__phone", "vehicle_number", "vin")


@admin.register(ServiceUpdate)
class ServiceUpdateAdmin(admin.ModelAdmin):
    list_display = ("ticket", "status", "created_by", "created_at")


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("number", "customer_name", "model_name", "status", "valid_until", "created_at")
    list_filter = ("status",)
    search_fields = ("number", "customer_name", "customer_phone", "model_name")
