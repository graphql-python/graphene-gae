from functools import partial


from google.appengine.ext import ndb
from google.appengine.ext.db import BadArgumentError, Timeout

from graphql_relay.connection.connectiontypes import PageInfo, Edge
from graphene import relay, Argument, Boolean, Int, String, Field, Dynamic
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




# class NdbKeyStringField(Field):
#     def __init__(self, name, kind, *args, **kwargs):
#         self.name = name
#         self.kind = kind
#
#         if 'resolver' not in kwargs:
#             kwargs['resolver'] = self.default_resolver
#
#         if 'ndb' not in kwargs:
#             kwargs['ndb'] = Argument(Boolean(),
#                                      description="Return an NDB id (key.id()) instead of a GraphQL global id",
#                                      default=False)
#
#         super(NdbKeyStringField, self).__init__(*args, **kwargs)
#
#     def internal_type(self, schema):
#         _type = self.get_object_type(schema)
#         if not _type and self.parent._meta.only_fields:
#             raise Exception(
#                 "Model %r is not accessible by the schema. "
#                 "You can either register the type manually "
#                 "using @schema.register. "
#                 "Or disable the field in %s" % (
#                     self.kind,
#                     self.parent,
#                 )
#             )
#
#         if not _type:
#             raise SkipField()
#
#         from graphql import GraphQLString
#         return GraphQLString
#
#     def get_object_type(self, schema):
#         for _type in schema.types.values():
#             type_model = hasattr(_type, '_meta') and getattr(_type._meta, 'model', None)
#             if not type_model:
#                 continue
#
#             if self.kind == type_model or self.kind == type_model.__name__:
#                 return _type
#
#     def default_resolver(self, node, args, info):
#         entity = node.instance
#         key = getattr(entity, self.name)
#         if not key:
#             return None
#
#         is_global_id = not args.get('ndb', False)
#
#         if isinstance(key, list):
#             t = self.get_object_type(info.schema.graphene_schema)._meta.type_name
#             return [to_global_id(t, k.urlsafe()) for k in key] if is_global_id else [k.id() for k in key]
#
#         t = self.get_object_type(info.schema.graphene_schema)._meta.type_name
#         return to_global_id(t, key.urlsafe()) if is_global_id else key.id()


# class NdbKeyField(Field):
#     def __init__(self, name, kind, *args, **kwargs):
#         self.name = name
#         self.kind = kind
#
#         if 'resolver' not in kwargs:
#             kwargs['resolver'] = self.default_resolver
#
#         super(NdbKeyField, self).__init__(*args, **kwargs)
#
#     def internal_type(self, schema):
#         _type = self.get_object_type(schema)
#         if not _type and self.parent._meta.only_fields:
#             raise Exception(
#                 "Model %r is not accessible by the schema. "
#                 "You can either register the type manually "
#                 "using @schema.register. "
#                 "Or disable the field in %s" % (
#                     self.kind,
#                     self.parent,
#                 )
#             )
#
#         if not _type:
#             raise SkipField()
#
#         return schema.T(_type)
#
#     def get_object_type(self, schema):
#         for _type in schema.types.values():
#             type_model = hasattr(_type, '_meta') and getattr(_type._meta, 'model', None)
#             if not type_model:
#                 continue
#
#             if self.kind == type_model or self.kind == type_model.__name__:
#                 return _type
#
#     def default_resolver(self, node, args, info):
#         entity = node.instance
#         key = getattr(entity, self.name)
#
#         if isinstance(key, list):
#             entities = ndb.get_multi(key)
#             return entities
#
#         return key.get()
