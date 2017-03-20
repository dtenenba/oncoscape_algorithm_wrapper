from flask import Flask
import do_plsr
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'
