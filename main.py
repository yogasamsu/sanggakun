import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

load_dotenv()
# Perhatikan: Kita ganti nama fungsi import agar lebih generik
from services.ai_service import analyze_receipt 
from services.sheet_service import save_data

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! 🤖\nKirim foto **Struk** atau **Buku Tabungan**, saya akan sortat otomatis.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("⏳ Sedang memindai dokumen...")
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        result = analyze_receipt(photo_file.file_path)
        
        if not result:
            await status_msg.edit_text("❌ Gagal membaca gambar.")
            return

        # LOGIKA BALASAN BERDASARKAN TIPE
        if result['jenis_dokumen'] == 'STRUK':
            # Balasan untuk Struk (Sama seperti sebelumnya)
            jurnal_text = ""
            for item in result['jurnal']:
                debit = f"{item['debit']:,}"
                kredit = f"{item['kredit']:,}"
                if item['debit'] > 0: jurnal_text += f"🟢 (Dr) {item['akun']}: {debit}\n"
                else: jurnal_text += f"🔴 (Cr) {item['akun']}: {kredit}\n"

            reply_text = (
                f"🧾 **Struk Terdeteksi**\n"
                f"📅 {result['tanggal']} | 🏪 {result['merchant']}\n"
                f"📝 {result['deskripsi_umum']}\n\n"
                f"{jurnal_text}"
            )
        
        elif result['jenis_dokumen'] == 'MUTASI':
            # Balasan untuk Mutasi
            total_trx = len(result['transaksi'])
            total_uang = sum(item['nominal'] for item in result['transaksi'])
            
            reply_text = (
                f"🏦 **Mutasi Rekening Terdeteksi**\n"
                f"Bank: {result.get('bank', '-')}\n"
                f"Jumlah Baris: {total_trx} transaksi\n"
                f"Total Nilai Terbaca: Rp {total_uang:,}\n\n"
                f"Data akan masuk ke tab 'Mutasi Bank'."
            )
        
        await status_msg.edit_text(reply_text + "\n\n💾 *Menyimpan...*")

        # Simpan ke Sheets
        tipe_simpan = save_data(result)
        
        if tipe_simpan:
            await update.message.reply_text(f"✅ Tersimpan di Sheet: **{tipe_simpan}**")
        else:
            await update.message.reply_text("⚠️ Gagal menyimpan ke Google Sheets.")

    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text(f"Error: {e}")

if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot Sanggabiz V2 (Multi-Doc) berjalan... 🚀")
    application.run_polling()