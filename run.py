import asyncio
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Bot tokenini shu yerga kiriting
BOT_TOKEN = "8492051752:AAGLlduftP4Vme-d27QDSZbcYhePS6bNbjE"

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# States yaratish
class TestStates(StatesGroup):
    waiting_answer = State()

# Foydalanuvchi ma'lumotlarini saqlash
user_data = {}

# Matnli masalalar shablonlari
TEXT_PROBLEMS = [
    "Aziza {a} ta olma sotib oldi, keyin yana {b} ta sotib oldi. Hammasi bo'lib nechta olma bo'ldi?|{a}+{b}",
    "Do'konda {a} ta kitob bor edi. {b} ta sotildi. Nechta kitob qoldi?|{a}-{b}",
    "Sardor har kuni {a} ta mashq bajaradi. {b} kunda jami nechta mashq bajaradi?|{a}*{b}",
    "Maktabda {a} ta o'quvchi bor. Ularni {b} ta guruhga teng bo'lishdi. Har guruhda nechta o'quvchi?|{a}//{b}",
    "Bog'da {a} ta daraxt bor edi. Yana {b} ta ko'chatni ekishdi. Jami nechta daraxt bo'ldi?|{a}+{b}",
    "Fermer {a} kg olma yig'di va ularni {b} ta qutiga teng bo'lib soldi. Har qutida necha kg olma bo'ldi?|{a}//{b}",
    "Javohir {a} so'm pul yig'di. {b} so'm sarfladi. Qancha puli qoldi?|{a}-{b}",
    "Bir quti {a} so'm turadi. {b} ta quti necha so'm turadi?|{a}*{b}",
    "Sinfdagi {a} ta o'quvchidan {b} nafari qiz. Necha nafari o'g'il bola?|{a}-{b}",
    "Kutubxonada {a} ta kitob bor. Ularning {b} baravari yangi kitoblar keldi. Jami nechta kitob bo'ldi?|{a}+{a}*{b}",
]

def generate_question(level):
    """Savol yaratish funksiyasi"""
    if level == 'easy':
        # Oson savol: 1-1000 oralig'ida
        a = random.randint(1, 1000)
        b = random.randint(1, 1000)
        op = random.choice(['+', '-', '*', '/'])
        
        if op == '+':
            question = f"{a} + {b} nechiga teng?"
            answer = a + b
        elif op == '-':
            if a < b:
                a, b = b, a
            question = f"{a} - {b} nechiga teng?"
            answer = a - b
        elif op == '*':
            a = random.randint(1, 100)
            b = random.randint(1, 100)
            question = f"{a} × {b} nechiga teng?"
            answer = a * b
        else:
            b = random.randint(1, 50)
            a = b * random.randint(1, 20)
            question = f"{a} ÷ {b} nechiga teng?"
            answer = a // b
            
        time_limit = 30
        
    elif level == 'medium':
        # O'rtacha savol: 1-10000 oralig'ida
        a = random.randint(1, 10000)
        b = random.randint(1, 10000)
        op = random.choice(['+', '-', '*', '/'])
        
        if op == '+':
            question = f"{a} + {b} nechiga teng?"
            answer = a + b
        elif op == '-':
            if a < b:
                a, b = b, a
            question = f"{a} - {b} nechiga teng?"
            answer = a - b
        elif op == '*':
            a = random.randint(1, 500)
            b = random.randint(1, 500)
            question = f"{a} × {b} nechiga teng?"
            answer = a * b
        else:
            b = random.randint(1, 100)
            a = b * random.randint(1, 100)
            question = f"{a} ÷ {b} nechiga teng?"
            answer = a // b
            
        time_limit = 30
        
    else:  # hard
        # Qiyin savol: matnli masala
        template = random.choice(TEXT_PROBLEMS)
        text, formula = template.split('|')
        
        # Sonlarni generatsiya qilish
        if '//' in formula:
            b = random.randint(2, 100)
            a = b * random.randint(10, 500)
        else:
            a = random.randint(100, 50000)
            b = random.randint(100, 50000)
        
        question = text.format(a=a, b=b)
        answer = eval(formula.format(a=a, b=b))
        time_limit = 90
    
    return question, answer, time_limit

def generate_options(correct_answer):
    """Javob variantlarini yaratish"""
    options = [correct_answer]
    
    # 3 ta noto'g'ri javob qo'shish
    while len(options) < 4:
        # Noto'g'ri javoblarni to'g'ri javobga yaqin qilish
        offset = random.randint(1, max(10, abs(correct_answer) // 10))
        wrong = correct_answer + random.choice([-1, 1]) * offset
        if wrong not in options and wrong > 0:
            options.append(wrong)
    
    random.shuffle(options)
    return options

def create_options_keyboard(options, question_num):
    """Javob tugmalarini yaratish"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(opt), callback_data=f"answer_{question_num}_{opt}")]
        for opt in options
    ])
    return keyboard

def create_menu_keyboard():
    """Asosiy menyu tugmalari"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Testni boshlash", callback_data="start_test")],
        [InlineKeyboardButton(text="❓ Yordam", callback_data="help")]
    ])
    return keyboard

def create_result_keyboard():
    """Natija ekranidagi tugmalar"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Qayta test", callback_data="start_test")],
        [InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu")]
    ])
    return keyboard

async def send_question(chat_id, user_id):
    """Savolni yuborish va taymer boshlash"""
    data = user_data[user_id]
    current = data['current_question']
    
    # Savolni generatsiya qilish
    if current < 15:
        level = 'easy'
    elif current < 30:
        level = 'medium'
    else:
        level = 'hard'
    
    question, answer, time_limit = generate_question(level)
    options = generate_options(answer)
    
    # Ma'lumotlarni saqlash
    data['questions'].append({
        'question': question,
        'answer': answer,
        'options': options,
        'time_limit': time_limit,
        'start_time': asyncio.get_event_loop().time()
    })
    
    # Savolni yuborish
    keyboard = create_options_keyboard(options, current)
    level_name = "Oson" if level == 'easy' else "O'rtacha" if level == 'medium' else "Qiyin"
    
    message = await bot.send_message(
        chat_id,
        f"📊 {current + 1}-savol / 45 ({level_name})\n\n"
        f"❓ {question}\n\n"
        f"⏱ Qolgan vaqt: {time_limit} soniya",
        reply_markup=keyboard
    )
    
    data['current_message_id'] = message.message_id
    
    # Taymer boshlash
    asyncio.create_task(timer_countdown(chat_id, user_id, current, time_limit))

async def timer_countdown(chat_id, user_id, question_num, time_limit):
    """Vaqtni hisoblash va yangilash"""
    data = user_data.get(user_id)
    if not data:
        return
    
    for remaining in range(time_limit - 1, -1, -1):
        await asyncio.sleep(1)
        
        # Foydalanuvchi javob berganini tekshirish
        if user_id not in user_data or data['current_question'] != question_num:
            return
        
        # Xabarni yangilash (har 5 soniyada)
        if remaining % 5 == 0 or remaining < 10:
            try:
                question_data = data['questions'][question_num]
                level = "Oson" if question_num < 15 else "O'rtacha" if question_num < 30 else "Qiyin"
                keyboard = create_options_keyboard(question_data['options'], question_num)
                
                await bot.edit_message_text(
                    f"📊 {question_num + 1}-savol / 45 ({level})\n\n"
                    f"❓ {question_data['question']}\n\n"
                    f"⏱ Qolgan vaqt: {remaining} soniya",
                    chat_id,
                    data['current_message_id'],
                    reply_markup=keyboard
                )
            except:
                pass
    
    # Vaqt tugadi
    if user_id in user_data and data['current_question'] == question_num:
        data['wrong_answers'] += 1
        data['current_question'] += 1
        
        await bot.edit_message_text(
            "⏰ Vaqt tugadi! Javob noto'g'ri deb hisoblanadi.\n\n"
            "⏭ Keyingi savolga o'tilmoqda...",
            chat_id,
            data['current_message_id']
        )
        
        await asyncio.sleep(2)
        
        # Keyingi savol yoki natija
        if data['current_question'] < 45:
            await send_question(chat_id, user_id)
        else:
            await show_result(chat_id, user_id)

async def show_result(chat_id, user_id):
    """Test natijasini ko'rsatish"""
    data = user_data[user_id]
    correct = data['correct_answers']
    total = 45
    percentage = (correct / total) * 100
    passed = percentage >= 80
    
    result_text = (
        "🎯 <b>TEST YAKUNLANDI!</b>\n\n"
        f"✅ To'g'ri javoblar: {correct}\n"
        f"❌ Noto'g'ri javoblar: {data['wrong_answers']}\n"
        f"📊 Jami savollar: {total}\n\n"
        f"📈 Natija: <b>{percentage:.1f}%</b>\n\n"
    )
    
    if passed:
        result_text += "🎉 <b>TABRIKLAYMIZ! Siz testdan muvaffaqiyatli o'tdingiz!</b>"
    else:
        result_text += "😔 <b>Afsuski, siz testdan o'ta olmadingiz. O'tish bali: 80%</b>"
    
    await bot.send_message(
        chat_id,
        result_text,
        reply_markup=create_result_keyboard(),
        parse_mode='HTML'
    )
    
    # Ma'lumotlarni tozalash
    del user_data[user_id]

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Start buyrug'i"""
    await message.answer(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Men Matematik Test Boti. Sizning matematik bilimingizni sinash uchun yaratilganman.\n\n"
        "📝 <b>Test haqida:</b>\n"
        "• Jami 45 ta savol\n"
        "• 15 ta oson (30 soniya)\n"
        "• 15 ta o'rtacha (30 soniya)\n"
        "• 15 ta qiyin (90 soniya)\n"
        "• O'tish bali: 80%\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=create_menu_keyboard(),
        parse_mode='HTML'
    )

@dp.message(Command("test"))
async def cmd_test(message: Message):
    """Test buyrug'i"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, boshlaymiz!", callback_data="start_test")],
        [InlineKeyboardButton(text="❌ Yo'q, ortga", callback_data="main_menu")]
    ])
    
    await message.answer(
        "📝 <b>Testni boshlaysizmi?</b>\n\n"
        "Test 45 ta savoldan iborat. Tayyor bo'lsangiz boshlang!",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    """Testni to'xtatish"""
    user_id = message.from_user.id
    
    if user_id in user_data:
        del user_data[user_id]
        await message.answer(
            "🛑 Test to'xtatildi.\n\n"
            "Qayta boshlash uchun /test buyrug'ini yuboring.",
            reply_markup=create_menu_keyboard()
        )
    else:
        await message.answer(
            "❌ Hozirda faol test yo'q.",
            reply_markup=create_menu_keyboard()
        )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Yordam buyrug'i"""
    await message.answer(
        "📖 <b>BOTDAN FOYDALANISH QO'LLANMASI</b>\n\n"
        "🤖 <b>Buyruqlar:</b>\n"
        "/start - Botni ishga tushirish\n"
        "/test - Testni boshlash\n"
        "/stop - Testni to'xtatish\n"
        "/help - Yordam\n\n"
        "📝 <b>Test haqida:</b>\n"
        "• Test 45 ta savoldan iborat\n"
        "• Har savol uchun 4 ta variant\n"
        "• Faqat tugmalar orqali javob berish mumkin\n"
        "• Har savol uchun vaqt cheklangan\n\n"
        "⚡️ <b>Qiyinlik darajalari:</b>\n"
        "1️⃣ Oson (15 savol) - 30 soniya\n"
        "   Oddiy amallar, 1000 gacha sonlar\n\n"
        "2️⃣ O'rtacha (15 savol) - 30 soniya\n"
        "   Oddiy amallar, 10000 gacha sonlar\n\n"
        "3️⃣ Qiyin (15 savol) - 90 soniya\n"
        "   Matnli masalalar, 50000 gacha sonlar\n\n"
        "🎯 <b>O'tish bali:</b> 80% (36/45 to'g'ri)\n\n"
        "⏰ Vaqt tugasa, javob noto'g'ri hisoblanadi.\n\n"
        "Omad tilayman! 🍀",
        reply_markup=create_menu_keyboard(),
        parse_mode='HTML'
    )

@dp.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Bosh sahifaga qaytish"""
    await callback.message.edit_text(
        "🏠 <b>Bosh sahifa</b>\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=create_menu_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()

@dp.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Yordam"""
    await callback.message.edit_text(
        "📖 <b>BOTDAN FOYDALANISH QO'LLANMASI</b>\n\n"
        "🤖 <b>Buyruqlar:</b>\n"
        "/start - Botni ishga tushirish\n"
        "/test - Testni boshlash\n"
        "/stop - Testni to'xtatish\n"
        "/help - Yordam\n\n"
        "📝 <b>Test haqida:</b>\n"
        "• Test 45 ta savoldan iborat\n"
        "• Har savol uchun 4 ta variant\n"
        "• Faqat tugmalar orqali javob berish mumkin\n"
        "• Har savol uchun vaqt cheklangan\n\n"
        "⚡️ <b>Qiyinlik darajalari:</b>\n"
        "1️⃣ Oson (15 savol) - 30 soniya\n"
        "2️⃣ O'rtacha (15 savol) - 30 soniya\n"
        "3️⃣ Qiyin (15 savol) - 90 soniya\n\n"
        "🎯 <b>O'tish bali:</b> 80% (36/45 to'g'ri)\n\n"
        "Omad tilayman! 🍀",
        reply_markup=create_menu_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()

@dp.callback_query(F.data == "start_test")
async def callback_start_test(callback: CallbackQuery):
    """Testni boshlash"""
    user_id = callback.from_user.id
    
    # Foydalanuvchi ma'lumotlarini yaratish
    user_data[user_id] = {
        'current_question': 0,
        'correct_answers': 0,
        'wrong_answers': 0,
        'questions': [],
        'current_message_id': None
    }
    
    await callback.message.edit_text(
        "🚀 <b>Test boshlanmoqda...</b>\n\n"
        "Tayyor bo'ling!",
        parse_mode='HTML'
    )
    
    await asyncio.sleep(1)
    await send_question(callback.message.chat.id, user_id)
    await callback.answer()

@dp.callback_query(F.data.startswith("answer_"))
async def callback_answer(callback: CallbackQuery):
    """Javobni tekshirish"""
    user_id = callback.from_user.id
    
    if user_id not in user_data:
        await callback.answer("❌ Test topilmadi. /test buyrug'i bilan qayta boshlang.", show_alert=True)
        return
    
    data = user_data[user_id]
    _, question_num, answer = callback.data.split("_")
    question_num = int(question_num)
    answer = int(answer)
    
    # Savolni tekshirish
    if data['current_question'] != question_num:
        await callback.answer("⚠️ Bu savol allaqachon o'tgan!", show_alert=True)
        return
    
    question_data = data['questions'][question_num]
    correct_answer = question_data['answer']
    
    # Javobni tekshirish
    if answer == correct_answer:
        data['correct_answers'] += 1
        result_emoji = "✅"
        result_text = "To'g'ri javob!"
    else:
        data['wrong_answers'] += 1
        result_emoji = "❌"
        result_text = f"Noto'g'ri! To'g'ri javob: {correct_answer}"
    
    data['current_question'] += 1
    
    await callback.message.edit_text(
        f"{result_emoji} <b>{result_text}</b>\n\n"
        f"⏭ Keyingi savolga o'tilmoqda...",
        parse_mode='HTML'
    )
    
    await asyncio.sleep(1.5)
    
    # Keyingi savol yoki natija
    if data['current_question'] < 45:
        await send_question(callback.message.chat.id, user_id)
    else:
        await show_result(callback.message.chat.id, user_id)
    
    await callback.answer()

# Noma'lum xabarlarni qaytarish
@dp.message()
async def unknown_message(message: Message):
    """Noma'lum xabarlar"""
    await message.answer(
        "❌ Men faqat tugmalar orqali ishlayman.\n\n"
        "Iltimos, quyidagi tugmalardan foydalaning:",
        reply_markup=create_menu_keyboard()
    )

async def main():
    """Botni ishga tushirish"""
    print("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())