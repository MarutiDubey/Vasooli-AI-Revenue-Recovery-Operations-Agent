import sqlite3
import os

DB_PATH = "vasooli.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create webhook_events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webhook_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE,
            event_type TEXT,
            subscription_id TEXT,
            payment_id TEXT,
            payload_hash TEXT,
            received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed_at DATETIME,
            event_source TEXT DEFAULT 'RAZORPAY'
        )
    ''')
    try:
        cursor.execute("ALTER TABLE webhook_events ADD COLUMN event_source TEXT DEFAULT 'RAZORPAY'")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE,
            name TEXT,
            email TEXT,
            contact TEXT,
            tenure_days INTEGER,
            opt_out BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE,
            customer_id INTEGER,
            plan_id TEXT,
            amount INTEGER,
            currency TEXT DEFAULT 'INR',
            state TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    # Create recovery_cases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recovery_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id INTEGER,
            customer_id INTEGER,
            amount_at_risk INTEGER,
            status TEXT,
            priority TEXT,
            diagnosis TEXT,
            ai_recommendation TEXT,
            policy_decision TEXT,
            policy_override_reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    # Create recovery_actions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recovery_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER,
            action_type TEXT,
            status TEXT,
            razorpay_resource_id TEXT,
            ai_recommended BOOLEAN,
            policy_approved BOOLEAN,
            reason TEXT,
            requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            executed_at DATETIME,
            FOREIGN KEY (case_id) REFERENCES recovery_cases(id)
        )
    ''')

    # Create promises table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER,
            promised_amount INTEGER,
            promised_date DATE,
            source_text TEXT,
            ai_confidence REAL,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            checked_at DATETIME,
            FOREIGN KEY (case_id) REFERENCES recovery_cases(id)
        )
    ''')

    # Create recovery_outcomes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recovery_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER,
            action_id INTEGER,
            cash_recovered BOOLEAN,
            cash_amount INTEGER,
            subscription_reactivated BOOLEAN,
            razorpay_payment_id TEXT,
            razorpay_invoice_id TEXT,
            exception_reason TEXT,
            verified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES recovery_cases(id),
            FOREIGN KEY (action_id) REFERENCES recovery_actions(id)
        )
    ''')

    conn.commit()
    conn.close()
