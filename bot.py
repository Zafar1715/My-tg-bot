import os
import sqlite3
import pandas as pd

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)

# ================== TOKEN (Render ENV) ==================
TOKEN = os.environ.get("TOKEN")

if not TOKEN:
    raise Exception("TOKEN not found in Environment Variables")

# ================== ADMIN ACCESS ==================
ADMINS = [8676281750]  # 👈 ВСТАВЬ СЮДА СВОЙ ID

def can_access(user_id):
    return user_id in ADMINS

# ================== DATABASE ==================
def init_db():
    conn = sqlite3.connect("nakladnye.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        driver TEXT,
        car_number TEXT,
        tons REAL,
        invoice_number TEXT,
        object_name TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================== STATES ==================
DATE, DRIVER, CAR, TONS, INVOICE, OBJECT = range(6)

# ================== MENU ==================
menu = ReplyKeyboardMarkup([
    ["➕ Добавить", "📊 Отчёт"],
    ["📁 Excel"]
], resize_keyboard=True)

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 🔥 временно показываем ID (можешь убрать потом)
    await update.message.reply_text(f"Your ID: {user_id}")

    if not can_access(user_id):
        await update.message.reply_text("⛔ Нет доступа")
        return

    await update.message.reply_text("🏭 Система накладных активна", reply_markup=menu)

# ================== ADD FLOW ==================
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not can_access(update.effective_user.id):
        return

    await update.message.reply_text("📅 Дата:")
    return DATE

async def date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text
    await update.message.reply_text("👷 Водитель:")
    return DRIVER

async def driver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["driver"] = update.message.text
    await update.message.reply_text("🚗 Машина:")
    return CAR

async def car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["car"] = update.message.text
    await update.message.reply_text("⚖️ Тоннаж:")
    return TONS

async def tons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["tons"] = float(update.message.text)
    except:
        await update.message.reply_text("Введите число")
        return TONS

    await update.message.reply_text("🧾 Накладная:")
    return INVOICE

async def invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["invoice"] = update.message.text
    await update.message.reply_text("🏗 Объект:")
    return OBJECT

async def object_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["object"] = update.message.text

    data = context.user_data

    conn = sqlite3.connect("nakladnye.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO invoices (date, driver, car_number, tons, invoice_number, object_name)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["date"],
        data["driver"],
        data["car"],
        data["tons"],
        data["invoice"],
        data["object"]
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text("✅ Сохранено", reply_markup=menu)
    return ConversationHandler.END

# ================== REPORT ==================
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("nakladnye.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT object_name, SUM(tons)
        FROM invoices
        GROUP BY object_name
    """)

    rows = cursor.fetchall()
    conn.close()

    text = "📊 ОТЧЁТ:\n\n"

    for obj, tons in rows:
        text += f"🏗 {obj}: {tons} тонн\n"

    await update.message.reply_text(text)

# ================== EXCEL ==================
async def excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("nakladnye.db")

    df = pd.read_sql_query("SELECT * FROM invoices", conn)

    file = "report.xlsx"
    df.to_excel(file, index=False)

    conn.close()

    await update.message.reply_document(document=open(file, "rb"))

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Добавить$"), add_start)],
        states={
            DATE: [MessageHandler(filters.TEXT, date)],
            DRIVER: [MessageHandler(filters.TEXT, driver)],
            CAR: [MessageHandler(filters.TEXT, car)],
            TONS: [MessageHandler(filters.TEXT, tons)],
            INVOICE: [MessageHandler(filters.TEXT, invoice)],
            OBJECT: [MessageHandler(filters.TEXT, object_name)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^📊 Отчёт$"), report))
    app.add_handler(MessageHandler(filters.Regex("^📁 Excel$"), excel))

    print("🚛 BOT STARTED")

    app.run_polling()

if __name__ == "__main__":
    main()
