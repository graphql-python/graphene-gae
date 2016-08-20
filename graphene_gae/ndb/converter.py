from collections import namedtuple

import inflect
from graphql_relay import to_global_id

from google.appengine.ext import ndb

from graphene import String, Boolean, Int, Float, List, NonNull, Field, Dynamic, Argument
from graphene.types.json import JSONString
from graphene.types.datetime import DateTime
# from graphene_gae.ndb.fields import NdbKeyStringField #, NdbKeyField

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
    is_required = ndb_key_prop._required
    model = ndb_key_prop._kind
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

    def dynamic_type_key_string_prop():
        from .types import NdbObjectTypeMeta
        if not NdbObjectTypeMeta.REGISTRY.get(model):
            return None

        global_type_name = NdbObjectTypeMeta.REGISTRY[model].__name__

        _type = String
        if is_repeated:
            _type = List(_type)

        if is_required:
            _type = NonNull(_type)

        def resolve(entity, args, *_):
            is_global_id = not args.get('ndb', False)
            key = ndb_key_prop._get_user_value(entity)
            if isinstance(key, list):
                return [to_global_id(global_type_name, k.urlsafe()) for k in key] if is_global_id else [k.id() for k in key]

            return to_global_id(global_type_name, key.urlsafe()) if is_global_id else key.id()

        return Field(
            _type,
            resolver=resolve,
            args={'ndb': Argument(Boolean, False, description="Return an NDB id (key.id()) instead of a GraphQL global id")}
        )

    def dynamic_type_key_prop():
        from .types import NdbObjectTypeMeta
        _type = NdbObjectTypeMeta.REGISTRY.get(model)
        if not _type:
            return None

        if is_repeated:
            _type = List(_type)

        if is_required:
            _type = NonNull(_type)

        def resolve(entity, *_):
            key = ndb_key_prop._get_user_value(entity)
            if isinstance(key, list):
                return ndb.get_multi(key)

            return key.get()

        return Field(_type, resolver=resolve)

    return [
        ConversionResult(name=string_prop_name, field=Dynamic(dynamic_type_key_string_prop)),
        ConversionResult(name=resolved_prop_name, field=Dynamic(dynamic_type_key_prop))
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

