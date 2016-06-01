from google.appengine.ext import ndb

__author__ = 'ekampf'


class Address(ndb.Model):
    address1 = ndb.StringProperty()
    address2 = ndb.StringProperty()
    city = ndb.StringProperty()


class PhoneNumber(ndb.Model):
    area = ndb.StringProperty()
    number = ndb.StringProperty()


class Author(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    addresses = ndb.LocalStructuredProperty(Address, repeated=True)
    mobile = ndb.LocalStructuredProperty(PhoneNumber)


class Tag(ndb.Model):
    name = ndb.StringProperty()


class Comment(ndb.Model):
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)
    body = ndb.StringProperty()


class Article(ndb.Model):
    headline = ndb.StringProperty(required=True)
    summary = ndb.StringProperty()
    body = ndb.TextProperty()
    body_hash = ndb.ComputedProperty(lambda self: self.calc_body_hash())
    keywords = ndb.StringProperty(repeated=True)

    author_key = ndb.KeyProperty(kind='Author')
    tags = ndb.KeyProperty(Tag, repeated=True)

    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def calc_body_hash(self):
        import hashlib
        return hashlib.md5(self.body).hexdigit() if self.body else None

