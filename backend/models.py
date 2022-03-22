from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, DateTime, Integer
# from app import app
db = SQLAlchemy()
# ma = Marshmallow()

# наследует от db.Model, чтоб оно могло передать инфу в миграции
class BaseModel(db.Model):
    __abstract__ = True

    title = Column('title', String())
    created_time = Column('created_time', DateTime, nullable=False)
    last_edited_time = Column('last_edited_time', DateTime, nullable=False)

    page_id = Column('page_id', Integer, primary_key=True)

    # def __init__ не нужен
    def __repr__(self):
        return f'page: {self.title}'


class AllNotionPages(BaseModel):
    __tablename__ = 'all_notion_pages'
    link = Column('link', String(), unique=True, nullable=False)


class NewNotionPages(BaseModel):
    __tablename__ = 'new_pages'
    link = db.Column('link', String(), unique=True, nullable=False)


class BookmarksForRemove(db.Model):
    __tablename__ = 'bookmarks_for_remove'

    bookmark_id = Column('bookmark_id', String(), unique=True, nullable=False)
    primary_id = Column('primary_id', Integer, primary_key=True)

    def __repr__(self):
        return f'bookmark_id: {self.bookmark_id}'
