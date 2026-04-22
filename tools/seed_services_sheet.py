#!/usr/bin/env python3
"""
seed_services_sheet.py — Write all services from the PDF into the Google Sheet.

Sheet: formattion.ai — Services (1rmRmTsiK-IAraRzRWFmTBr_Mq0HxvNGL14cP7PgFTBc)
Tab:   Services

Usage:
    python tools/seed_services_sheet.py
"""

import os, sys, json
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# ── Auth ──────────────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CREDS_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../workflows/news engine/credentials.json")
)
TOKEN_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../workflows/news engine/token.json")
)

SHEET_ID  = "14q9e1REewluhPTY-p3p8mHKWA-ArfIXOpmWGfoR_Gdo"
TAB_NAME  = "Services"

# ── Data ──────────────────────────────────────────────────────────────────────

HEADERS = [
    "slug", "number", "card_eyebrow", "card_title", "card_desc",
    "page_intro",
    "item1_title", "item1_desc", "item1_tag1", "item1_tag2",
    "item2_title", "item2_desc", "item2_tag1", "item2_tag2",
    "item3_title", "item3_desc", "item3_tag1", "item3_tag2",
    "callout_text", "image_prompt",
]

PIPE = " | "  # separator for bullet lists within a cell

SERVICES = [
    {
        "slug":         "health-safety",
        "number":       "01",
        "card_eyebrow": "Health & Safety",
        "card_title":   "Health & Safety Management System",
        "card_desc":    "Stay compliant without the paperwork burden",
        "page_intro":   "We automate your health & safety processes to keep you compliant, reduce risk, and remove the constant burden of paperwork.",
        "item1_title":  "What this system does",
        "item1_desc":   PIPE.join([
            "Generates RAMS tailored to each project and main contractor requirements",
            "Distributes toolbox talks (TBTs), briefings, and safety documents to site teams",
            "Collects and stores signed documents digitally",
            "Tracks compliance across multiple sites and projects",
            "Ensures the right documents are in place before work starts",
        ]),
        "item1_tag1":   "RAMS generation",
        "item1_tag2":   "Digital distribution",
        "item2_title":  "Additional capabilities",
        "item2_desc":   PIPE.join([
            "Adapts documentation to different main contractor formats and standards",
            "Sends automatic reminders for TBTs, briefings, and required actions",
            "Tracks completion and acknowledgement of safety documents",
            "Logs inspections such as HAVS and PUWER checks",
            "Provides a clear audit trail for compliance and reporting",
        ]),
        "item2_tag1":   "Multi-contractor",
        "item2_tag2":   "Auto reminders",
        "item3_title":  "Typical deliverables",
        "item3_desc":   PIPE.join([
            "Automated RAMS generation workflows",
            "Digital TBT and site briefing distribution system",
            "HAVS, PUWER, and inspection logging workflows",
            "Compliance tracking dashboard",
            "Centralised H&S document management system",
            "Main contractor-specific document formatting",
        ]),
        "item3_tag1":   "RAMS workflows",
        "item3_tag2":   "Compliance dashboard",
        "callout_text": "We replace your Health and Safety Manager with reduced risk, consistent compliance, and no more chasing paperwork across sites.",
        "image_prompt": "Construction site safety inspection, UK subcontractor reviewing RAMS documents, hard hat, high-vis, professional, natural light",
    },
    {
        "slug":         "social-media-marketing",
        "number":       "02",
        "card_eyebrow": "Marketing",
        "card_title":   "Social Media & Marketing System",
        "card_desc":    "Stay visible and generate enquiries without managing social yourself",
        "page_intro":   "We help you stay visible, look professional, and generate consistent enquiries — without needing to manage social media yourself.",
        "item1_title":  "What this system does",
        "item1_desc":   PIPE.join([
            "Captures project updates, site progress, and completed work",
            "Automatically turns this into content across your social platforms",
            "Schedules and publishes posts consistently",
            "Captures enquiries generated from social media",
            "Routes leads directly into your CRM for follow-up",
        ]),
        "item1_tag1":   "Content creation",
        "item1_tag2":   "Auto scheduling",
        "item2_title":  "Additional capabilities",
        "item2_desc":   PIPE.join([
            "Reuses content across multiple platforms (LinkedIn, Facebook, etc.)",
            "Highlights completed projects to build credibility with main contractors",
            "Tracks which content generates enquiries and engagement",
            "Supports employer branding and recruitment visibility",
            "Maintains a consistent online presence without manual effort",
        ]),
        "item2_tag1":   "Multi-platform",
        "item2_tag2":   "Engagement tracking",
        "item3_title":  "Typical deliverables",
        "item3_desc":   PIPE.join([
            "Automated content creation and posting workflows",
            "Social media scheduling system",
            "Enquiry capture and routing integration",
            "Content library of projects and case studies",
            "Basic performance and engagement tracking",
        ]),
        "item3_tag1":   "Content workflows",
        "item3_tag2":   "Enquiry capture",
        "callout_text": "We replace your social media manager with a consistent, professional presence that builds trust and generates opportunities — without the time commitment.",
        "image_prompt": "UK construction subcontractor completed project photography, professional site work, modern building exterior, clean finish",
    },
    {
        "slug":         "lead-generation-crm",
        "number":       "03",
        "card_eyebrow": "Lead Generation",
        "card_title":   "Lead Generation & CRM System",
        "card_desc":    "Win more work with every enquiry captured and followed up properly",
        "page_intro":   "We help you win more work by ensuring every enquiry is captured, tracked, and followed up properly — without relying on memory or manual admin.",
        "item1_title":  "What this system does",
        "item1_desc":   PIPE.join([
            "Captures enquiries from your website, email, and social channels automatically",
            "Logs every lead into a central CRM with full visibility",
            "Tracks each opportunity from enquiry through to quote and job won",
            "Sends automated follow-ups so no lead is ever missed",
            "Reminds you when action is needed on active opportunities",
        ]),
        "item1_tag1":   "Lead capture",
        "item1_tag2":   "Auto follow-up",
        "item2_title":  "Additional capabilities",
        "item2_desc":   PIPE.join([
            "Pre-qualifies leads to focus on the right work",
            "Tracks where your best enquiries are coming from",
            "Monitors conversion rates and pipeline value",
            "Supports estimating and quote follow-up workflows",
            "Provides a clear view of upcoming work and workload",
        ]),
        "item2_tag1":   "Pre-qualification",
        "item2_tag2":   "Pipeline tracking",
        "item3_title":  "Typical deliverables",
        "item3_desc":   PIPE.join([
            "Lead capture forms and integrations",
            "CRM setup with pipeline stages tailored to your business",
            "Automated follow-up and reminder workflows",
            "Opportunity tracking dashboard",
            "Reporting on enquiries, conversions, and pipeline value",
        ]),
        "item3_tag1":   "CRM setup",
        "item3_tag2":   "Pipeline dashboard",
        "callout_text": "We replace your business development manager with more enquiries converted into work, a clearer pipeline, and no missed opportunities.",
        "image_prompt": "Construction business pipeline dashboard on laptop, UK subcontractor office, professional desk, natural light",
    },
    {
        "slug":         "personal-assistant",
        "number":       "04",
        "card_eyebrow": "Operations",
        "card_title":   "Personal Assistant & Digital Receptionist",
        "card_desc":    "An always-on assistant that manages your admin and communications",
        "page_intro":   "We provide an intelligent, always-on assistant that manages your day-to-day admin, communication, and organisation — allowing you to focus on running the business.",
        "item1_title":  "What this system does",
        "item1_desc":   PIPE.join([
            "Responds to common enquiries across email, web, and messaging channels",
            "Handles incoming calls, captures key information, and routes enquiries",
            "Reviews emails and drafts responses for approval",
            "Routes emails and tasks to the correct person automatically",
            "Logs and organises all incoming requests and communications",
            "Assists with calendar scheduling, reminders, and meeting coordination",
            "Creates documents such as quotes, reports, and internal communications",
        ]),
        "item1_tag1":   "Email management",
        "item1_tag2":   "Call handling",
        "item2_title":  "Additional capabilities",
        "item2_desc":   PIPE.join([
            "Follows up on outstanding tasks and conversations automatically",
            "Summarises emails, meetings, and key updates",
            "Tracks actions and ensures nothing is missed",
            "Prepares daily or weekly briefings for directors",
            "Monitors key business metrics and flags issues early",
            "Assists with internal task management and delegation",
        ]),
        "item2_tag1":   "Task tracking",
        "item2_tag2":   "Director briefings",
        "item3_title":  "Typical deliverables",
        "item3_desc":   PIPE.join([
            "AI-driven email and communication management system",
            "Call handling and enquiry capture workflows",
            "Calendar and scheduling automation",
            "Task tracking and follow-up system",
            "Business insights dashboard",
            "Document generation workflows",
        ]),
        "item3_tag1":   "AI comms",
        "item3_tag2":   "Scheduling automation",
        "callout_text": "We replace your assistant with less interruption, better organisation, and significantly more time to focus on high-value work.",
        "image_prompt": "UK construction director at clean office desk, organised workspace, laptop with dashboard, professional natural light",
    },
    {
        "slug":         "hr-internal-comms",
        "number":       "05",
        "card_eyebrow": "Human Resources",
        "card_title":   "HR & Internal Communications System",
        "card_desc":    "Manage your team, training, and communications without the admin",
        "page_intro":   "We streamline how your team is managed, trained, and communicated with — ensuring consistency across your workforce and reducing admin.",
        "item1_title":  "What this system does",
        "item1_desc":   PIPE.join([
            "Manages onboarding for new staff and subcontractors",
            "Tracks training, certifications, and expiry dates (e.g. CSCS, plant tickets)",
            "Schedules and records PDRs (Performance & Development Reviews)",
            "Handles holiday requests, absences, and approvals",
            "Distributes company updates, policies, and key communications",
            "Maintains centralised digital staff records",
            "Logs incidents, issues, and internal reports",
            "Standardises internal processes and documentation",
        ]),
        "item1_tag1":   "Onboarding",
        "item1_tag2":   "Cert tracking",
        "item2_title":  "Additional capabilities",
        "item2_desc":   PIPE.join([
            "Sends automatic reminders for expiring qualifications and required training",
            "Ensures all staff receive and acknowledge key communications",
            "Tracks performance, attendance, and development over time",
            "Supports compliance with workforce and site requirements",
            "Provides visibility of workforce status across projects",
        ]),
        "item2_tag1":   "Auto reminders",
        "item2_tag2":   "Workforce visibility",
        "item3_title":  "Typical deliverables",
        "item3_desc":   PIPE.join([
            "Digital onboarding and induction workflows",
            "Training and certification tracking system",
            "PDR and performance tracking workflows",
            "Leave and absence management system",
            "Internal communications and acknowledgement tracking",
            "Centralised staff database and records system",
        ]),
        "item3_tag1":   "Digital onboarding",
        "item3_tag2":   "Staff database",
        "callout_text": "We replace your HR manager with a more organised, compliant, and accountable workforce with fewer communication gaps.",
        "image_prompt": "UK construction workers site induction, CSCS cards, professional team briefing, high-vis vests, natural outdoor light",
    },
    {
        "slug":         "ongoing-support",
        "number":       "06",
        "card_eyebrow": "Retainer",
        "card_title":   "Ongoing Support & Optimisation",
        "card_desc":    "Your systems monitored, improved, and adapted as your business grows",
        "page_intro":   "Your monthly retainer ensures your systems continue to run smoothly, improve over time, and adapt as your business grows.",
        "item1_title":  "What your retainer includes",
        "item1_desc":   PIPE.join([
            "Ongoing system monitoring and maintenance",
            "Continuous improvements and refinements to workflows",
            "Adjustments as your business processes evolve",
            "Support and troubleshooting when needed",
            "Performance tracking and optimisation",
        ]),
        "item1_tag1":   "Monitoring",
        "item1_tag2":   "Optimisation",
        "item2_title":  "Systems that improve over time",
        "item2_desc":   PIPE.join([
            "Adapt to how your projects and workflows actually operate",
            "Improve accuracy in handling tasks like document creation, communication, and data processing",
            "Become more aligned with your preferences, standards, and decision-making",
            "Reduce the need for manual input over time",
        ]),
        "item2_tag1":   "Self-improving",
        "item2_tag2":   "Less manual input",
        "item3_title":  "Why this matters",
        "item3_desc":   PIPE.join([
            "Your business changes — your systems change with it",
            "Issues are caught and resolved before they affect your operations",
            "Workflows are continuously refined based on real usage",
            "You have a dedicated point of contact for support and improvements",
            "Your investment compounds in value the longer systems are in place",
        ]),
        "item3_tag1":   "Continuous value",
        "item3_tag2":   "Dedicated support",
        "callout_text": "Systems that don't just work — they get better, more efficient, and more valuable the longer they are in place.",
        "image_prompt": "UK construction business analytics dashboard, performance charts, professional office setting, modern clean workspace",
    },
    {
        "slug":         "branding-identity",
        "number":       "07",
        "card_eyebrow": "Branding",
        "card_title":   "Branding & Identity Package",
        "card_desc":    "A complete brand system that makes your business look credible and consistent",
        "page_intro":   "Most subcontractors have a logo — but no consistent brand behind it. We create a complete branding system that ensures your business looks professional, consistent, and credible across every touchpoint.",
        "item1_title":  "What this includes",
        "item1_desc":   PIPE.join([
            "Logo refinement or redesign",
            "Full brand guidelines document",
            "Colour palette and typography selection",
            "Logo variations (primary, secondary, icons)",
            "High-quality logo files for all uses",
        ]),
        "item1_tag1":   "Logo design",
        "item1_tag2":   "Brand guidelines",
        "item2_title":  "Where this is applied",
        "item2_desc":   PIPE.join([
            "Workwear and PPE branding",
            "Vehicle graphics and signage",
            "Site boards and hoarding",
            "Quotes, invoices, and documentation",
            "Email signatures and communications",
            "Social media and marketing",
            "Website design and layout",
            "Tender submissions and presentations",
        ]),
        "item2_tag1":   "Physical branding",
        "item2_tag2":   "Digital branding",
        "item3_title":  "Additional capabilities",
        "item3_desc":   PIPE.join([
            "Branded document templates (RAMS, quotes, reports)",
            "Consistent formatting across all business outputs",
            "Guidance for suppliers (printers, signwriters, etc.)",
        ]),
        "item3_tag1":   "Document templates",
        "item3_tag2":   "Supplier guidance",
        "callout_text": "A professional, consistent brand that builds trust with main contractors and clients.",
        "image_prompt": "UK construction company professional branding, branded high-vis workwear, site signage, clean modern identity",
    },
    {
        "slug":         "website-design-build",
        "number":       "08",
        "card_eyebrow": "Website",
        "card_title":   "Website Design & Build",
        "card_desc":    "A professional website that reflects your work and wins enquiries",
        "page_intro":   "Your website should reflect the quality of your work and support your business in winning new opportunities. We design and build modern, professional websites tailored to subcontractors in construction.",
        "item1_title":  "What this includes",
        "item1_desc":   PIPE.join([
            "Fully designed, on-brand website",
            "Mobile-friendly and responsive layout",
            "Clear structure focused on your services and projects",
            "Contact and enquiry capture forms",
            "Integration with your Lead & CRM system",
        ]),
        "item1_tag1":   "Responsive design",
        "item1_tag2":   "CRM integration",
        "item2_title":  "Additional capabilities",
        "item2_desc":   PIPE.join([
            "Project portfolio and case study pages",
            "SEO-ready structure and content",
            "Fast, secure hosting setup",
            "Domain connection and management",
            "Ongoing updates and improvements",
        ]),
        "item2_tag1":   "SEO-ready",
        "item2_tag2":   "Portfolio pages",
        "item3_title":  "Ongoing support (optional)",
        "item3_desc":   PIPE.join([
            "Website hosting and maintenance",
            "Content updates and improvements",
            "Performance monitoring and optimisation",
        ]),
        "item3_tag1":   "Hosting",
        "item3_tag2":   "Maintenance",
        "callout_text": "A professional online presence that builds credibility and generates enquiries.",
        "image_prompt": "Modern UK construction company website on laptop screen, professional subcontractor, clean minimal design, office setting",
    },
]

# ── Main ──────────────────────────────────────────────────────────────────────

def get_creds():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        else:
            print("ERROR: No valid token found. Run the news engine auth flow first.")
            sys.exit(1)
    return creds


def main():
    print("Authenticating with Google ...")
    creds = get_creds()

    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)

    try:
        ws = sh.worksheet(TAB_NAME)
        print(f"  Found tab: {TAB_NAME}")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=TAB_NAME, rows=50, cols=len(HEADERS))
        print(f"  Created tab: {TAB_NAME}")

    rows = [HEADERS]
    for s in SERVICES:
        row = [s.get(h, "") for h in HEADERS]
        rows.append(row)

    ws.clear()
    ws.update("A1", rows)
    print(f"  Written {len(SERVICES)} services + header row")
    print(f"\nDone. Open: https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == "__main__":
    main()
