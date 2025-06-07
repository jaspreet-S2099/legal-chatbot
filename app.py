from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from gemini_utils import generate_legal_response
from dotenv import load_dotenv
import pandas as pd
import os

# Load .env variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")  # Set secret key from .env

# Load IPC dataset on startup
df = pd.read_csv("ipc_sections.csv")

# Intro route (shown first unless already started)
@app.route('/')
def intro():
    if session.get('visited'):
        return redirect(url_for('index'))
    return render_template('intro.html')

# Triggered only by Get Started button
@app.route('/start')
def start():
    session['visited'] = True
    return redirect(url_for('index'))

# Main app page after intro
@app.route('/index')
def index():
    return render_template('index.html')

# Documentation page
@app.route('/docs')
def docs():
    return render_template('docs.html')

# Chatbot POST endpoint
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']

    if not user_message.strip():
        return jsonify({'response': "Please enter a valid query."})

    bot_response = generate_legal_response(user_message, df)
    return jsonify({'response': bot_response})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

