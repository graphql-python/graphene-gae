from collections import namedtuple

import inflect

from google.appengine.ext import ndb

from graphene import String, Boolean, Int, Float, List, NonNull, Field, Dynamic
from graphene.types.json import JSONString
from graphene.types.datetime import DateTime

from .fields import DynamicNdbKeyStringField, DynamicNdbKeyReferenceField

__author__ = 'ekampf'

ConversionResult = namedtuple('ConversionResult', ['name', 'field'])


p = inflect.engine()


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def convert_ndb_scalar_property(graphene_type, ndb_prop, **kwargs):
    kwargs['description'] = "%s %s property" % (ndb_prop._name, graphene_type)
    _type = graphene_type

    if ndb_prop._repeated:
        _type = List(_type)

    if ndb_prop._required:
        _type = NonNull(_type)

    return Field(_type, **kwargs)


def convert_ndb_string_property(ndb_prop):
    return convert_ndb_scalar_property(String, ndb_prop)


def convert_ndb_boolean_property(ndb_prop):
    return convert_ndb_scalar_property(Boolean, ndb_prop)


def convert_ndb_int_property(ndb_prop):
    return convert_ndb_scalar_property(Int, ndb_prop)


def convert_ndb_float_property(ndb_prop):
    return convert_ndb_scalar_property(Float, ndb_prop)


def convert_ndb_json_property(ndb_prop):
    return Field(JSONString, description=ndb_prop._name)


def convert_ndb_datetime_property(ndb_prop):
    return Field(DateTime, description=ndb_prop._name)


def convert_ndb_key_propety(ndb_key_prop):
    """
    Two conventions for handling KeyProperties:
    #1.
        Given:
            store_key = ndb.KeyProperty(...)

        Result is 2 fields:
            store_id  = graphene.String() -> resolves to store_key.urlsafe()
            store     = NdbKeyField()     -> resolves to entity

    #2.
        Given:
            store = ndb.KeyProperty(...)

        Result is 2 fields:
            store_id = graphene.String() -> resolves to store_key.urlsafe()
            store     = NdbKeyField()    -> resolves to entity

    """
    is_repeated = ndb_key_prop._repeated
    name = ndb_key_prop._code_name

    if name.endswith('_key') or name.endswith('_keys'):
        # Case #1 - name is of form 'store_key' or 'store_keys'
        string_prop_name = rreplace(name, '_key', '_id', 1)
        resolved_prop_name = name[:-4] if name.endswith('_key') else p.plural(name[:-5])
    else:
        # Case #2 - name is of form 'store'
        singular_name = p.singular_noun(name) if p.singular_noun(name) else name
        string_prop_name = singular_name + '_ids' if is_repeated else singular_name + '_id'
        resolved_prop_name = name

    return [
        ConversionResult(name=string_prop_name, field=DynamicNdbKeyStringField(ndb_key_prop)),
        ConversionResult(name=resolved_prop_name, field=DynamicNdbKeyReferenceField(ndb_key_prop))
    ]


def convert_local_structured_property(ndb_structured_property):
    is_required = ndb_structured_property._required
    is_repeated = ndb_structured_property._repeated
    model = ndb_structured_property._modelclass
    name = ndb_structured_property._code_name

    def dynamic_type():
        from .types import NdbObjectTypeMeta
        _type = NdbObjectTypeMeta.REGISTRY.get(model.__name__)
        if not _type:
            return None

        if is_repeated:
            _type = List(_type)

        if is_required:
            _type = NonNull(_type)

        return Field(_type)

    field = Dynamic(dynamic_type)
    return ConversionResult(name=name, field=field)


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
    ndb.KeyProperty: convert_ndb_key_propety,
    ndb.StructuredProperty: convert_local_structured_property,
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

    if isinstance(field, (list, ConversionResult,)):
        return field

    return ConversionResult(name=prop._code_name, field=field)

