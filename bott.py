from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters

TOKEN = '7675958058:AAHZlWpWRvKVpASt0Tt73g4rZSXAbjDicls'
SECRET_KEY = 'MATH270'

# Adminlar va boshqa ma'lumotlarni saqlash
authorized_admins = set()
questions = {}
user_scores = {}
user_states = {}  # Foydalanuvchi holatini boshqarish uchun

# Start function for regular users
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [KeyboardButton("Savol kodi yuborish")],
        [KeyboardButton("Reytingni ko‘rish")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Salom! Tanlovni tanlang.", reply_markup=reply_markup)

# Adminni tasdiqlash va admin menyusiga o'tish
async def authorize(update: Update, context: CallbackContext) -> None:
    if context.args and context.args[0] == SECRET_KEY:
        authorized_admins.add(update.message.chat_id)
        await update.message.reply_text("Siz admin sifatida tasdiqlandingiz!")
        await admin_menu(update, context)
    else:
        await update.message.reply_text("Noto‘g‘ri maxfiy kalit. Iltimos, qaytadan urinib ko‘ring.")

# Admin menyusi
async def admin_menu(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id in authorized_admins:
        keyboard = [
            [KeyboardButton("Savol qo‘shish")],
            [KeyboardButton("Javob qo‘shish")],
            [KeyboardButton("Reytingni reset qilish")],
            [KeyboardButton("Barcha reyting")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Admin menyusi:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Sizga admin huquqi berilmagan! Iltimos, avval maxfiy kalitni kiriting.")

# Savol qo‘shish
async def add_question(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id in authorized_admins:
        await update.message.reply_text("Iltimos, savol uchun rasm yuboring.")
    else:
        await update.message.reply_text("Sizga ruxsat berilmagan!")

# Savolni qo‘shish uchun rasmni qabul qilish
async def receive_question_photo(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id in authorized_admins:
        if update.message.photo:
            question_photo = update.message.photo[-1].file_id
            question_code = f"q{len(questions) + 1}"
            questions[question_code] = {"image": question_photo, "answers": [], "attempted_users": set()}
            await update.message.reply_text(f"Savol qo‘shildi. Kod: {question_code}. Javoblar qo‘shish uchun 'Javob qo‘shish' tugmasidan foydalaning.")
        else:
            await update.message.reply_text("Iltimos, savol uchun rasm yuboring.")
    else:
        await update.message.reply_text("Sizga ruxsat berilmagan!")

# Javob qo‘shish
async def add_answer(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id in authorized_admins:
        await update.message.reply_text("Iltimos, savol kodini kiriting va javobni yozing.\nFormat: /add_answer <savol_kodi> <javob>")
    else:
        await update.message.reply_text("Sizga ruxsat berilmagan!")

# Javob qo‘shishning ishlashi
async def handle_add_answer(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id in authorized_admins:
        try:
            # Savol kodi va javoblarni olish
            question_code = context.args[0]
            new_answer = " ".join(context.args[1:])

            # Agar savol kodi mavjud bo'lsa, javobni qo'shish
            if question_code in questions:
                questions[question_code]["answers"].append(new_answer)
                await update.message.reply_text(f"Javob '{new_answer}' savol {question_code} uchun muvaffaqiyatli qo‘shildi!")
            else:
                await update.message.reply_text("Bunday savol kodi topilmadi.")
        except (IndexError, ValueError):
            await update.message.reply_text("Noto‘g‘ri format. To‘g‘ri format: /add_answer <savol_kodi> <javob>")
    else:
        await update.message.reply_text("Sizga ruxsat berilmagan!")

# Savol kodi yuborilganda savolni ko‘rsatish
async def send_question(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    user_text = update.message.text.strip()

    if user_text.startswith("q"):
        question_code = user_text
        if question_code in questions:
            user_states[user_id] = {"current_question": question_code}  # Foydalanuvchi holatini saqlash
            question = questions[question_code]
            question_image = question["image"]
            await update.message.reply_photo(
                question_image, caption=f"Savol kodi: {question_code}. Javoblaringizni yuboring."
            )
        else:
            await update.message.reply_text("Bunday savol kodi topilmadi.")
    else:
        await update.message.reply_text("Iltimos, savol kodini yuboring.")

# Javobni tekshirish
async def check_answers(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    user_text = update.message.text.strip()

    if user_id in user_states and "current_question" in user_states[user_id]:
        question_code = user_states[user_id]["current_question"]
        if question_code in questions:
            question = questions[question_code]
            correct_answers = question["answers"]

            if not correct_answers:
                await update.message.reply_text("Bu savol uchun javoblar hali qo‘shilmagan.")
                return

            user_answers = user_text.split()
            score = sum(1 for ua in user_answers if ua in correct_answers)
            user_scores[user_id] = user_scores.get(user_id, 0) + score
            await update.message.reply_text(f"Siz {score} ta to‘g‘ri javob berdingiz! Umumiy ballaringiz: {user_scores[user_id]}.")

            # Foydalanuvchi holatini tozalash
            user_states.pop(user_id, None)
        else:
            await update.message.reply_text("Bunday savol kodi topilmadi.")
    else:
        await update.message.reply_text("Savol tanlanmagan. Avval savol kodini yuboring.")

# Foydalanuvchi buyruqlariga ishlov berish
async def handle_user_commands(update: Update, context: CallbackContext) -> None:
    user_text = update.message.text.strip()

    if user_text == "Savol kodi yuborish":
        if len(questions) > 0:
            await update.message.reply_text("Iltimos, savol kodini yuboring (masalan, q1).")
        else:
            await update.message.reply_text("Hozirda savollar mavjud emas.")
    elif user_text.startswith("q"):  # Masalan, "q1"
        await send_question(update, context)
    elif user_text == "Reytingni ko‘rish":
        user_id = update.message.chat_id
        user_score = user_scores.get(user_id, 0)
        await update.message.reply_text(f"Sizning umumiy ballaringiz: {user_score}.")
    else:
        await update.message.reply_text("Mavjud bo‘lmagan buyruq. Iltimos, menyudan tanlang.")

# Asosiy bot funksiyasi
def main():
    application = Application.builder().token(TOKEN).build()

    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("authorize", authorize))
    application.add_handler(CommandHandler("add_answer", handle_add_answer))
    application.add_handler(MessageHandler(filters.PHOTO, receive_question_photo))
    application.add_handler(MessageHandler(filters.Regex(r'^q\d+\s+.*$'), check_answers))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_commands))

    # Botni ishga tushirish
    application.run_polling()

if __name__ == "__main__":
    main()
