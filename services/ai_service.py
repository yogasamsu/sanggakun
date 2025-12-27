import json
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_receipt(image_url: str) -> dict:
    """
    Mendeteksi apakah gambar adalah STRUK (Single Transaksi) atau MUTASI (List Transaksi).
    """
    
    chart_of_accounts = """
    ASET: [Kas Kecil, Bank BCA, Perlengkapan]
    KEWAJIBAN: [Utang Usaha]
    PENDAPATAN: [Pendapatan Jasa]
    BEBAN: [Beban Operasional, Beban Makan/Minum, Beban Transport, Beban Sewa]
    """

    system_prompt = f"""
    Kamu adalah AI Finance Expert. Tugasmu:
    1. Identifikasi jenis dokumen: Apakah "STRUK" (Bukti transaksi tunggal) atau "MUTASI" (Foto buku tabungan/screenshot e-banking dengan banyak baris).
    
    SKENARIO A: Jika dokumen adalah "STRUK":
    Buat jurnal akuntansi double-entry seperti sebelumnya.
    Gunakan akun: {chart_of_accounts}
    
    SKENARIO B: Jika dokumen adalah "MUTASI":
    Ekstrak SEMUA baris transaksi yang terlihat jelas di gambar.
    
    OUTPUT HARUS JSON FORMAT (PILIH SALAH SATU STRUKTUR):
    
    --- Opsi 1 (Jika Struk) ---
    {{
        "jenis_dokumen": "STRUK",
        "tanggal": "YYYY-MM-DD",
        "merchant": "Nama Toko",
        "deskripsi_umum": "Ket Singkat",
        "jurnal": [
             {{"akun": "Debit Account", "debit": 10000, "kredit": 0}},
             {{"akun": "Credit Account", "debit": 0, "kredit": 10000}}
        ]
    }}

    --- Opsi 2 (Jika Mutasi) ---
    {{
        "jenis_dokumen": "MUTASI",
        "bank": "Nama Bank (BCA/Mandiri/dll)",
        "transaksi": [
            {{
                "tanggal": "YYYY-MM-DD",
                "deskripsi": "Uraian transaksi di baris ini",
                "tipe": "CR" (Uang Masuk/Kredit) atau "DB" (Uang Keluar/Debit),
                "nominal": 50000
            }},
            ... (ulangi untuk semua baris yang terbaca)
        ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ],
                }
            ],
            max_tokens=1000, # Naikkan token karena mutasi isinya banyak
        )
        
        content = response.choices[0].message.content.replace("```json", "").replace("```", "")
        return json.loads(content)
        
    except Exception as e:
        print(f"Error AI: {e}")
        return None