import inspect
import six

from graphene import relay
from graphene.core.classtypes.objecttype import ObjectType, ObjectTypeMeta

from google.appengine.ext import ndb
from google.appengine.ext.db import BadArgumentError

from .options import NdbOptions

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


class NdbObjectTypeMeta(ObjectTypeMeta):
    options_class = NdbOptions

    def construct_fields(cls):
        from .converter import convert_ndb_property

        ndb_model = cls._meta.model

        only_fields = cls._meta.only_fields
        already_created_fields = {field.attname for field in cls._meta.local_fields}

        for prop_name, prop in ndb_model._properties.iteritems():
            name = prop._code_name

            is_not_in_only = only_fields and name not in only_fields
            is_already_created = name in already_created_fields
            is_excluded = name in cls._meta.exclude_fields or is_already_created
            if is_not_in_only or is_excluded:
                continue

            conversion_result = convert_ndb_property(prop, cls._meta)
            cls.add_to_class(conversion_result.name, conversion_result.field)

    def construct(cls, *args, **kwargs):
        cls = super(NdbObjectTypeMeta, cls).construct(*args, **kwargs)
        if not cls._meta.abstract:
            if not cls._meta.model:
                raise Exception('Ndb ObjectType %s must have a model in the Meta class attr' % cls)

            if not inspect.isclass(cls._meta.model) or not issubclass(cls._meta.model, ndb.Model):
                raise Exception('Provided model in %s is not an Ndb model' % cls)

            cls.construct_fields()
        return cls


class InstanceObjectType(ObjectType):
    class Meta:
        abstract = True

    def __init__(self, _root=None):
        super(InstanceObjectType, self).__init__(_root=_root)
        assert not self._root or isinstance(self._root, self._meta.model), (
            '{} received a non-compatible instance ({}) '
            'when expecting {}'.format(
                self.__class__.__name__,
                self._root.__class__.__name__,
                self._meta.model.__name__
            ))

    @property
    def instance(self):
        return self._root

    @instance.setter
    def instance(self, value):
        self._root = value


class NdbObjectType(six.with_metaclass(NdbObjectTypeMeta, InstanceObjectType)):
    class Meta:
        abstract = True


###################  Relay stuff


class NdbNodeMeta(NdbObjectTypeMeta, relay.types.NodeMeta):
    pass


class NdbNodeInstance(relay.types.Node, InstanceObjectType):
    class Meta:
        abstract = True


class NdbNode(six.with_metaclass(NdbNodeMeta, NdbNodeInstance)):
    class Meta:
        abstract = True

    @classmethod
    def get_node(cls, id, info=None):
        try:
            instance = cls._meta.model.get_by_id(id)
            return cls(instance)
        except cls._meta.model.DoesNotExist:
            return None


class NdbConnection(relay.types.Connection):
    @classmethod
    def from_list(cls, ndb_query, args, info):
        connection = connection_from_ndb_query(ndb_query, args, connection_type=cls, edge_type=cls.edge_type, pageinfo_type=relay.PageInfo)
        connection.set_connection_data(ndb_query)
        return connection
