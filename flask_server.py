import json

from flask import Flask
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

new_pages_file = 'new_notion_pages.json'
pages_for_removing_file = 'pages_for_removing.json'


@app.route("/add")
@cross_origin()
def add_pages():
    print("add_pages() called")

    with open(new_pages_file, 'r') as file:
        label = file.read()

        print(f'file: {label}')

    with open(new_pages_file, 'w') as file:
        json.dump({}, file)

    return label

@app.route("/remove")
@cross_origin()
def remove_pages():
    print("remove_pages() called")

    with open(pages_for_removing_file, 'r') as file:
        label = file.read()


    with open(pages_for_removing_file, 'w') as file:
        json.dump({}, file)

    return label


if __name__ == "__main__":
    app.run(debug=True)
