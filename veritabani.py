import sqlite3

def baglanti_kur():
    return sqlite3.connect('toplanti.db')

def tablo_olustur():
    conn = baglanti_kur()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS toplantilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baslik TEXT NOT NULL,
            tarih TEXT NOT NULL,
            aciklama TEXT
        )
    ''')
    conn.commit()
    conn.close()
