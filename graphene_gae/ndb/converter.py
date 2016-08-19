from collections import namedtuple

import inflect
from google.appengine.ext import ndb

from graphene import String, Boolean, Int, Float, List, NonNull, Field
from graphene.types.json import JSONString
from graphene.types.datetime import DateTime
# from graphene_gae.ndb.fields import NdbKeyField, NdbKeyStringField

__author__ = 'ekampf'

p = inflect.engine()


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def convert_ndb_scalar_property(graphene_type, ndb_prop, **kwargs):
    description = "%s %s property" % (ndb_prop._name, graphene_type)
    result = graphene_type(description=description, **kwargs)
    if ndb_prop._repeated:
        result = List(result)

    if ndb_prop._required:
        result = NonNull(result)

    return result


def convert_ndb_string_property(ndb_prop):
    return convert_ndb_scalar_property(String, ndb_prop)


def convert_ndb_boolean_property(ndb_prop):
    return convert_ndb_scalar_property(Boolean, ndb_prop)


def convert_ndb_int_property(ndb_prop):
    return convert_ndb_scalar_property(Int, ndb_prop)


def convert_ndb_float_property(ndb_prop):
    return convert_ndb_scalar_property(Float, ndb_prop)


def convert_ndb_json_property(ndb_prop):
    return JSONString(description=ndb_prop._name)


def convert_ndb_datetime_property(ndb_prop):
    return DateTime(description=ndb_prop._name)


# def convert_ndb_key_propety(ndb_key_prop):
#     """
#     Two conventions for handling KeyProperties:
#     #1.
#         Given:
#             store_key = ndb.KeyProperty(...)
#
#         Result is 2 fields:
#             store_id  = graphene.String() -> resolves to store_key.urlsafe()
#             store     = NdbKeyField()     -> resolves to entity
#
#     #2.
#         Given:
#             store = ndb.KeyProperty(...)
#
#         Result is 2 fields:
#             store_id = graphene.String() -> resolves to store_key.urlsafe()
#             store     = NdbKeyField()     -> resolves to entity
#
#     """
#     name = ndb_key_prop._code_name
#
#     if name.endswith('_key') or name.endswith('_keys'):
#         # Case #1 - name is of form 'store_key' or 'store_keys'
#         string_prop_name = rreplace(name, '_key', '_id', 1)
#         resolved_prop_name = name[:-4] if name.endswith('_key') else p.plural(name[:-5])
#     else:
#         # Case #2 - name is of form 'store'
#         singular_name = p.singular_noun(name) if p.singular_noun(name) else name
#         string_prop_name = singular_name + '_ids' if ndb_key_prop._repeated else singular_name + '_id'
#         resolved_prop_name = name
#
#     string_field = NdbKeyStringField(name, ndb_key_prop._kind)
#     resolved_field = NdbKeyField(name, ndb_key_prop._kind)
#
#     if ndb_key_prop._repeated:
#         string_field = string_field.List
#         resolved_field = resolved_field.List
#
#     if ndb_key_prop._required:
#         string_field = string_field.NonNull
#         resolved_field = resolved_field.NonNull
#
#     return [
#         string_field,
#         resolved_field
#     ]
#

def convert_local_structured_property(ndb_structured_prop):
    is_required = ndb_structured_prop._required
    is_repeated = ndb_structured_prop._repeated
    model = ndb_structured_prop._modelclass
    name = ndb_structured_prop._code_name

    t = LazyType(model.__name__ + 'Type')
    if is_repeated:
        l = List(t)
        return ConversionResult(name=name, field=l.NonNull if is_required else l)

    return ConversionResult(name=name, field=Field(t))


def convert_computed_property(ndb_computed_prop):
    return convert_ndb_scalar_property(String, ndb_computed_prop)


converters = {
    ndb.StringProperty: convert_ndb_string_property,
    ndb.TextProperty: convert_ndb_string_property,
    ndb.BooleanProperty: convert_ndb_boolean_property,
    ndb.IntegerProperty: convert_ndb_int_property,
    ndb.FloatProperty: convert_ndb_float_property,
    ndb.JsonProperty: convert_ndb_json_property,
    ndb.DateProperty: convert_ndb_datetime_property,
    ndb.DateTimeProperty: convert_ndb_datetime_property,
    # ndb.KeyProperty: convert_ndb_key_propety,
    ndb.LocalStructuredProperty: convert_local_structured_property,
    ndb.ComputedProperty: convert_computed_property
}


def convert_ndb_property(prop):
    converter_func = converters.get(type(prop))
    if not converter_func:
        raise Exception("Don't know how to convert NDB field %s (%s)" % (prop._code_name, prop))

    field = converter_func(prop)
    if not field:
        raise Exception("Failed to convert NDB propeerty to a GraphQL field %s (%s)" % (prop._code_name, prop))

    return field
