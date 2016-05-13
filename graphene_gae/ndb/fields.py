from google.appengine.ext import ndb
from graphene.core.exceptions import SkipField
from graphene.core.types.base import FieldType
from graphene.utils import to_snake_case
from graphene.relay import ConnectionField

from .types import NdbConnection

__author__ = 'ekampf'


class NdbConnectionField(ConnectionField):

    def __init__(self, *args, **kwargs):
        kwargs['connection_type'] = kwargs.pop('connection_type', NdbConnection)
        super(NdbConnectionField, self).__init__(*args, **kwargs)

    @property
    def model(self):
        return self.type._meta.model


class NdbKeyField(FieldType):
    def __init__(self, name, kind, *args, **kwargs):
        self.name = name
        self.kind = kind

        if 'resolver' not in kwargs:
            kwargs['resolver'] = self.default_resolver

        super(NdbKeyField, self).__init__(*args, **kwargs)

    def internal_type(self, schema):
        _type = self.get_object_type(schema)
        if not _type and self.parent._meta.only_fields:
            raise Exception(
                "Model %r is not accessible by the schema. "
                "You can either register the type manually "
                "using @schema.register. "
                "Or disable the field in %s" % (
                    self.model,
                    self.parent,
                )
            )

        if not _type:
            raise SkipField()

        return schema.T(_type)

    def get_object_type(self, schema):
        for _type in schema.types.values():
            type_model = hasattr(_type, '_meta') and getattr(_type._meta, 'model', None)
            if not type_model:
                continue

            if self.kind == type_model or self.kind == type_model.__name__:
                return _type

    def default_resolver(self, node, args, info):
        entity = node.instance
        key = getattr(entity, self.name)

        if isinstance(key, list):
            return self.__auto_resolve_repeated(entity, key)

        return self.__auto_resolve_key(entity, key)

    def __auto_resolve_repeated(self, entity, keys):
        if not self.name.endswith('_keys'):
            return ndb.get_multi(keys)

        cache_name = self.name[:-4]  # TODO: pluralise
        if hasattr(entity, cache_name):
            return getattr(entity, cache_name)

        values = ndb.get_multi(keys)
        setattr(entity, cache_name, values)
        return values

    def __auto_resolve_key(self, entity, key):
        if not self.name.endswith('_key'):
            return key.get()

        cache_name = self.name[:-4]
        if hasattr(entity, cache_name):
            return getattr(entity, cache_name)

        value = key.get()
        setattr(entity, cache_name, value)
        return value











