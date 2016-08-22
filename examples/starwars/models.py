from google.appengine.ext import ndb

__author__ = 'ekampf'


class Character(ndb.Model):
    name = ndb.StringProperty()

    def __str__(self):
        return self.name


class Faction(ndb.Model):
    name = ndb.StringProperty()
    hero_key = ndb.KeyProperty(kind=Character)

    def __str__(self):
        return self.name


class Ship(ndb.Model):
    name = ndb.StringProperty()
    faction_key = ndb.KeyProperty(kind=Faction)

    def __str__(self):
        return self.name

