import os
import sqlite3

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, "instance", "cloud_agents.db")
        else:
            self.db_path = db_path

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                user_key TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                base_price REAL NOT NULL,
                trust_score REAL NOT NULL,
                location TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                duration INTEGER NOT NULL,
                bandwidth INTEGER NOT NULL,
                cpu INTEGER NOT NULL,
                ram INTEGER NOT NULL,
                trustworthiness REAL NOT NULL,
                available_slots INTEGER NOT NULL,
                FOREIGN KEY (provider_id) REFERENCES providers(id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                final_price REAL NOT NULL,
                fuzzy_score REAL,
                status TEXT DEFAULT 'confirmed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (service_id) REFERENCES services(id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        self.conn.commit()

    def get_user_by_username(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

    def create_user(self, username, password, email, user_key):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, email, user_key) VALUES (?, ?, ?, ?)",
            (username, password, email, user_key)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_services_by_type(self, service_type):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT services.*, providers.name AS provider_name
            FROM services
            JOIN providers ON services.provider_id = providers.id
            WHERE services.service_type = ?
        """, (service_type,))
        return cursor.fetchall()

    def get_all_services(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT services.*, providers.name AS provider_name
            FROM services
            JOIN providers ON services.provider_id = providers.id
        """)
        return cursor.fetchall()

    def create_contract(self, user_id, service_id, final_price, fuzzy_score):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO contracts (user_id, service_id, final_price, fuzzy_score)
            VALUES (?, ?, ?, ?)
        """, (user_id, service_id, final_price, fuzzy_score))
        self.conn.commit()
        return cursor.lastrowid

    def log(self, agent_type, message):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO agent_logs (agent_type, message) VALUES (?, ?)",
            (agent_type, message)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_logs(self, limit=50):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM agent_logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return cursor.fetchall()

    def reset_logs(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM agent_logs")
        self.conn.commit()

    def close(self):
        self.conn.close()
