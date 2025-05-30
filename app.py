from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import json
from datetime import datetime, timedelta
from veritabani import baglanti_kur, tablo_olustur
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'supersecretkey'

tablo_olustur()
DURUM_DOSYASI = 'toplanti_durumu.json'

def oku_durum():
    if not os.path.exists(DURUM_DOSYASI):
        return {"aktif": False, "tarih": None}
    with open(DURUM_DOSYASI, 'r') as f:
        return json.load(f)

def kaydet_durum(aktif, tarih=None):
    with open(DURUM_DOSYASI, 'w') as f:
        json.dump({"aktif": aktif, "tarih": tarih}, f)

def durum_class(durum):
    return {
        'Devam Ediyor': 'devam_ediyor',
        'Tamamlandı': 'tamamlandi',
        'Beklemede': 'beklemede',
        'İptal Edildi': 'iptal_edildi'
    }.get(durum, '')

@app.route('/', methods=['GET', 'POST'])
def index():
    durum = oku_durum()
    bugun = datetime.now().strftime('%Y-%m-%d')

    if request.method == 'POST':
        if not durum['aktif']:
            flash('Toplantı başlatılmadan gündem eklenemez.')
            return redirect(url_for('index'))

        yeni_kayit = (
            datetime.now().strftime('%Y%m%d%H%M%S'),
            durum['tarih'],
            request.form['konu'],
            request.form.get('karar', ''),
            request.form['durum'],
            request.form['termin'],
            request.form.get('eylem', ''),
            request.form['sorumlu']
        )

        conn = baglanti_kur()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO toplantilar (id, tarih, konu, karar, durum, termin, eylem, sorumlu)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', yeni_kayit)
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    filtre_tarih = request.args.get('tarih', '')
    filtre_durum = request.args.get('durum', '')
    filtre_sorumlu = request.args.get('sorumlu', '')

    conn = baglanti_kur()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT tarih FROM toplantilar")
    tarih_listesi = sorted(r[0] for r in cursor.fetchall())

    query = "SELECT * FROM toplantilar"
    filters = []
    params = []
    if filtre_tarih:
        filters.append("tarih = %s")
        params.append(filtre_tarih)
    if filtre_durum:
        filters.append("durum = %s")
        params.append(filtre_durum)
    if filtre_sorumlu:
        filters.append("sorumlu = %s")
        params.append(filtre_sorumlu)
    if filters:
        query += " WHERE " + " AND ".join(filters)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    cursor.execute("SELECT DISTINCT sorumlu FROM toplantilar WHERE sorumlu != ''")
    sorumlular = sorted(s[0] for s in cursor.fetchall())

    sayilar = {
        'devam': sum(1 for r in rows if r[4] == 'Devam Ediyor'),
        'tamam': sum(1 for r in rows if r[4] == 'Tamamlandı'),
        'beklemede': sum(1 for r in rows if r[4] == 'Beklemede'),
        'iptal': sum(1 for r in rows if r[4] == 'İptal Edildi')
    }

    toplam = sum(sayilar.values())
    yarin = (datetime.now() + timedelta(days=1)).date()

    bildirimler = []
    for r in rows:
        try:
            if r[5]:
                termin_date = datetime.strptime(r[5], "%Y-%m-%d").date()
                if termin_date == yarin:
                    bildirimler.append(r)
        except Exception:
            continue

    conn.close()

    data = [{
        'id': r[0],
        'toplanti_tarihi': r[1],
        'konu': r[2],
        'karar': r[3],
        'durum': r[4],
        'durum_class': durum_class(r[4]),
        'termin': r[5],
        'eylem': r[6],
        'sorumlu': r[7]
    } for r in rows]

    return render_template(
        'index.html',
        gundemler=data,
        bugun=bugun,
        toplanti=durum,
        filtre={"tarih": filtre_tarih, "durum": filtre_durum, "sorumlu": filtre_sorumlu},
        sorumlular=sorumlular,
        tarih_listesi=tarih_listesi,
        sayilar=sayilar,
        toplam=toplam,
        bildirimler=bildirimler
    )

@app.route('/export_excel')
def export_excel():
    conn = baglanti_kur()
    df = pd.read_sql_query("SELECT * FROM toplantilar", conn)
    conn.close()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Gündem')
    output.seek(0)
    return send_file(output, download_name="gundem.xlsx", as_attachment=True)

@app.route('/baslat')
def baslat():
    bugun = datetime.now().strftime('%Y-%m-%d')
    kaydet_durum(True, bugun)
    flash("Toplantı başlatıldı.")
    return redirect(url_for('index'))

@app.route('/bitir')
def bitir():
    kaydet_durum(False)
    flash("Toplantı sonlandırıldı.")
    return redirect(url_for('index'))

@app.route('/sil/<id>')
def sil(id):
    conn = baglanti_kur()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM toplantilar WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    flash("Gündem silindi.")
    return redirect(url_for('index'))

@app.route('/duzenle/<id>', methods=['GET', 'POST'])
def duzenle(id):
    conn = baglanti_kur()
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute('''
            UPDATE toplantilar
            SET konu = %s, karar = %s, durum = %s, termin = %s, eylem = %s, sorumlu = %s
            WHERE id = %s
        ''', (
            request.form['konu'],
            request.form['karar'],
            request.form['durum'],
            request.form['termin'],
            request.form['eylem'],
            request.form['sorumlu'],
            id
        ))
        conn.commit()
        conn.close()
        flash("Gündem güncellendi.")
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM toplantilar WHERE id = %s", (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("Kayıt bulunamadı.")
        return redirect(url_for('index'))

    veri = {
        'ID': row[0],
        'Toplantı Tarihi': row[1],
        'Konu': row[2],
        'Karar': row[3],
        'Durum': row[4],
        'Termin': row[5],
        'Eylem Öğeleri': row[6],
        'Sorumlu': row[7]
    }

    return render_template('duzenle.html', veri=veri)

if __name__ == '__main__':
    app.run(debug=True)
