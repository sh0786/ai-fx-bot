# Ready to Fly
import os
import sys
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import yfinance as yf
import telebot

# --- SETTINGS ---
XAI_KEY = os.environ.get("XAI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not XAI_KEY or not TELEGRAM_TOKEN:
    print("Error: Keys missing!")
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- 1. MARKET DATA ---
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

# --- 2. AI BRAIN (xAI / Grok) ---
llm = ChatOpenAI(
    api_key=XAI_KEY,
    base_url="https://api.x.ai/v1",
    model="grok-beta"
)

# --- 3. AGENTS ---
analyst = Agent(
    role='FX Expert',
    goal='Analyze trend',
    backstory='Expert trader.',
    verbose=True,
    llm=llm
)

writer = Agent(
    role='Writer',
    goal='Write telegram msg',
    backstory='Summarizer.',
    verbose=True,
    llm=llm
)

# --- 4. TASKS ---
task1 = Task(description=f"Analyze: {market_info}. BUY or SELL?", agent=analyst, expected_output="Decision")
task2 = Task(description="Write short telegram msg with signal and price.", agent=writer, expected_output="Message string")

# --- 5. RUN ---
 crew = Crew(agents=[analyst, writer], tasks=[task1, task2], memory=False)

result = crew.kickoff()
bot.send_message(CHAT_ID, str(result))
