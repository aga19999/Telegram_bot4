from credentials import BOT_TOKEN, BOT_USERNAME
from flask import Flask, render_template
app = Flask(__name__)


def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
