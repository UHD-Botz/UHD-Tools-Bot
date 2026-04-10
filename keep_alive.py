from flask import Flask
from waitress import serve
import threading
import os

app = Flask(__name__)

@app.route('/')
def health_check():
    return "UHD Tools Bot is Running 🚀"

def run():
    port = int(os.environ.get("PORT", 8000))
    serve(app, host="0.0.0.0", port=port, _quiet=True)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
