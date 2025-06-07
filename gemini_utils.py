import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key securely from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"GEMINI_API_KEY: {GEMINI_API_KEY!r}")  # <--- This will print key or None

# Configure Gemini with loaded key
genai.configure(api_key=GEMINI_API_KEY)

# Choose the model
model = genai.GenerativeModel("gemini-2.0-flash")

def is_small_talk(query):
    small_talk_keywords = [
        "hi", "hello", "how are you", "who are you", "what's up",
        "good morning", "good evening", "good night", "hey", "thanks", "thank you"
    ]
    return any(k in query.lower() for k in small_talk_keywords)

def is_irrelevant_query(query):
    irrelevant_keywords = ["joke", "dance", "mars", "aliens", "pizza", "weather", "song"]
    return any(k in query.lower() for k in irrelevant_keywords)

def generate_legal_response(user_query, df):
    """
    Handles user queries:
    1. Strict dataset match → formatted IPC response
    2. Small talk → casual Gemini response
    3. No IPC match but legal → Gemini Indian law-based response
    4. Absurd → fallback message
    """

    # 1. Handle small talk
    if is_small_talk(user_query):
        try:
            response = model.generate_content(user_query)
            return response.text.strip()
        except Exception as e:
            return f"An error occurred: {str(e)}"

    # 2. Handle clearly irrelevant queries
    if is_irrelevant_query(user_query):
        return "Sorry, I couldn't find any relevant result for your query."

    # 3. Prepare dataset as reference context for Gemini
    context_rows = []
    for _, row in df.iterrows():
        context_rows.append(
            f"Section: {row['Section']}\nOffense: {row['Offense']}\nDescription: {row['Description']}\nPunishment: {row['Punishment']}"
        )

    ipc_context = "\n\n".join(context_rows)

    # Prompt Gemini to only use dataset
    strict_prompt = f"""
You are a legal assistant AI. Use the dataset provided to answer queries related to IPC (Indian Penal Code) sections.
Only use the data from this dataset, do not hallucinate or invent IPC information.

User query: "{user_query}"

Dataset:
{ipc_context}

Based on the above dataset, respond concisely in this format:
- IPC Section(s)
- Description
- Punishment

If no section is relevant, reply: "NO_MATCH"
"""

    try:
        response = model.generate_content(strict_prompt)
        reply_text = response.text.strip()

        # If Gemini couldn't find a match from dataset, it replies with NO_MATCH
        if "NO_MATCH" in reply_text:
            # Let Gemini use its own intelligence but limit it to Indian law
            fallback_prompt = f"""
You are a legal assistant AI specialized in Indian Law. If the user query does not match the IPC dataset,
respond with correct and concise information based only on the Indian legal system — including laws from any domain (education, finance, cybercrime, traffic, etc.).

Avoid hallucinations or non-Indian law content. If the query is irrelevant, absurd, or out of scope, simply say:
"Sorry, I couldn't find any relevant result for your query."

User query: "{user_query}"
"""

            fallback_response = model.generate_content(fallback_prompt)
            return fallback_response.text.strip()

        # If a match was found, return it
        return reply_text

    except Exception as e:
        return f"An error occurred: {str(e)}"
