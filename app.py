import os
import streamlit as st
import speech_recognition as sr
import pyttsx3
import queue
import threading
from groq import Groq
import requests
import pint
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.playback import play

# Load environment variables
load_dotenv()

# Initialize Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize Unit Registry (for conversions)
ureg = pint.UnitRegistry()

# Fetch API Key for Exchange Rates
exchange_rate_api_key = os.getenv("EXCHANGE_RATE_API_KEY")

# Initialize text-to-speech engine
engine = pyttsx3.init(driverName='sapi5')
engine.say("Hello, your text-to-speech is working!")
engine.runAndWait()
speak_queue: queue.Queue[str] = queue.Queue()

def speak_worker():
    """Worker function to process speech tasks from the queue."""
    while True:
        text = speak_queue.get()
        if text is None:  # Exit condition
            break
        engine.say(text)
        engine.runAndWait()
        speak_queue.task_done()

# Start the speech thread
speech_thread = threading.Thread(target=speak_worker, daemon=True)
speech_thread.start()

def speak(text):
    """Add text to the speech queue."""
    speak_queue.put(text)

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

def voice_input():
    recognizer = sr.Recognizer()
    st.info("Listening... Speak now!")

    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source)
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Sorry, I could not understand the audio."
        except sr.RequestError:
            return "Could not request results."

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
        speak(f"The result is {result}")

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
        speak(f"The converted amount is {result}")

query = st.text_input("Ask AI about conversions (e.g., 'How much does 5 kg weigh on the Moon?')")
if st.button("Get AI Suggestion"):
    ai_response = ai_suggestions(query)
    st.info(f"🤖 AI Suggestion: {ai_response}")
    speak(ai_response)

if st.button("🎤 Speak for Conversion"):
    spoken_text = voice_input()
    
    if spoken_text:
        st.success(f"🗣️ You said: {spoken_text}")
        speak(f"You said: {spoken_text}")
        
        words = spoken_text.split()
        if len(words) >= 3 and words[0].lower() == "convert":
            try:
                value = float(words[1])
                from_unit = words[2]
                to_unit = words[-1]
                
                if from_unit.upper() in currencies and to_unit.upper() in currencies:
                    result = convert_currency(value, from_unit.upper(), to_unit.upper())
                else:
                    result = convert_units(value, from_unit, to_unit)
                
                st.success(f"✅ Result: {result}")
                speak(f"The result is {result}")
            except ValueError:
                st.warning("Invalid format. Try saying: 'Convert 10 kg to pounds'.")
        else:
            ai_response = ai_suggestions(spoken_text)
            st.info(f"🤖 AI Response: {ai_response}")
            speak(ai_response)
