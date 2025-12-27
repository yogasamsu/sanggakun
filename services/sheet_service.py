import gspread
import os
from datetime import datetime

gc = gspread.service_account(filename='google_key.json')
SH_ID = os.getenv("SPREADSHEET_ID")

def save_transaction(data: dict):
    try:
        sh = gc.open_by_key(SH_ID)
        worksheet = sh.sheet1 
        
        # Cek Header (Update Kolom agar sesuai format Jurnal Umum)
        if not worksheet.get('A1'): 
            header = ["Tanggal", "No. Bukti", "Deskripsi", "Nama Akun (COA)", "Debit", "Kredit", "Timestamp"]
            worksheet.append_row(header)

        # Generate Nomor Bukti Unik (misal pakai Timestamp simpel)
        no_bukti = f"TRX-{int(datetime.now().timestamp())}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # LOOPING: Kita simpan setiap baris jurnal (Debit & Kredit)
        rows_to_add = []
        for entry in data['jurnal']:
            row = [
                data['tanggal'],
                no_bukti,            # ID yang sama untuk 2 baris ini (Pairing)
                data['merchant'] + " - " + data['deskripsi_umum'],
                entry['akun'],       # Ini Akun hasil pilihan AI
                entry['debit'],
                entry['kredit'],
                timestamp
            ]
            rows_to_add.append(row)
        
        # Simpan sekaligus (lebih efisien)
        worksheet.append_rows(rows_to_add)
        return True
    except Exception as e:
        print(f"Error Sheets: {e}")
        return False