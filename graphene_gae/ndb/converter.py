from google.appengine.ext import ndb

from graphene.core.types.definitions import List
from graphene.core.types.scalars import String, Boolean, Int, Float
from graphene.core.types.custom_scalars import JSONString, DateTime

__author__ = 'ekampf'

def convert_ndb_scalar_property(graphene_type, ndb_prop):
    description = "%s %s property" % (ndb_prop._name, graphene_type)
    if ndb_prop._repeated:
        return graphene_type(description=description).List

    return graphene_type(description=description)


def convert_ndb_string_property(ndb_prop):
    return convert_ndb_scalar_property(String, ndb_prop)


def convert_ndb_boolean_property(ndb_prop):
    return convert_ndb_scalar_property(Boolean, ndb_prop)


def convert_ndb_int_property(ndb_prop):
    return convert_ndb_scalar_property(Int, ndb_prop)


def convert_ndb_float_property(ndb_prop):
    return convert_ndb_scalar_property(Float, ndb_prop)


def convert_ndb_json_property(ndb_prop):
    return JSONString()


def convert_ndb_datetime_property(ndb_prop):
    return DateTime()

converters = {
    ndb.StringProperty: convert_ndb_string_property,
    ndb.TextProperty: convert_ndb_string_property,
    ndb.BooleanProperty: convert_ndb_boolean_property,
    ndb.IntegerProperty: convert_ndb_int_property,
    ndb.FloatProperty: convert_ndb_float_property,
    ndb.JsonProperty: convert_ndb_json_property,
    ndb.DateProperty: convert_ndb_datetime_property,
    ndb.DateTimeProperty: convert_ndb_datetime_property
}

def convert_ndb_property(prop):
    converter_func = converters.get(type(prop))
    if converter_func:
        return converter_func(prop)

    return None
