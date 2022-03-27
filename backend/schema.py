from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field

from backend.models import NewNotionPages, BookmarksForRemove, AllNotionPages

# marshmello должен быть иницианизирован после sql_alchemy
ma = Marshmallow()


class NewPagesSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = NewNotionPages

    # auto_value -  тоже самое, что и auto_field. auto_value от другого класса наследуется, не от SQLAlchemyAutoSchema) и SQLAlchemyAutoSchema. Чтоб не приходилось прописывать значение полей, чтоб оно само это делало
    link = auto_field(dump_only=True)
    title = auto_field(dump_only=True)


# TODO: добавить class AllNotionPages():


class BookmarksSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = BookmarksForRemove

    class BookmarksForRemove():
        id = auto_field(dump_only=True, required=True)


class AllNotionPagesSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AllNotionPages

    link = auto_field(dump_only=True)
    title = auto_field(dump_only=True)
