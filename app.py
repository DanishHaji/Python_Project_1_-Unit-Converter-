import os
import streamlit as st
import queue
import threading
from groq import Groq
import requests
import pint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize Unit Registry (for conversions)
ureg = pint.UnitRegistry()

# Fetch API Key for Exchange Rates
exchange_rate_api_key = os.getenv("EXCHANGE_RATE_API_KEY")

def ai_suggestions(query):
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": query}],
        model="llama-3.3-70b-versatile",
        stream=False,
    )
    return chat_completion.choices[0].message.content

def convert_units(value, from_unit, to_unit):
    try:
        return ureg.Quantity(value, from_unit).to(to_unit)
    except pint.errors.DimensionalityError:
        return "Invalid conversion."

def convert_currency(amount, from_currency, to_currency):
    """Convert currency using Exchange Rate API"""
    if not exchange_rate_api_key:
        return "API key missing."
    
    url = f"https://v6.exchangerate-api.com/v6/{exchange_rate_api_key}/latest/{from_currency}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code != 200 or "conversion_rates" not in data:
            return "Invalid currency conversion."
        
        rate = data["conversion_rates"].get(to_currency)
        if not rate:
            return "Invalid currency conversion."
        
        converted_amount = round(amount * rate, 2)
        return converted_amount
    
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="AI-Powered Converters", layout="centered")
st.title("🚀 Universal Converter Pro - Powered by AI 🤖")

# Create tabs
tab1, tab2 = st.tabs(["Unit Conversion", "Currency Converter"])

unit_categories = {
    "Length": ["meter", "kilometer", "mile", "foot", "inch", "centimeter", "millimeter", "yard", "nautical mile"],
    "Mass/Weight": ["kilogram", "gram", "pound", "ounce", "ton", "stone", "milligram", "microgram"],
    "Volume": ["liter", "milliliter", "gallon", "quart", "pint", "cup", "fluid ounce", "tablespoon", "teaspoon"],
    "Area": ["square meter", "square kilometer", "acre", "hectare", "square foot", "square mile", "square yard", "square inch"],
    "Temperature": ["celsius", "fahrenheit", "kelvin"],
    "Time": ["second", "minute", "hour", "day", "week", "month", "year"],
    "Speed": ["meter/second", "kilometer/hour", "mile/hour", "foot/second", "knot"],
    "Energy": ["joule", "kilojoule", "calorie", "kilocalorie", "BTU", "electronvolt", "watt-hour", "kilowatt-hour"],
    "Power": ["watt", "kilowatt", "megawatt", "horsepower"],
    "Pressure": ["pascal", "bar", "atmosphere", "psi", "torr"],
    "Data Storage": ["byte", "kilobyte", "megabyte", "gigabyte", "terabyte", "petabyte", "exabyte"],
    "Fuel Efficiency": ["miles per gallon", "kilometers per liter", "liters per 100 km"],
    "Digital Speed": ["bit per second", "kilobit per second", "megabit per second", "gigabit per second", "terabit per second"],
    "Frequency": ["hertz", "kilohertz", "megahertz", "gigahertz"],
    "Force": ["newton", "kilonewton", "pound-force", "dyne"],
}

with tab1:
    st.header("📏 Unit Conversion")
    conversion_type = st.selectbox("Choose a conversion type:", list(unit_categories.keys()))
    from_unit = st.selectbox("From Unit", unit_categories[conversion_type])
    to_unit = st.selectbox("To Unit", unit_categories[conversion_type])
    value = st.number_input("Enter Value", min_value=0.0, step=0.1)
    convert_button = st.button("Convert")
    
    if convert_button:
        result = convert_units(value, from_unit, to_unit)
        st.success(f"✅ Result: {result}")

with tab2:
    st.header("💰 Currency Converter")
    currencies = ["USD", "EUR", "GBP", "INR", "JPY", "CAD", "AUD", "PKR",  
    "CNY", "SGD", "AED", "CHF", "MYR", "THB", "SAR", "NZD"]
    amount = st.number_input("Enter Amount", min_value=0.0, step=0.1)
    from_currency = st.selectbox("From Currency", currencies)
    to_currency = st.selectbox("To Currency", currencies)
    currency_convert_button = st.button("Convert Currency")
    
    if currency_convert_button:
        result = convert_currency(amount, from_currency, to_currency)
        st.success(f"✅ Converted Amount: {result}")

query = st.text_input("Ask AI about conversions (e.g., 'How much does 5 kg weigh on the Moon?')")
if st.button("Get AI Suggestion"):
    ai_response = ai_suggestions(query)
    st.info(f"🤖 AI Suggestion: {ai_response}")
