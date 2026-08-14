from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Customer, DailyActivity, FollowUp, Lead, SalesTeamMember, ServicePlan, ServiceTeamMember, ServiceTicket, ServiceUpdate, User, WorkTask


class CoreWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="manager", password="secret", role=User.Roles.ADMIN)
        self.staff = User.objects.create_user(username="staff", password="secret", role=User.Roles.STAFF)
        self.client.login(username="manager", password="secret")

    def test_master_customer_prevents_duplicate_lead_customer_records(self):
        response = self.client.post(reverse("customer-create"), {"name": "Asha Rao", "phone": "+91 9876543210", "email": "asha@example.com"})
        self.assertEqual(response.status_code, 302)
        customer = Customer.objects.get()
        self.client.post(reverse("lead-create"), {"customer_name": "Asha Rao", "phone": "9876543210", "customer": customer.pk, "source": "WHATSAPP", "stage": "NEW", "rating": "HOT", "assigned_to": self.staff.pk})
        self.client.post(reverse("lead-create"), {"customer_name": "Asha Rao", "phone": "+91 9876543210", "source": "PHONE", "stage": "CONTACTED", "rating": "WARM", "assigned_to": self.staff.pk})
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(Lead.objects.count(), 2)
        self.assertEqual(Lead.objects.filter(customer=customer).count(), 2)

    def test_lead_next_followup_creates_reminder(self):
        response = self.client.post(reverse("lead-create"), {"customer_name": "Nikhil Das", "phone": "9123456789", "source": "WHATSAPP", "stage": "NEW", "rating": "HOT", "assigned_to": self.staff.pk, "next_followup": "2026-08-05T10:30"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FollowUp.objects.count(), 1)
        self.assertEqual(FollowUp.objects.first().lead.customer_name, "Nikhil Das")

    def test_dashboard_handles_general_reminder_without_customer(self):
        FollowUp.objects.create(title="General reminder", due_at=timezone.now(), assigned_to=self.admin)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "General")

    def test_service_ticket_is_owned_by_service_team_and_has_timeline(self):
        customer = Customer.objects.create(name="Service Customer", phone="9000000001")
        member = ServiceTeamMember.objects.create(name="Ravi Technician", phone="9000000002")
        plan = ServicePlan.objects.first()
        response = self.client.post(reverse("service-create"), {"customer": customer.pk, "service_plan": plan.pk, "vehicle_model": "Demo EV", "vehicle_number": "KA01AB1234", "odometer_km": 500, "complaint": "Brake inspection", "status": "OPEN", "priority": "NORMAL", "assigned_to": member.pk, "estimate_amount": "0", "final_amount": "0"})
        self.assertEqual(response.status_code, 302)
        ticket = ServiceTicket.objects.get()
        self.assertEqual(ticket.assigned_to, member)
        self.assertEqual(ServiceUpdate.objects.filter(ticket=ticket).count(), 1)

    def test_staff_cannot_open_management_pages(self):
        self.client.login(username="staff", password="secret")
        response = self.client.get(reverse("users"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_quotation_pdf_downloads(self):
        response = self.client.post(reverse("quotation-create"), {"customer_name": "PDF Customer", "customer_phone": "9111111111", "model_name": "City EV", "ex_showroom": "100000", "central_subsidy": "5000", "state_subsidy": "5000", "rto_registration": "1000", "insurance": "5000", "accessories": "2000", "discount": "1000", "status": "DRAFT", "valid_until": "2026-08-31"})
        self.assertEqual(response.status_code, 302)
        quote = __import__("crm.models", fromlist=["Quotation"]).Quotation.objects.get()
        pdf = self.client.get(reverse("quotation-pdf", args=[quote.pk]))
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF-"))
        public_pdf = self.client.get(reverse("quotation-public-pdf", args=[quote.share_token]))
        self.assertEqual(public_pdf.status_code, 200)
        self.assertTrue(public_pdf.content.startswith(b"%PDF-"))

    def test_daily_activity_is_owned_by_sales_member(self):
        customer = Customer.objects.create(name="Daily Customer", phone="9222222222")
        member = SalesTeamMember.objects.create(name="Daily Executive", phone="9333333333", user=self.staff)
        response = self.client.post(reverse("daily-activity-create"), {"activity_date": "2026-08-03", "activity_type": "CALL", "title": "Routine customer call", "customer": customer.pk, "sales_member": member.pk, "status": "COMPLETED", "outcome": "Customer requested a quote", "amount": "0"})
        self.assertEqual(response.status_code, 302)
        activity = DailyActivity.objects.get()
        self.assertEqual(activity.sales_member, member)
        self.assertEqual(activity.customer, customer)

    def test_manager_assigns_task_and_sales_member_completes_it(self):
        member = SalesTeamMember.objects.create(name="Assigned Executive", phone="9444444444", user=self.staff)
        response = self.client.post(reverse("task-create"), {"title": "Call hot leads", "description": "Call the hot leads from today", "assigned_to": member.pk, "due_date": "2026-08-03", "status": "TODO", "priority": "HIGH"})
        self.assertEqual(response.status_code, 302)
        task = WorkTask.objects.get()
        self.client.login(username="staff", password="secret")
        response = self.client.post(reverse("task-complete", args=[task.pk]))
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, WorkTask.Statuses.DONE)
