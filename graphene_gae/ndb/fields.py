from functools import partial
import six

from google.appengine.ext import ndb
from google.appengine.ext.db import BadArgumentError, Timeout

from graphql_relay import to_global_id
from graphql_relay.connection.connectiontypes import Edge
from graphene import relay, Argument, Boolean, Int, String, Field, List, NonNull, Dynamic
from graphene.relay.connection import PageInfo

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
    edge_type = edge_type or Edge
    pageinfo_type = pageinfo_type or PageInfo

    full_args = dict(args, **kwargs)
    first = full_args.get('first')
    after = full_args.get('after')
    has_previous_page = bool(after)
    keys_only = full_args.get('keys_only', False)
    batch_size = full_args.get('batch_size', 20)
    page_size = first if first else full_args.get('page_size', 20)
    start_cursor = ndb.Cursor(urlsafe=after) if after else None

    ndb_iter = query.iter(produce_cursors=True, start_cursor=start_cursor, batch_size=batch_size, keys_only=keys_only, projection=query.projection)

    timeouts = 0
    edges = []
    while len(edges) < page_size:
        try:
            entity = ndb_iter.next()
        except StopIteration:
            break
        except Timeout:
            timeouts += 1
            if timeouts > 2:
                break

            continue

        if keys_only:
            # entity is actualy an ndb.Key and we need to create an empty entity to hold it
            entity = edge_type._meta.fields['node']._type._meta.model(key=entity)

        edge = edge_type(node=entity, cursor=ndb_iter.cursor_after().urlsafe())
        edges.append(edge)

    try:
        end_cursor = ndb_iter.cursor_after().urlsafe()
    except BadArgumentError:
        end_cursor = None

    # Construct the connection
    return connection_type(
        edges=edges,
        page_info=pageinfo_type(
            start_cursor=start_cursor.urlsafe() if start_cursor else '',
            end_cursor=end_cursor,
            has_previous_page=has_previous_page,
            has_next_page=ndb_iter.has_next()
        )
    )


class NdbConnectionField(relay.ConnectionField):
    def __init__(self, type, *args, **kwargs):
        super(NdbConnectionField, self).__init__(
            type,
            *args,
            keys_only=Boolean(),
            batch_size=Int(),
            page_size=Int(),
            **kwargs
        )

    @property
    def model(self):
        return self.type._meta.node._meta.model

    @staticmethod
    def connection_resolver(resolver, connection, model, root, args, context, info):
        ndb_query = resolver(root, args, context, info)
        if ndb_query is None:
            ndb_query = model.query()

        return connection_from_ndb_query(
            ndb_query,
            args=args,
            connection_type=connection,
            edge_type=connection.Edge,
            pageinfo_type=PageInfo
        )

    def get_resolver(self, parent_resolver):
        return partial(self.connection_resolver, parent_resolver, self.type, self.model)


class DynamicNdbKeyStringField(Dynamic):
    def __init__(self, ndb_key_prop, *args, **kwargs):
        kind = ndb_key_prop._kind

        def get_type():
            from .types import NdbObjectTypeMeta
            kind_name = kind if isinstance(kind, six.string_types) else kind.__name__

            if not NdbObjectTypeMeta.REGISTRY.get(kind_name):
                return None

            global_type_name = NdbObjectTypeMeta.REGISTRY[kind_name].__name__
            return NdbKeyStringField(ndb_key_prop, global_type_name)

        super(DynamicNdbKeyStringField, self).__init__(
            get_type,
            *args, **kwargs
        )


class DynamicNdbKeyReferenceField(Dynamic):
    def __init__(self, ndb_key_prop, *args, **kwargs):
        kind = ndb_key_prop._kind

        def get_type():
            from .types import NdbObjectTypeMeta
            kind_name = kind if isinstance(kind, six.string_types) else kind.__name__
            _type = NdbObjectTypeMeta.REGISTRY.get(kind_name)
            if not _type:
                return None

            return NdbKeyReferenceField(ndb_key_prop, _type)

        super(DynamicNdbKeyReferenceField, self).__init__(
            get_type,
            *args, **kwargs
        )


class NdbKeyStringField(Field):
    def __init__(self, ndb_key_prop, graphql_type_name, *args, **kwargs):
        self.__ndb_key_prop = ndb_key_prop
        self.__graphql_type_name = graphql_type_name
        is_repeated = ndb_key_prop._repeated
        is_required = ndb_key_prop._required

        _type = String
        if is_repeated:
            _type = List(_type)

        if is_required:
            _type = NonNull(_type)

        kwargs['args'] = {
            'ndb': Argument(Boolean, False, description="Return an NDB id (key.id()) instead of a GraphQL global id")
        }

        super(NdbKeyStringField, self).__init__(_type, *args, **kwargs)

    def resolve_key_to_string(self, entity, args, context, info):
        is_global_id = not args.get('ndb', False)
        key_value = self.__ndb_key_prop._get_user_value(entity)
        if not key_value:
            return None

        if isinstance(key_value, list):
            return [to_global_id(self.__graphql_type_name, k.urlsafe()) for k in key_value] if is_global_id else [k.id() for k in key_value]

        return to_global_id(self.__graphql_type_name, key_value.urlsafe()) if is_global_id else key_value.id()

    def get_resolver(self, parent_resolver):
        return self.resolve_key_to_string


class NdbKeyReferenceField(Field):
    def __init__(self, ndb_key_prop, graphql_type, *args, **kwargs):
        self.__ndb_key_prop = ndb_key_prop
        self.__graphql_type = graphql_type
        is_repeated = ndb_key_prop._repeated
        is_required = ndb_key_prop._required

        _type = self.__graphql_type
        if is_repeated:
            _type = List(_type)

        if is_required:
            _type = NonNull(_type)

        super(NdbKeyReferenceField, self).__init__(_type, *args, **kwargs)

    def resolve_key_reference(self, entity, args, context, info):
        key_value = self.__ndb_key_prop._get_user_value(entity)
        if not key_value:
            return None

        if isinstance(key_value, list):
            return ndb.get_multi(key_value)

        return key_value.get()

    def get_resolver(self, parent_resolver):
        return self.resolve_key_reference


