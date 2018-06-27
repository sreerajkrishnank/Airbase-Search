from flask import Flask, request
import json
from symspell import init, get_suggestions
import numpy as np
app = Flask(__name__)

def takeSecond(elem):
    return elem[1]

@app.route("/search")
def hello():
    word = request.args.get('word')
    suggestions = get_suggestions(word)
    # sorted_list = sorted(suggestions, key=lambda(term, (freq, dist)): (dist, -freq))
    return json.dumps(suggestions)

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    init()
    app.debug = True
    app.run()
