import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# Load environment variables
load_dotenv()
from services.ai_service import analyze_receipt
from services.sheet_service import save_transaction

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo Sanggabiz! 🤖\nKirimkan foto struk/bukti transfer, saya akan buatkan Jurnal Akuntansinya.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    status_msg = await update.message.reply_text("⏳ Sedang menganalisa gambar & menentukan akun...")
    
    try:
        # 1. Ambil File Gambar
        photo_file = await update.message.photo[-1].get_file()
        photo_url = photo_file.file_path
        
        # 2. Kirim ke AI Service
        result = analyze_receipt(photo_url)
        
        if not result:
            await status_msg.edit_text("❌ Gagal membaca gambar. Pastikan foto jelas.")
            return

        # 3. Format Pesan Konfirmasi (Disini tadi Errornya, sekarang sudah diperbaiki)
        # Kita loop data jurnal untuk ditampilkan rapi
        jurnal_text = ""
        for item in result['jurnal']:
            # Format angka dengan pemisah ribuan
            debit_fmt = f"{item['debit']:,}"
            kredit_fmt = f"{item['kredit']:,}"
            
            if item['debit'] > 0:
                jurnal_text += f"🟢 (Dr) {item['akun']}: Rp {debit_fmt}\n"
            elif item['kredit'] > 0:
                jurnal_text += f"🔴 (Cr) {item['akun']}: Rp {kredit_fmt}\n"

        # Perhatikan: Kita pakai 'deskripsi_umum' bukan 'deskripsi'
        confirmation_text = (
            f"✅ **Jurnal Terbentuk!**\n"
            f"📅 Tanggal: {result['tanggal']}\n"
            f"🏪 Merchant: {result['merchant']}\n"
            f"📝 Ket: {result['deskripsi_umum']}\n\n" 
            f"**Entri Akuntansi:**\n"
            f"{jurnal_text}\n"
            f"Sedang memposting ke Buku Besar..."
        )
        await status_msg.edit_text(confirmation_text)

        # 4. Simpan ke Google Sheets
        success = save_transaction(result)
        
        if success:
            await update.message.reply_text("💾 **Data Berhasil Disimpan!**\nCek Google Sheets, header dan jurnal sudah otomatis dibuat.")
        else:
            await update.message.reply_text("⚠️ Gagal menyimpan ke Google Sheets. Cek koneksi.")

    except Exception as e:
        logging.error(f"Error handling photo: {e}")
        # Tampilkan error ke chat agar mudah debug (opsional, tapi membantu)
        await status_msg.edit_text(f"Terjadi kesalahan sistem: {e}")

if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    photo_handler = MessageHandler(filters.PHOTO, handle_photo)
    
    application.add_handler(start_handler)
    application.add_handler(photo_handler)
    
    print("Bot Sanggabiz sedang berjalan... 🚀")
    application.run_polling()