import os
import csv
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# راه‌اندازی لاگ‌ها
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# بارگذاری محصولات از فایل CSV
PRODUCTS = []
CSV_FILE_PATH = os.getenv("CSV_PATH", "products_data.csv")

def load_products():
    global PRODUCTS
    try:
        if os.path.exists(CSV_FILE_PATH):
            with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                PRODUCTS = [row for row in reader]
            logger.info(f"Loaded {len(PRODUCTS)} products from {CSV_FILE_PATH}")
        else:
            logger.warning(f"CSV file not found at {CSV_FILE_PATH}")
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")

load_products()

# دستور شروع (Start)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_message = (
        f"سلام {user_name} عزیز! 🤖✨\n\n"
        "من ربات دیدبان بازار هستم. می‌تونم در پیدا کردن محصولات و بررسی قیمت‌ها کمکت کنم.\n\n"
        "💡 **دستورات من:**\n"
        "• `/products` - مشاهده لیست محصولات\n"
        "• جستجو: کافیه نام یا بخشی از محصول مورد نظرت رو برام بفرستی!"
    )
    await update.message.reply_text(welcome_message)

# دستور نمایش محصولات
async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not PRODUCTS:
        await update.message.reply_text("فعلاً هیچ محصولی در دیتابیس ثبت نشده است.")
        return
    
    response = "📦 **لیست محصولات موجود:**\n\n"
    for idx, p in enumerate(PRODUCTS[:10], 1):
        name = p.get('name', 'نامشخص')
        price = p.get('price', 'نامشخص')
        response += f"{idx}. {name} - قیمت: {price}\n"
    
    await update.message.reply_text(response)

# جستجوی هوشمند در پیام‌ها
async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip().lower()
    if not PRODUCTS:
        await update.message.reply_text("دیتابیس محصولات خالی است.")
        return
    
    matches = [p for p in PRODUCTS if query in p.get('name', '').lower()]
    
    if matches:
        response = f"🔍 نتایج جستجو برای '{query}':\n\n"
        for p in matches[:5]:
            name = p.get('name', 'نامشخص')
            price = p.get('price', 'نامشخص')
            link = p.get('link', '#')
            response += f"🔹 **{name}**\n💰 قیمت: {price}\n🔗 [لینک محصول]({link})\n\n"
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ محصولی با این مشخصات پیدا نکردم. کلمه دیگری را امتحان کنید.")

# سرور بسیار سبک برای پاس کردن سلامت سنجی (Health Check) ها در هاستینگ‌ها
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server running on port {port}")
    server.serve_forever()

# تابع اصلی اجرا
def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN environment variable is missing!")
        return

    # استارت سرور سلامت در ترد جداگانه
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()

    # راه‌اندازی اپلیکیشن تلگرام
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("products", list_products))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_handler))
    
    logger.info("Bot is starting polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
