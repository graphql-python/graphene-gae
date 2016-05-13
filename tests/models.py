from google.appengine.ext import ndb

__author__ = 'ekampf'


class Author(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()


class Tag(ndb.Model):
    name = ndb.StringProperty()


class Comment(ndb.Model):
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
    body = ndb.StringProperty()


class Article(ndb.Model):
    headline = ndb.StringProperty()
    summary = ndb.StringProperty()
    body = ndb.TextProperty()
    keywords = ndb.StringProperty(repeated=True)

    author_key = ndb.KeyProperty(kind='Author')
    tags = ndb.KeyProperty(Tag, repeated=True)

    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
