import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database.db import Database

def seed():
    db_file = os.path.join(current_dir, "instance", "cloud_agents.db")
    if os.path.exists(db_file):
        os.remove(db_file)

    db = Database(db_path=db_file)
    cursor = db.conn.cursor()

    providers_data = [
        ("AmazonX Cloud", "IaaS", 5.00, 0.92, "USA"),
        ("GoogleZ Cloud", "SaaS", 3.00, 0.95, "USA"),
        ("AzureY Cloud", "PaaS", 4.00, 0.88, "India"),
        ("CloudNine", "SaaS", 2.50, 0.80, "India"),
        ("TeraHost", "IaaS", 6.00, 0.90, "Germany"),
        ("SmartPaaS", "PaaS", 3.80, 0.83, "UK"),
        ("QuickCloud", "SaaS", 2.00, 0.70, "India"),
        ("BigInfra", "IaaS", 4.50, 0.87, "USA"),
        ("CloudNest", "PaaS", 3.20, 0.82, "Singapore"),
        ("DataForge", "SaaS", 2.80, 0.91, "Japan")
    ]

    provider_id_map = {}
    for name, s_type, base_price, trust_score, location in providers_data:
        cursor.execute("""
            INSERT INTO providers (name, service_type, base_price, trust_score, location)
            VALUES (?, ?, ?, ?, ?)
        """, (name, s_type, base_price, trust_score, location))
        provider_id_map[name] = cursor.lastrowid

    # 20 services: 7 IaaS, 7 SaaS, 6 PaaS (at least 6 each)
    services_data = [
        # IaaS (7 services)
        (provider_id_map["AmazonX Cloud"], "AmazonX Compute Basic", "IaaS", "horizontal", 2.50, 12, 250, 2, 4, 0.92, 25),
        (provider_id_map["AmazonX Cloud"], "AmazonX Compute High-Mem", "IaaS", "vertical", 6.50, 24, 800, 8, 32, 0.94, 10),
        (provider_id_map["AmazonX Cloud"], "AmazonX Storage Cluster", "IaaS", "horizontal", 4.00, 18, 500, 4, 16, 0.91, 15),
        (provider_id_map["TeraHost"], "TeraHost Dedicated Core", "IaaS", "vertical", 7.50, 24, 1000, 16, 64, 0.93, 5),
        (provider_id_map["TeraHost"], "TeraHost Fast Virtual", "IaaS", "horizontal", 5.20, 10, 600, 4, 16, 0.88, 20),
        (provider_id_map["BigInfra"], "BigInfra Elastic Node", "IaaS", "horizontal", 3.80, 8, 350, 4, 8, 0.86, 30),
        (provider_id_map["BigInfra"], "BigInfra Scale Max", "IaaS", "vertical", 5.80, 20, 750, 8, 32, 0.89, 12),

        # SaaS (7 services)
        (provider_id_map["GoogleZ Cloud"], "GoogleZ Email Suite", "SaaS", "horizontal", 2.20, 24, 100, 2, 4, 0.96, 40),
        (provider_id_map["GoogleZ Cloud"], "GoogleZ Analytics Pro", "SaaS", "vertical", 4.50, 12, 300, 4, 8, 0.95, 20),
        (provider_id_map["CloudNine"], "CloudNine Office Suite", "SaaS", "horizontal", 1.80, 24, 150, 2, 4, 0.82, 35),
        (provider_id_map["CloudNine"], "CloudNine CRM Pro", "SaaS", "vertical", 3.10, 16, 200, 4, 8, 0.81, 18),
        (provider_id_map["QuickCloud"], "QuickCloud File Sync", "SaaS", "horizontal", 1.20, 6, 80, 1, 2, 0.72, 50),
        (provider_id_map["QuickCloud"], "QuickCloud Project Desk", "SaaS", "vertical", 2.00, 12, 120, 2, 4, 0.70, 25),
        (provider_id_map["DataForge"], "DataForge AI OCR API", "SaaS", "vertical", 3.50, 8, 400, 4, 8, 0.92, 15),

        # PaaS (6 services)
        (provider_id_map["AzureY Cloud"], "AzureY App Service", "PaaS", "horizontal", 3.60, 12, 400, 4, 8, 0.89, 22),
        (provider_id_map["AzureY Cloud"], "AzureY Container Apps", "PaaS", "vertical", 5.00, 24, 650, 8, 16, 0.90, 14),
        (provider_id_map["SmartPaaS"], "SmartPaaS Microservices Runtime", "PaaS", "horizontal", 3.20, 10, 300, 2, 8, 0.84, 28),
        (provider_id_map["SmartPaaS"], "SmartPaaS ML Pipelines", "PaaS", "vertical", 4.80, 16, 550, 8, 16, 0.85, 10),
        (provider_id_map["CloudNest"], "CloudNest Serverless Stack", "PaaS", "horizontal", 2.90, 8, 250, 2, 4, 0.83, 32),
        (provider_id_map["CloudNest"], "CloudNest Kubernetes Engine", "PaaS", "vertical", 4.20, 20, 500, 6, 16, 0.81, 16)
    ]

    for p_id, name, s_type, cat, price, dur, bw, cpu, ram, trust, slots in services_data:
        cursor.execute("""
            INSERT INTO services (provider_id, name, service_type, category, price, duration, bandwidth, cpu, ram, trustworthiness, available_slots)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (p_id, name, s_type, cat, price, dur, bw, cpu, ram, trust, slots))

    db.conn.commit()

    # 1 test user
    db.create_user(
        username="demo",
        password="demo123",
        email="demo@test.com",
        user_key="KEY-DEMO-001"
    )

    # 3 initial logs
    db.log("SYSTEM", "Database initialized")
    db.log("SYSTEM", "10 providers loaded")
    db.log("SYSTEM", "20 services available")

    # Counts verification
    cursor.execute("SELECT COUNT(*) FROM providers")
    providers_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM services")
    services_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]

    db.close()

    print("✅ Database seeded successfully")
    print(f"Providers: {providers_count}")
    print(f"Services: {services_count}")
    print(f"Users: {users_count}")

if __name__ == "__main__":
    seed()
