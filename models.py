from flask_server import db


class AllNotionPages(db.Model):
    pages_id = db.Column('pages_id', db.Integer, primary_key=True)
    title = db.Column('title', db.String())
    link = db.Column('link', db.String())
    created_time =  db.Column('created_time', db.DateTime)
    last_edited_time = db.Column('last_edited_time', db.DateTime)

    # интересно, зачем это нужно - без этого без работает вызов каждый перененной из экземпляра класса
    def __init__(self, title, link, created_time, last_edited_time):
        self.title = title
        self.link = link
        self.created_time = created_time
        self.last_edited_time = last_edited_time

    def __repr__(self):
        return f'Page "{self.title}"'

