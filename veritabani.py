import psycopg2
import os

def baglanti_kur():
    return psycopg2.connect(
        dbname=os.environ.get("DB_toplanti"),
        user=os.environ.get("DB_ozcan_takip"),
        password=os.environ.get("DB_OJBllqlj9Djesddf83NiqPSHT1RXBeNW"),
        host=os.environ.get("DB_dpg-d0rbvj15pdvs73drjspg-a"),
        port="5432"
    )

def tablo_olustur():
    conn = baglanti_kur()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS toplantilar (
            id SERIAL PRIMARY KEY,
            baslik TEXT NOT NULL,
            tarih TEXT NOT NULL,
            aciklama TEXT
        )
    ''')
    conn.commit()
    conn.close()
    
