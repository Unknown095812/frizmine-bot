import os
import requests
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Получаем токен из переменной окружения
BOT_TOKEN = os.getenv('BOT_TEKON', 7592986586:AAFXGYbQ9-bVhPr6LwEB8A4taCRt170NxgQ)

# API endpoints
API_SERVERS = 'https://frizmine.shop/api/servers/public'
API_PAYMENTS = 'https://frizmine.shop/api/payments/last'

# Для хранения подписчиков на уведомления
subscribers = set()
last_payment_id = None

def get_servers():
    """Получить данные о серверах"""
    try:
        response = requests.get(API_SERVERS, timeout=10)
        return response.json()
    except:
        return None

def get_payments():
    """Получить последние покупки"""
    try:
        response = requests.get(API_PAYMENTS, timeout=10)
        return response.json()
    except:
        return None

def format_server_status(servers):
    """Форматирование статуса серверов"""
    if not servers:
        return "❌ Ошибка загрузки данных"
    
    # Разделяем лобби и игровые серверы
    lobby = next((s for s in servers if s.get('lobby', False)), None)
    game_servers = [s for s in servers if not s.get('lobby', False)]
    
    # Общий онлайн (из лобби)
    total_online = lobby['online'] if lobby else 0
    
    # Онлайн по анархиям
    anarchy_online = sum(s['online'] for s in game_servers)
    
    message = f"📊 **СТАТУС СЕРВЕРОВ FRIZMINE**\n"
    message += f"━━━━━━━━━━━━━━━━━━\n"
    message += f"👥 **Всего онлайн:** {total_online}\n"
    message += f"🎮 **В анархиях:** {anarchy_online}\n\n"
    
    # Лобби
    if lobby:
        percentage = int(lobby['online'] / lobby['max'] * 100) if lobby['max'] > 0 else 0
        bar = create_progress_bar(percentage)
        message += f"🟪 **{lobby['name']}**\n"
        message += f"{bar} {lobby['online']}/{lobby['max']} ({percentage}%)\n\n"
    
    # Игровые серверы
    message += "**АНАРХИИ:**\n"
    for server in game_servers:
        emoji = "🟢" if server['online'] > 0 else "🔴"
        percentage = int(server['online'] / server['max'] * 100) if server['max'] > 0 else 0
        bar = create_progress_bar(percentage)
        
        message += f"{emoji} **{server['name']}**\n"
        message += f"{bar} {server['online']}/{server['max']} ({percentage}%)\n\n"
    
    # Самый популярный
    if game_servers:
        most_popular = max(game_servers, key=lambda x: x['online'])
        message += f"━━━━━━━━━━━━━━━━━━\n"
        message += f"🔥 **Самый популярный:**\n{most_popular['name']} ({most_popular['online']} игроков)"
    
    return message

def create_progress_bar(percentage):
    """Создать прогресс-бар"""
    filled = int(percentage / 10)
    empty = 10 - filled
    return "▓" * filled + "░" * empty

def format_payments(payments):
    """Форматирование последних покупок"""
    if not payments:
        return "❌ Ошибка загрузки данных"
    
    message = "💰 **ПОСЛЕДНИЕ ПОКУПКИ**\n"
    message += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, payment in enumerate(payments[:10], 1):
        paid_time = datetime.fromisoformat(payment['paid_at'].replace('Z', '+00:00'))
        time_str = paid_time.strftime('%H:%M')
        
        message += f"{i}. **{payment['nickname']}**\n"
        message += f"   🆔 {payment['id']} • 🕐 {time_str}\n\n"
    
    return message

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [
        [InlineKeyboardButton("📊 Онлайн серверов", callback_data='online')],
        [InlineKeyboardButton("💰 Последние покупки", callback_data='payments')],
        [InlineKeyboardButton("📈 Статистика", callback_data='stats')],
        [InlineKeyboardButton("🔔 Уведомления", callback_data='notify')],
        [InlineKeyboardButton("🌐 Веб-панель", url='https://unknown095812.github.io/frizmine-panel/frizmine_panel.html')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🟪 **FRIZMINE MONITOR BOT**\n\n"
        "Отслеживай статистику серверов FrizMine в реальном времени!\n\n"
        "Выбери действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def online_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /online"""
    servers = get_servers()
    message = format_server_status(servers)
    
    keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data='refresh_online')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def payments_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /payments"""
    payments = get_payments()
    message = format_payments(payments)
    
    keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data='refresh_payments')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    servers = get_servers()
    payments = get_payments()
    
    if not servers or not payments:
        await update.message.reply_text("❌ Ошибка загрузки данных")
        return
    
    # Разделяем лобби и игровые серверы
    lobby = next((s for s in servers if s.get('lobby', False)), None)
    game_servers = [s for s in servers if not s.get('lobby', False)]
    
    total_online = lobby['online'] if lobby else 0
    total_slots = sum(s['max'] for s in servers)
    anarchy_online = sum(s['online'] for s in game_servers)
    
    # Загруженность
    load_percentage = int(total_online / total_slots * 100) if total_slots > 0 else 0
    
    message = "📈 **ПОЛНАЯ СТАТИСТИКА**\n"
    message += "━━━━━━━━━━━━━━━━━━\n\n"
    message += f"👥 **Общий онлайн:** {total_online}\n"
    message += f"🎮 **В анархиях:** {anarchy_online}\n"
    message += f"📊 **Всего слотов:** {total_slots}\n"
    message += f"⚡ **Загруженность:** {load_percentage}%\n"
    message += f"🖥️ **Серверов:** {len(servers)}\n\n"
    
    if game_servers:
        most_popular = max(game_servers, key=lambda x: x['online'])
        least_popular = min(game_servers, key=lambda x: x['online'])
        
        message += f"🔥 **Самый популярный:**\n"
        message += f"{most_popular['name']} ({most_popular['online']} игроков)\n\n"
        message += f"🌙 **Самый пустой:**\n"
        message += f"{least_popular['name']} ({least_popular['online']} игроков)\n\n"
    
    if payments:
        message += f"💸 **Последняя покупка:**\n"
        message += f"{payments[0]['nickname']}\n"
        paid_time = datetime.fromisoformat(payments[0]['paid_at'].replace('Z', '+00:00'))
        time_str = paid_time.strftime('%H:%M:%S')
        message += f"Время: {time_str}"
    
    keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data='refresh_stats')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'online' or query.data == 'refresh_online':
        servers = get_servers()
        message = format_server_status(servers)
        keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data='refresh_online')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data == 'payments' or query.data == 'refresh_payments':
        payments = get_payments()
        message = format_payments(payments)
        keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data='refresh_payments')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data == 'stats' or query.data == 'refresh_stats':
        servers = get_servers()
        payments = get_payments()
        
        if not servers or not payments:
            await query.edit_message_text("❌ Ошибка загрузки данных")
            return
        
        lobby = next((s for s in servers if s.get('lobby', False)), None)
        game_servers = [s for s in servers if not s.get('lobby', False)]
        
        total_online = lobby['online'] if lobby else 0
        total_slots = sum(s['max'] for s in servers)
        anarchy_online = sum(s['online'] for s in game_servers)
        load_percentage = int(total_online / total_slots * 100) if total_slots > 0 else 0
        
        message = "📈 **ПОЛНАЯ СТАТИСТИКА**\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        message += f"👥 **Общий онлайн:** {total_online}\n"
        message += f"🎮 **В анархиях:** {anarchy_online}\n"
        message += f"📊 **Всего слотов:** {total_slots}\n"
        message += f"⚡ **Загруженность:** {load_percentage}%\n"
        message += f"🖥️ **Серверов:** {len(servers)}\n\n"
        
        if game_servers:
            most_popular = max(game_servers, key=lambda x: x['online'])
            message += f"🔥 **Самый популярный:**\n"
            message += f"{most_popular['name']} ({most_popular['online']} игроков)\n\n"
        
        if payments:
            message += f"💸 **Последняя покупка:**\n"
            message += f"{payments[0]['nickname']}"
        
        keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data='refresh_stats')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data == 'notify':
        chat_id = update.effective_chat.id
        if chat_id in subscribers:
            subscribers.remove(chat_id)
            await query.edit_message_text("🔕 Уведомления отключены")
        else:
            subscribers.add(chat_id)
            await query.edit_message_text("🔔 Уведомления включены!\nТы будешь получать сообщения о новых покупках.")

async def check_new_payments(context: ContextTypes.DEFAULT_TYPE):
    """Фоновая задача: проверка новых покупок"""
    global last_payment_id
    
    payments = get_payments()
    if not payments:
        return
    
    if last_payment_id is None:
        last_payment_id = payments[0]['id']
        return
    
    new_payments = []
    for payment in payments:
        if payment['id'] > last_payment_id:
            new_payments.append(payment)
        else:
            break
    
    if new_payments:
        last_payment_id = new_payments[0]['id']
        
        for payment in reversed(new_payments):
            paid_time = datetime.fromisoformat(payment['paid_at'].replace('Z', '+00:00'))
            time_str = paid_time.strftime('%H:%M:%S')
            
            message = (
                f"💰 **НОВАЯ ПОКУПКА!**\n\n"
                f"Игрок: **{payment['nickname']}**\n"
                f"ID: {payment['id']}\n"
                f"Время: {time_str}"
            )
            
            for chat_id in list(subscribers):
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                except:
                    subscribers.discard(chat_id)

def main():
    """Запуск бота"""
    print("🤖 Запуск бота...")
    
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("online", online_command))
    application.add_handler(CommandHandler("payments", payments_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Запускаем фоновую проверку новых покупок каждые 60 секунд
    application.job_queue.run_repeating(check_new_payments, interval=60, first=10)
    
    print(f"✅ Бот запущен!")
    print(f"📱 Открой Telegram и найди своего бота")
    print(f"⚡ Нажми Ctrl+C для остановки")
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
