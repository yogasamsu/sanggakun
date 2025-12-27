import gspread
import os
from datetime import datetime

gc = gspread.service_account(filename='google_key.json')
SH_ID = os.getenv("SPREADSHEET_ID")

def save_data(data: dict):
    """
    Fungsi Router: Menyimpan ke Sheet Jurnal ATAU Sheet Mutasi.
    """
    try:
        sh = gc.open_by_key(SH_ID)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # === JALUR 1: STRUK (JURNAL UMUM) ===
        if data['jenis_dokumen'] == 'STRUK':
            worksheet = sh.sheet1 
            
            # Auto-Header Jurnal
            if not worksheet.get('A1'): 
                worksheet.append_row(["Tanggal", "No. Bukti", "Deskripsi", "Nama Akun (COA)", "Debit", "Kredit", "Timestamp"])

            no_bukti = f"TRX-{int(datetime.now().timestamp())}"
            rows_to_add = []
            
            for entry in data['jurnal']:
                rows_to_add.append([
                    data['tanggal'],
                    no_bukti,
                    data['merchant'] + " - " + data['deskripsi_umum'],
                    entry['akun'],
                    entry['debit'],
                    entry['kredit'],
                    timestamp
                ])
            
            worksheet.append_rows(rows_to_add)
            return "JURNAL"

        # === JALUR 2: MUTASI BANK ===
        elif data['jenis_dokumen'] == 'MUTASI':
            # Coba cari sheet 'Mutasi Bank', kalau belum ada, buat baru
            try:
                worksheet = sh.worksheet("Mutasi Bank")
            except:
                worksheet = sh.add_worksheet(title="Mutasi Bank", rows="1000", cols="6")
            
            # Auto-Header Mutasi
            if not worksheet.get('A1'):
                worksheet.append_row(["Tanggal", "Bank", "Deskripsi", "Tipe (DB/CR)", "Nominal", "Timestamp"])

            rows_to_add = []
            for item in data['transaksi']:
                rows_to_add.append([
                    item['tanggal'],
                    data.get('bank', 'Unknown'),
                    item['deskripsi'],
                    item['tipe'],
                    item['nominal'],
                    timestamp
                ])
            
            worksheet.append_rows(rows_to_add)
            return "MUTASI"

    except Exception as e:
        print(f"Error Sheets: {e}")
        return False