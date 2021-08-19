import json

from flask import Flask
from flask_apscheduler import APScheduler
from flask_cors import CORS, cross_origin

from collect_pages_for_removing import collect_pages_for_removing
from notion_tracking import notion_tracking

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# TODO: запросов к серверу многовато, имхо

# TODO: вот это все тоже в переменные среды вынести
new_pages_file = 'new_notion_pages.json'
pages_for_removing_file = 'pages_for_removing.json'
scheduler = APScheduler()


@app.route("/add")
@cross_origin()
def add_pages():
    with open(new_pages_file, 'r') as file:
        label = file.read()


    with open(new_pages_file, 'w') as file:
        json.dump({}, file)

    return label


@app.route("/remove")
@cross_origin()
def remove_pages():
    with open(pages_for_removing_file, 'r') as file:
        label = file.read()

    with open(pages_for_removing_file, 'w') as file:
        json.dump({}, file)

    return label


if __name__ == "__main__":
    scheduler.add_job(id='notion_tracking task', func=notion_tracking, trigger='interval', seconds=120)
    scheduler.add_job(id='collect_pages_for_removing task', func=collect_pages_for_removing, trigger='interval',
                      seconds=10)
    scheduler.start()

    app.run(host='0.0.0.0')
