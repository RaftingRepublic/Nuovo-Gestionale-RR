"""
Database Engine — SQLite via SQLAlchemy.

Usato per l'indice registrazioni (ricerche, lista, ordinamento).
I file PDF/firma/biometrici restano su file system (GDPR: dati minimi nel DB).

NOTA: SQLite con check_same_thread=False è sicuro con FastAPI perché
      ogni request ottiene la propria sessione via Depends(get_db).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Il file .db viene creato nella cartella backend/
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./rafting.db")

engine = create_engine(
    DB_PATH,
    connect_args={"check_same_thread": False},  # Necessario per SQLite + FastAPI
    echo=False,  # Metti True per debug SQL queries
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency injection per FastAPI.
    Apre una sessione DB per la durata della request, poi la chiude.

    Uso:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
