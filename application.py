from flask import Flask, request
import json
from symspell import init, get_suggestions
application = Flask(__name__)

def takeSecond(elem):
    return elem[1]

@application.route("/search")
def hello():
    word = request.args.get('word')
    print(word)
    suggestions = get_suggestions(word)
    # sorted_list = sorted(suggestions, key=lambda(term, (freq, dist)): (dist, -freq))
    return json.dumps(suggestions)

# run the application.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production application.
    init()
    application.debug = True
    application.run()
