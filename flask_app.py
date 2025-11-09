# flask_app.py - 100% WORKING VERSION (November 2025)
import json
import re
import telebot
from flask import Flask, request
import os

# TOKEN FROM ENVIRONMENT - NO HARD CODED TOKEN!
TOKEN = os.environ.get('BOT_TOKEN')
USERNAME = os.environ.get('PYTHONANYWHERE_USERNAME')

if not TOKEN or not USERNAME:
    print("ERROR: Set BOT_TOKEN and PYTHONANYWHERE_USERNAME in Bash console!")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# Load your JSON
try:
    with open('icd10_codes_2025.json', 'r', encoding='utf-8') as f:
        icd_data = json.load(f)
    desc_to_code = {}
    for code, info in icd_data.items():
        key = info['long_description'].lower()
        desc_to_code.setdefault(key, []).append(code)
    print(f"Loaded {len(icd_data)} codes")
except Exception as e:
    print("JSON ERROR:", e)
    exit(1)

def is_icd_code(q):
    return re.match(r'^[A-Z]\d{2}(\.\d{1,4})?$', q.strip().upper())

def code_to_disease(code):
    code = code.upper().strip()
    info = icd_data.get(code)
    if not info: return "Code not found."
    status = '(Category Header - Non-billable)' if info.get('is_header') else '(Billable Code)'
    return f"**{code}**\n{info['long_description']}\n{info['short_description']}\n{status}"

def disease_to_code(term):
    term = term.lower().strip()
    results = []
    for desc, codes in desc_to_code.items():
        if term in desc:
            for c in codes:
                info = icd_data[c]
                status = '(Category Header - Non-billable)' if info.get('is_header') else '(Billable Code)'
                results.append(f"**{c}**\n{info['long_description']}\n{info['short_description']}\n{status}")
    return results or ["No results found."]

@bot.message_handler(commands=['start', 'help'])
def start(m):
    bot.reply_to(m, "ICD-10 Bot is ONLINE 24/7!\nSend code (E11.9) or disease (diabetes)")

@bot.message_handler(func=lambda m: True)
def all(m):
    q = m.text.strip()
    if is_icd_code(q):
        bot.reply_to(m, code_to_disease(q), parse_mode='Markdown')
    else:
        res = disease_to_code(q)
        chunk = ""
        for r in res:
            if len(chunk) + len(r) > 3900:
                bot.send_message(m.chat.id, chunk, parse_mode='Markdown')
                chunk = ""
            chunk += r + "\n\n"
        if chunk:
            bot.send_message(m.chat.id, chunk, parse_mode='Markdown')

# Flask
app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def setup():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{USERNAME}.pythonanywhere.com/{TOKEN}")
    return "BOT IS NOW ALWAYS ON!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.environ.get("PORT", 5000))