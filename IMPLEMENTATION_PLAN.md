# Showroom Operations CRM and LMS

This project is a Django-based lead and service management system for a small vehicle showroom. The old browser-only IndexedDB and Google Sheets design is being replaced by a shared server application with a master customer catalog and a Neon PostgreSQL database.

## Product Direction

The system must answer one operational question clearly: who is this person, what did we promise them, who owns the next action, and what is the current state of the vehicle or service job?

The application has two access profiles:

| Profile | Responsibility |
| --- | --- |
| Admin / Manager | Full visibility, user management, customer catalog, service team, service plans, reports, quotations, and configuration. |
| CRM manager | Manage the sales team, assign tasks, review daily totals, and work all CRM records. |
| Sales executive / Staff | Create and work leads, daily calls, showroom visits, reminders, quotations, and tasks assigned to them. |
| Service staff | Work service tickets and daily service/problem-resolution records assigned to the workshop. |

Django superusers retain technical admin access. Business admins use the in-app profile role and should not need to edit database records directly.

## Architecture

```text
Customer browser
    |
    | HTTPS, authenticated Django session
    v
Django application on the client server
    |
    | PostgreSQL connection with DATABASE_URL and SSL
    v
Neon PostgreSQL
```

- The website is no longer the database. Browser storage is not the source of truth.
- Neon stores the shared records. The `DATABASE_URL` secret stays on the server.
- Django owns authentication, permissions, forms, business rules, PDF generation, and audit events.
- Google Sheets is not required for daily operation. CSV export can remain as an optional backup/reporting feature.
- Quotations are generated as server-side PDFs and can be downloaded or shared with the customer through WhatsApp from the device.

## Daily Operations Ledger

Daily work is recorded as structured `DailyActivity` records instead of being buried in notes. The record types are:

- Daily call
- Daily booking
- Daily sale
- Daily service completed
- Problem resolved

Each record has the work date, title, customer, optional lead/quotation/service ticket, responsible sales-team member, outcome, amount, and next follow-up. The dashboard summarizes today's calls, bookings, sales, services, and sales value. Managers can filter the full ledger by date and record type; staff see their own records.

This gives management a reliable daily report without requiring a separate spreadsheet. The customer link keeps daily activity attached to the master customer history.

## Sales Team and Manager Tasks

The `SalesTeamMember` register tracks how many people are working in sales/CRM, their role, manager, phone, email, joining date, active status, and optional portal login.

The `WorkTask` queue lets an Admin or CRM Manager assign a dated task to a sales-team member. Tasks can link to a customer or lead and have priority, description, due date, and status. The assigned employee sees their own queue and can mark a task completed; managers see the full team queue.

## Master Customer Catalog

`Customer` is the master entity used across the entire application. It is not recreated in each module.

The catalog stores:

- Name, primary phone, email, address, and city
- Vehicle model, registration number, and VIN
- Purchase date and customer notes
- A stable customer code such as `CUST-20260803-ABC123`
- Links to leads, showroom visits, quotations, follow-ups, and service tickets

Duplicate prevention rules:

1. Phone numbers are normalized to their last ten digits.
2. `phone_key` is unique in the database.
3. Lead, showroom visit, and quotation intake first search the master catalog by phone.
4. If no customer exists, the system creates one master record and links the new activity to it.
5. Staff can search and edit the catalog directly before registering a new person.

Future enhancement: support multiple vehicles per customer with a separate `CustomerVehicle` table. The first release keeps one primary vehicle on the customer profile and records the vehicle snapshot on each service ticket.

## CRM: Lead and Call Management

The lead register handles enquiries received from WhatsApp data, phone calls, website forms, social media, referrals, and walk-ins.

Each lead contains:

- Master customer link
- Contact details captured at the time of enquiry
- Lead source, stage, rating, interested model, color, and budget
- Assigned employee
- Notes, lost reason, created/updated timestamps
- Next follow-up date and time

Lead stages:

`New -> Contacted -> Qualified -> Showroom visit -> Quotation shared -> Booking -> Won/Lost`

When an employee creates a lead with a next-follow-up date, the system creates a reminder queue entry automatically. Staff should never have to keep the next action only in free-text notes.

## Reminders and Follow-ups

The Reminders tab is a single queue for:

- Lead calls
- WhatsApp follow-ups
- Showroom visit follow-ups
- Payment reminders
- Service reminders
- General customer callbacks

Every reminder has a due date/time, owner, status, related customer/lead, notes, and completion timestamp. The dashboard surfaces overdue and due-today items. A future notification job can send email, WhatsApp template, or browser notifications without changing the data model.

## Showroom Visit Management

The Showroom Visits tab tracks people who visit or plan to visit for a new-vehicle enquiry.

Required workflow:

1. Search the master customer catalog by phone.
2. Register a scheduled visit or walk-in arrival.
3. Record the vehicle/model of interest and the assigned sales employee.
4. Mark status as Scheduled, Arrived, Completed, No-show, or Cancelled.
5. Record outcome and create the next follow-up reminder.
6. Link any resulting quotation back to the same customer and lead.

## Service and Repair Management

The Service tab is deliberately separate from sales. Sales staff can create or view a customer service request, but service operations own diagnosis, assignment, repair updates, approval, parts/work notes, and delivery status.

### Service plans

The initial seeded service schedule is editable from Django admin:

| Sequence | Milestone | Price |
| --- | --- | --- |
| 1 | Free Service 1 - 500 km | Free |
| 2 | Free Service 2 - 1,500 km | Free |
| 3 | Free Service 3 - 3,500 km | Free |

The model supports future paid plans, time-based due dates, and plan-specific prices without changing the ticket workflow.

### Service team

Admin/Manager can register and manage:

- Service manager
- Service advisor
- Technician / service boy
- Helper
- Phone, designation, skills, join date, active status, and notes

### Service ticket

Each ticket has a stable number such as `SRV-20260803-ABC123` and contains:

- One master customer
- Vehicle model, registration number, VIN, and odometer
- Service plan or repair/general-service classification
- Customer complaint
- Diagnosis, work completed, and technician notes
- Priority and operational status
- Assigned service-team member
- Appointment and promised delivery times
- Estimate, final amount, customer approval, and pickup requirement
- Next follow-up and closed timestamp

Service statuses:

`Open -> Checked in -> Diagnosis -> Awaiting approval -> Repair in progress -> Ready for delivery -> Delivered`

Every ticket status change creates a `ServiceUpdate` timeline entry. This gives management a repair history without mixing repair responsibility into the sales pipeline.

Next service release should add `ServiceLineItem` for parts, labor, quantities, rates, discounts, taxes, and invoice printing. The current ticket already has estimate/final totals so the workflow is ready for that extension.

## Quotations and WhatsApp

Quotation records are linked to the master customer and optionally the originating lead. They include:

- Vehicle model
- Ex-showroom price
- Central and state subsidy
- RTO/registration
- Insurance
- Accessories
- Dealer discount
- Final on-road total
- Validity date, status, and notes

The PDF endpoint creates a customer-ready downloadable document with the quotation number, customer details, price breakdown, validity, and terms. The next UI step is a WhatsApp action that opens a pre-filled message with the downloadable quotation URL.

## Database Tables

- `User`: Admin/Manager and Staff/Employee profiles
- `SalesTeamMember`: sales and CRM team register with optional portal login and manager
- `Customer`: master customer catalog
- `Lead`: sales enquiry and ownership
- `FollowUp`: reminder queue
- `DailyActivity`: daily calls, bookings, sales, services, and resolved problems
- `WorkTask`: manager-assigned sales/CRM work
- `ShowroomVisit`: visit planning and outcomes
- `ServiceTeamMember`: workshop staff
- `ServicePlan`: free/paid service schedule
- `ServiceTicket`: repair/service job
- `ServiceUpdate`: ticket timeline
- `Quotation`: sales quotation and PDF metadata

## Security and Data Rules

- Use HTTPS on the client domain.
- Keep `DJANGO_SECRET_KEY` and `DATABASE_URL` in server environment variables.
- Never put the Neon connection string in JavaScript, HTML, or the browser.
- Use Django CSRF protection and authenticated sessions.
- Restrict staff querysets to their assigned operational records where appropriate.
- Use database-level uniqueness for customer phone keys and human-readable record codes.
- Add an audit log before production handover for edits, assignments, status changes, and deletions.
- Do not hard-delete customer records in normal operations. Add archive/deactivate behavior instead.

## Scalability Guardrails

- Lead, customer, reminder, daily-activity, task, showroom, service-ticket, and quotation queries have indexes for their normal date, status, owner, and customer filters.
- Large list pages are paginated. The customer catalog currently shows 50 records per page.
- The dashboard uses bounded recent-record previews instead of rendering every record.
- Customer selectors currently use Django model choices. Before the catalog reaches several thousand records, replace those selects with server-side autocomplete search.
- Keep generated quotation PDFs out of the database. The current system generates them on demand; future uploads should use object storage rather than Render's local filesystem or PostgreSQL.

## Capacity and Upgrade Policy

Neon Free currently includes 0.5 GB storage per project and 100 compute-hours per project each month. This CRM stores text and numeric records rather than images, so the stated showroom volume should fit comfortably for years, not days. A rough planning estimate is 5-10 years of normal activity before 0.5 GB becomes a concern, but actual usage must be measured because notes, indexes, and future attachments change the result.

Upgrade based on signals, not a calendar date:

1. Alert at 70 percent database storage, around 350 MB.
2. Plan an upgrade or archive/export at 80 percent, around 400 MB.
3. Upgrade when Neon compute usage repeatedly approaches 100 CU-hours/month.
4. Upgrade when the client needs longer restore history, managed backups, always-on database availability, or stored file attachments.

At the current four-to-five-user scale, keep Render Free and Neon Free for the initial launch, monitor the first month, and upgrade the Render web service first if the wake-up delay becomes annoying. Upgrade Neon when storage, compute, or backup requirements actually justify it.

## Deployment

1. Create a Neon project and database.
2. Configure `DATABASE_URL` with SSL enabled.
3. Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, and `DJANGO_TIME_ZONE`.
4. Run `python manage.py migrate`.
5. Create the first admin with `python manage.py createsuperuser`.
6. Run `python manage.py collectstatic`.
7. Serve Django through the client server's WSGI/ASGI process and proxy the domain over HTTPS.
8. Test login, customer deduplication, reminders, ticket assignment, quotation PDF downloads, and restore/export procedures.

## Verification Checklist

- Two staff members can link the same phone number to one master customer.
- A lead created from WhatsApp creates one customer and one follow-up reminder.
- A showroom visit uses the same customer code as the lead.
- A daily call, booking, sale, service, and resolved-problem record can be filtered by date and owner.
- A CRM manager can assign a task to a sales-team member, and that member can complete it.
- A service ticket cannot be created without a master customer.
- Admin can add a technician and assign a ticket to that technician.
- Ticket status changes produce service timeline records.
- Three free service milestones appear after migration.
- Quotation totals calculate correctly and the PDF downloads with the quotation number.
- Staff cannot access user-management pages.
- Neon credentials are not present in any static asset.

## Next Implementation Phases

### Phase 1: Server foundation - complete

- Django project, custom user roles, migrations, Neon-ready database settings
- Master customer catalog and normalized phone deduplication
- Leads, follow-ups, showroom visits, service tickets, team, quotations
- Daily operations ledger, sales-team register, manager task queue
- Basic role-aware navigation and Django admin

### Phase 2: Operational polish

- Customer search/autocomplete widget in every create form
- Lead-to-customer conversion and customer profile timeline
- Service ticket line items for parts and labor
- WhatsApp message actions and printable service job card
- Dashboard charts and staff workload filters

### Phase 3: Production readiness

- Audit log and archive behavior
- Automated backup/export job
- Email/browser reminder notifications
- Rate limiting, password reset, session timeout, and 2FA review
- Server deployment, domain, HTTPS, error logging, and acceptance testing
