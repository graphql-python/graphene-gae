from google.appengine.ext import ndb
from google.appengine.ext.db import BadArgumentError

from graphene import relay
from graphene.core.exceptions import SkipField
from graphene.core.types.base import FieldType

__author__ = 'ekampf'


def connection_from_ndb_query(query, args={}, connection_type=None,
                              edge_type=None, pageinfo_type=None, **kwargs):
    '''
    A simple function that accepts an ndb Query and used ndb QueryIterator object(https://cloud.google.com/appengine/docs/python/ndb/queries#iterators)
    to returns a connection object for use in GraphQL.
    It uses array offsets as pagination,
    so pagination will only work if the array is static.
    '''
    connection_type = connection_type or relay.Connection
    edge_type = edge_type or relay.Edge
    pageinfo_type = pageinfo_type or relay.PageInfo

    full_args = dict(args, **kwargs)
    first = full_args.get('first')
    after = full_args.get('after')
    has_previous_page = bool(after)
    start_cursor = ndb.Cursor(urlsafe=after) if after else None

    iter = query.iter(produce_cursors=True, start_cursor=start_cursor, batch_size=10)

    page_size = first if first else 10
    edges = []
    while len(edges) < page_size:
        try:
            entity = iter.next()
        except StopIteration:
            break

        edge = edge_type(node=entity, cursor=iter.cursor_after().urlsafe())
        edges.append(edge)

    try:
        end_cursor = iter.cursor_after().urlsafe()
    except BadArgumentError:
        end_cursor = None

    # Construct the connection
    return connection_type(
        edges=edges,
        page_info=pageinfo_type(
            start_cursor=start_cursor.urlsafe() if start_cursor else '',
            end_cursor=end_cursor,
            has_previous_page=has_previous_page,
            has_next_page=iter.has_next()
        )
    )


class NdbConnection(relay.types.Connection):
    @classmethod
    def from_list(cls, ndb_query, args, info):
        connection = connection_from_ndb_query(ndb_query, args, connection_type=cls, edge_type=cls.edge_type, pageinfo_type=relay.PageInfo)
        connection.set_connection_data(ndb_query)
        return connection


class NdbConnectionField(relay.ConnectionField):
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
