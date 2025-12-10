import os
import sys

# --- 1. SETTINGS & FIXES ---
# Force CrewAI to use xAI (Grok)
os.environ["OPENAI_API_BASE"] = "https://api.x.ai/v1"
os.environ["OPENAI_BASE_URL"] = "https://api.x.ai/v1"
os.environ["OPENAI_API_KEY"] = os.environ.get("XAI_API_KEY")

from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import yfinance as yf
import telebot

# Keys Setup
XAI_KEY = os.environ.get("XAI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not XAI_KEY or not TELEGRAM_TOKEN:
    print("Error: Keys missing!")
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- 2. MARKET DATA ---
def get_market_data():
    try:
        ticker = yf.Ticker("EURUSD=X")
        data = ticker.history(period="1d", interval="1h")
        if data.empty: return "No Data"
        price = data['Close'].iloc[-1]
        trend = "UP" if price > data['Open'].iloc[-1] else "DOWN"
        return f"EUR/USD Price: {price:.4f} | Trend: {trend}"
    except:
        return "Error fetching data"

market_info = get_market_data()

# --- 3. AI BRAIN ---
llm = ChatOpenAI(
    api_key=XAI_KEY,
    base_url="https://api.x.ai/v1",
    model="grok-beta"
)

# --- 4. AGENTS ---
analyst = Agent(
    role='FX Expert',
    goal='Analyze trend',
    backstory='Expert trader.',
    verbose=True,
    llm=llm,
    allow_delegation=False
)

writer = Agent(
    role='Writer',
    goal='Write telegram msg',
    backstory='Summarizer.',
    verbose=True,
    llm=llm,
    allow_delegation=False
)

# --- 5. TASKS ---
task1 = Task(description=f"Analyze: {market_info}. BUY or SELL?", agent=analyst, expected_output="Decision")
task2 = Task(description="Write short telegram msg with signal and price.", agent=writer, expected_output="Message string")

# --- 6. RUN ---
# Dhyan dein: Niche wali lines ekdam Left side (diwar) se chipki hain
crew = Crew(agents=[analyst, writer], tasks=[task1, task2], memory=False)
result = crew.kickoff()

# Telegram
print(f"Sending: {result}")
bot.send_message(CHAT_ID, str(result))
