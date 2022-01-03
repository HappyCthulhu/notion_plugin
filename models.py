from app import db


class BaseModel(db.Model):
    __abstract__ = True

    title = db.Column('title', db.String())
    link = db.Column('link', db.String())
    created_time = db.Column('created_time', db.DateTime)
    last_edited_time = db.Column('last_edited_time', db.DateTime)

    page_id = db.Column('page_id', db.Integer, primary_key=True)

    # интересно, зачем это нужно - без этого без работает вызов каждый перененной из экземпляра класса
    # def __init__(self, title, link, created_time, last_edited_time):
    #     self.title = title
    #     self.link = link
    #     self.created_time = created_time
    #     self.last_edited_time = last_edited_time
    #
    def __repr__(self):
        return self.title


class AllNotionPages(BaseModel):
    __tablename__ = 'all_notion_pages'


class NewNotionPages(BaseModel):
    __tablename__ = 'new_pages'


class BookmarksForRemove(db.Model):
    __tablename__ = 'bookmarks_for_remove'

    bookmark_id = db.Column('bookmark_id', db.String())
    primary_id = db.Column('primary_id', db.Integer, primary_key=True)

    def __repr__(self):
        return f'bookmark_id: {self.bookmark_id}'
