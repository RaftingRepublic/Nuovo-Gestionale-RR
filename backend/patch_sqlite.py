from app.db.database import engine
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

def patch_db():
    print("🛠️ Esecuzione patch SQLite per Allineamento Split-Brain...")
    # Usiamo direttamente l'engine di SQLAlchemy che sa già dove si trova il DB locale
    with engine.begin() as conn:
        print("1. Creazione tabella 'customers' in SQLite...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers (
                id VARCHAR(36) PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        print("2. Aggiunta colonna 'customer_id' a 'orders' in SQLite...")
        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN customer_id VARCHAR(36)"))
            print("✅ Colonna aggiunta con successo.")
        except OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️ La colonna 'customer_id' esiste già. Ignoro e procedo.")
            else:
                print(f"❌ Errore inaspettato: {e}")

if __name__ == "__main__":
    patch_db()
    print("🚀 Patch completata. Il DB locale ora è allineato a Supabase.")