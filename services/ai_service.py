import json
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_receipt(image_url: str) -> dict:
    """
    Analisa gambar dan tentukan jurnal Double-Entry.
    """
    
    # KITA SUPLAI DAFTAR AKUN KE AI
    chart_of_accounts = """
    ASET: [Kas Kecil, Bank BCA, Perlengkapan]
    KEWAJIBAN: [Utang Usaha]
    PENDAPATAN: [Pendapatan Jasa]
    BEBAN: [Beban Operasional, Beban Makan/Minum, Beban Transport, Beban Sewa]
    """

    system_prompt = f"""
    Kamu adalah Akuntan Senior. Tugasmu adalah membuat JURNAL AKUNTANSI (Double Entry) dari gambar struk.
    
    Gunakan Daftar Akun ini (pilih yang paling relevan):
    {chart_of_accounts}
    
    ATURAN PENTING:
    1. Jika struk belanja (Pengeluaran):
       - DEBIT: Akun Beban yang sesuai (atau Perlengkapan).
       - KREDIT: "Kas Kecil" (Kecuali di struk tertulis Transfer/Debit Card, maka gunakan "Bank BCA").
    2. Jika bukti transfer masuk (Pendapatan):
       - DEBIT: "Bank BCA" (atau Kas Kecil).
       - KREDIT: "Pendapatan Jasa".
    
    OUTPUT HARUS JSON FORMAT:
    {{
        "tanggal": "YYYY-MM-DD",
        "merchant": "Nama Toko/Lawan Transaksi",
        "deskripsi_umum": "Ringkasan Transaksi",
        "jurnal": [
            {{"akun": "Nama Akun Debit", "debit": 15000, "kredit": 0}},
            {{"akun": "Nama Akun Kredit", "debit": 0, "kredit": 15000}}
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
            max_tokens=500,
        )
        
        content = response.choices[0].message.content.replace("```json", "").replace("```", "")
        return json.loads(content)
        
    except Exception as e:
        print(f"Error AI: {e}")
        return None