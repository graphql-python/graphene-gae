from collections import namedtuple

import inflect
from google.appengine.ext import ndb

from graphene.core.types.scalars import String, Boolean, Int, Float
from graphene.core.types.custom_scalars import JSONString, DateTime
from graphene_gae.ndb.fields import NdbKeyField

__author__ = 'ekampf'

ConversionResult = namedtuple('ConversionResult', ['name', 'field'])

p = inflect.engine()

def convert_ndb_scalar_property(graphene_type, ndb_prop):
    description = "%s %s property" % (ndb_prop._name, graphene_type)
    if ndb_prop._repeated:
        return graphene_type(description=description).List

    return graphene_type(description=description)


def convert_ndb_string_property(ndb_prop, meta):
    return convert_ndb_scalar_property(String, ndb_prop)


def convert_ndb_boolean_property(ndb_prop, meta):
    return convert_ndb_scalar_property(Boolean, ndb_prop)


def convert_ndb_int_property(ndb_prop, meta):
    return convert_ndb_scalar_property(Int, ndb_prop)


def convert_ndb_float_property(ndb_prop, meta):
    return convert_ndb_scalar_property(Float, ndb_prop)


def convert_ndb_json_property(ndb_prop, meta):
    return JSONString()


def convert_ndb_datetime_property(ndb_prop, meta):
    return DateTime()


def convert_ndb_key_propety(ndb_key_prop, meta):
    remove_key_suffix = meta.remove_key_property_suffix if meta else True

    name = ndb_key_prop._code_name
    if remove_key_suffix:
        if name.endswith('_key'):
            name = name[:-4]

        if name.endswith('_keys'):
            name = name[:-5]
            name = p.plural(name)

    field = NdbKeyField(ndb_key_prop._code_name, ndb_key_prop._kind)
    if ndb_key_prop._repeated:
        field = field.List

    return ConversionResult(name=name, field=field)


converters = {
    ndb.StringProperty: convert_ndb_string_property,
    ndb.TextProperty: convert_ndb_string_property,
    ndb.BooleanProperty: convert_ndb_boolean_property,
    ndb.IntegerProperty: convert_ndb_int_property,
    ndb.FloatProperty: convert_ndb_float_property,
    ndb.JsonProperty: convert_ndb_json_property,
    ndb.DateProperty: convert_ndb_datetime_property,
    ndb.DateTimeProperty: convert_ndb_datetime_property,
    ndb.KeyProperty: convert_ndb_key_propety
}

def convert_ndb_property(prop, meta=None):
    converter_func = converters.get(type(prop))
    if not converter_func:
        raise Exception("Don't know how to convert NDB field %s (%s)" % (prop._code_name, prop))

    result = converter_func(prop, meta)
    if not result:
        raise Exception("Failed to convert NDB field %s (%s)" % (prop._code_name, prop))

    if isinstance(result, ConversionResult):
        return result

    return ConversionResult(name=prop._code_name, field=result)
