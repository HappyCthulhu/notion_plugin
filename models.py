from app import db


class BaseModel(db.Model):
    __abstract__ = True

    title = db.Column('title', db.String())
    created_time = db.Column('created_time', db.DateTime, nullable=False)
    last_edited_time = db.Column('last_edited_time', db.DateTime, nullable=False)

    page_id = db.Column('page_id', db.Integer, primary_key=True)

    # интересно, зачем это нужно - без этого без работает вызов каждый перененной из экземпляра класса
    # def __init__(self, title, link, created_time, last_edited_time):
    #     self.title = title
    #     self.link = link
    #     self.created_time = created_time
    #     self.last_edited_time = last_edited_time
    #
    def __repr__(self):
        return f'page: {self.title}'


class AllNotionPages(BaseModel):
    __table_args__ = (
                         db.UniqueConstraint('link'),
                     ),
    __tablename__ = 'all_notion_pages'
    link = db.Column('link', db.String())
    db.UniqueConstraint(link, name='shit')


class NewNotionPages(BaseModel):
    __tablename__ = 'new_pages'
    link = db.Column('link', db.String(), unique=True, nullable=False)


class BookmarksForRemove(db.Model):
    __tablename__ = 'bookmarks_for_remove'

    bookmark_id = db.Column('bookmark_id', db.String(), unique=True, nullable=False)
    primary_id = db.Column('primary_id', db.Integer, primary_key=True)

    def __repr__(self):
        return f'bookmark_id: {self.bookmark_id}'
