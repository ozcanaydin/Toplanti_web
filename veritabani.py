import psycopg2
import os

def baglanti_kur():
    return psycopg2.connect(
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT")
    )

def tablo_olustur():
    conn = baglanti_kur()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS toplantilar (
            id TEXT PRIMARY KEY,
            tarih TEXT,
            konu TEXT,
            karar TEXT,
            durum TEXT,
            termin TEXT,
            eylem TEXT,
            sorumlu TEXT
        )
    ''')
    conn.commit()
    conn.close()
