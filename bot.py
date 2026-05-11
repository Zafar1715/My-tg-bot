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

# ================== TOKEN ==================
TOKEN = "8658556905:AAEQfrHltU9yCFE2b45jmmHXjB61enYwGvY"

# ================== INIT DB ==================
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        time TEXT
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

# ================== DB FUNCTIONS ==================
def add_invoice(data):
    conn = sqlite3.connect("nakladnye.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO invoices (
            date,
            driver,
            car_number,
            tons,
            invoice_number,
            object_name
        )
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


def get_report():
    conn = sqlite3.connect("nakladnye.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT object_name, SUM(tons)
        FROM invoices
        GROUP BY object_name
    """)

    rows = cursor.fetchall()

    conn.close()
    return rows


def log_action(user_id, action):
    conn = sqlite3.connect("nakladnye.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO logs (user_id, action, time)
        VALUES (?, ?, datetime('now'))
    """, (user_id, action))

    conn.commit()
    conn.close()

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏭 DISPATCH SYSTEM ONLINE",
        reply_markup=menu
    )

# ================== ADD FLOW ==================
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Введите дату:")
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
        await update.message.reply_text("⚠️ Введите число")
        return TONS

    await update.message.reply_text("🧾 Номер накладной:")
    return INVOICE

async def invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["invoice"] = update.message.text
    await update.message.reply_text("🏗 Объект:")
    return OBJECT

async def object_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["object"] = update.message.text

    add_invoice(context.user_data)
    log_action(update.effective_user.id, "ADD INVOICE")

    await update.message.reply_text(
        "✅ Накладная сохранена",
        reply_markup=menu
    )

    return ConversationHandler.END

# ================== REPORT ==================
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_report()

    if not rows:
        await update.message.reply_text("📭 Данных пока нет")
        return

    text = "📊 ОТЧЁТ ПО ОБЪЕКТАМ:\n\n"

    for obj, tons in rows:
        text += f"🏗 {obj}: {tons} тонн\n"

    await update.message.reply_text(text)

# ================== EXCEL ==================
async def excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("nakladnye.db")

    df = pd.read_sql_query(
        "SELECT * FROM invoices",
        conn
    )

    file_name = "report.xlsx"

    df.to_excel(file_name, index=False)

    conn.close()

    await update.message.reply_document(
        document=open(file_name, "rb")
    )

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^➕ Добавить$"),
                add_start
            )
        ],

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

    app.add_handler(
        MessageHandler(
            filters.Regex("^📊 Отчёт$"),
            report
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex("^📁 Excel$"),
            excel
        )
    )

    print("🚛 BOT STARTED")

    app.run_polling()

# ================== START APP ==================
if __name__ == "__main__":
    main()
