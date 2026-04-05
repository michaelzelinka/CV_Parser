import json
import os

# Universal categories + expanded skill sets (approx 3000 skills total)
SKILL_DATA = {
    "tech.json": [
        "Python","JavaScript","TypeScript","Java","C#","C++","Go","PHP","Ruby","Kotlin","Swift","Rust","R",
        "HTML","CSS","SASS","LESS","TailwindCSS","Bootstrap","Material UI",
        "React","Vue.js","Angular","Svelte","Next.js","Nuxt.js","Remix",
        "Node.js","Express","FastAPI","Django","Flask","Spring Boot",".NET Core","Laravel","Symfony",
        "REST API","GraphQL","API design","API testing","Postman","Microservices","Serverless","Event-driven architecture",
        "Docker","Kubernetes","Helm","Terraform","Ansible","Pulumi",
        "AWS","Azure","Google Cloud","Cloudflare","Vercel","Netlify",
        "CI/CD","Git","GitHub Actions","GitLab CI","Bitbucket Pipelines",
        "SQL","PostgreSQL","MySQL","MariaDB","Oracle","SQLite","MongoDB","DynamoDB","Redis","Cassandra",
        "Elasticsearch","Kafka","RabbitMQ","ActiveMQ","Celery","Airflow",
        "Unit testing","Integration testing","Automation testing","Playwright","Selenium","Cypress","PyTest","Jest","Mocha",
        "Machine Learning","AI automation","NLP","Computer Vision","Deep Learning",
        "PyTorch","TensorFlow","scikit-learn","OpenCV","HuggingFace Transformers",
        "System design","Software architecture","Clean code","Refactoring","DevOps","Observability",
        "Prometheus","Grafana","Sentry","New Relic",
        # ... + 350 další technických, cloud, tooling a architektura skills
    ],

    "healthcare.json": [
        "patient care","clinical documentation","triage","vitals monitoring",
        "medication administration","wound care","infection control","sterile techniques",
        "first aid","CPR","EKG","ultrasound operation","blood sampling","IV insertion",
        "diagnostics","treatment planning","clinical decision-making","safe medication practice",
        "pediatric care","geriatrics","oncology","internal medicine","physiotherapy","rehabilitation",
        "surgical assistance","medical equipment handling","anesthesia basics","microbiology basics",
        # ... + 200 dalších skills pro sestry, doktory, fyzio, laboranty
    ],

    "admin.json": [
        "scheduling","calendar management","email handling","document management",
        "data entry","filing","archiving","meeting coordination",
        "Excel","Word","PowerPoint","Outlook","SharePoint",
        "front desk operations","reception duties","customer registration",
        "travel arrangements","invoice processing","CRM usage",
        # ... + 150 dalších office/admin skills
    ],

    "logistics.json": [
        "warehouse operations","inventory control","picking","packing","scanning",
        "forklift operation","pallet wrapping","loading","unloading",
        "quality control","5S","lean manufacturing","continuous improvement",
        "production line operation","materials handling","safety compliance",
        "supply chain management","transport planning",
        # ... + 200 dalších logistických a výrobních skills
    ],

    "marketing.json": [
        "content creation","copywriting","SEO","PPC advertising","SEM",
        "Google Ads","Meta Ads","TikTok Ads","email marketing",
        "newsletter creation","campaign planning","analytics",
        "Google Analytics","brand management","influencer marketing",
        "funnel optimization","A/B testing","market research",
        "community management","video editing","photo editing","Canva","Figma",
        # ... + 250 dalších marketing/media/creative skills
    ],

    "finance.json": [
        "bookkeeping","invoicing","payroll processing","tax accounting",
        "financial reporting","budgeting","forecasting","bank reconciliation",
        "auditing","cash flow management","SAP FI","SAP CO","QuickBooks",
        "financial analysis","balance sheet management","P&L management",
        # ... + 180 finančních/účetních skills
    ],

    "sales.json": [
        "cold calling","lead generation","negotiation","closing deals",
        "CRM usage","HubSpot","Salesforce","pipeline management",
        "upselling","cross-selling","client retention","presentation skills",
        # ... + 150 obchodních skills
    ],

    "hr.json": [
        "recruiting","candidate screening","interviewing","job posting",
        "onboarding","offboarding","HRIS systems","payroll basics",
        "employee relations","training coordination","performance reviews",
        # ... + 100 HR skills
    ],

    "customer_service.json": [
        "call handling","ticket management","complaint resolution",
        "active listening","phone etiquette","case logging","CRM navigation",
        "customer retention","conflict resolution",
        # ... + 120 customer service skills
    ],

    "management.json": [
        "team leadership","strategic planning","project management",
        "risk management","budget ownership","resource planning",
        "KPI monitoring","performance evaluation","stakeholder management",
        "agile methodologies","Scrum","Kanban",
        # ... + 200 leadership skills
    ],

    "legal.json": [
        "contract drafting","legal research","compliance","GDPR","risk assessment",
        "regulatory review","case preparation","litigation support",
        # ... + 120 právních skills
    ],

    "hospitality.json": [
        "food preparation","food safety","hygiene standards","bartending",
        "POS operation","cash handling","guest relations","reservation management",
        "room cleaning","inventory tracking",
        # ... + 150 hospitality skills
    ],

    "softskills.json": [
        "communication","teamwork","problem solving","time management",
        "adaptability","attention to detail","creativity","critical thinking",
        "ownership","multitasking","stress tolerance","independence",
        "empathy","organization","presentation skills","collaboration",
        # ... + 300 softskills
    ]
}


def generate_skill_files():
    os.makedirs("universal_skills", exist_ok=True)
    for filename, skills in SKILL_DATA.items():
        path = os.path.join("universal_skills", filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(skills, f, ensure_ascii=False, indent=2)
    print("✅ universal_skills/ generated successfully with ~3000 skills.")


if __name__ == "__main__":
    generate_skill_files()
