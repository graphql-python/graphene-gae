import inspect
from collections import OrderedDict

from google.appengine.ext import ndb

from graphene import Field, ID  # , annotate, ResolveInfo
from graphene.relay import Connection, Node
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from graphene.types.utils import yank_fields_from_attrs

from .converter import convert_ndb_property
from .registry import Registry, get_global_registry


__author__ = 'ekampf'


def fields_for_ndb_model(ndb_model, registry, only_fields, exclude_fields):
    ndb_fields = OrderedDict()
    for prop_name, prop in ndb_model._properties.iteritems():
        name = prop._code_name

        is_not_in_only = only_fields and name not in only_fields
        is_excluded = name in exclude_fields  # or name in already_created_fields
        if is_not_in_only or is_excluded:
            continue

        results = convert_ndb_property(prop, registry)
        if not results:
            continue

        if not isinstance(results, list):
            results = [results]

        for r in results:
            ndb_fields[r.name] = r.field

    return ndb_fields


class NdbObjectTypeOptions(ObjectTypeOptions):
    model = None  # type: Model
    registry = None  # type: Registry
    connection = None  # type: Type[Connection]
    id = None  # type: str


class NdbObjectType(ObjectType):
    class Meta:
        abstract = True

    ndb_id = ID(resolver=lambda entity, *_: str(entity.key.id()))

    @classmethod
    def __init_subclass_with_meta__(cls, model=None, registry=None, skip_registry=False,
                                    only_fields=(), exclude_fields=(), connection=None,
                                    use_connection=None, interfaces=(), **options):

        if not model:
            raise Exception((
                'NdbObjectType {name} must have a model in the Meta class attr'
            ).format(name=cls.__name__))

        if not inspect.isclass(model) or not issubclass(model, ndb.Model):
            raise Exception((
                'Provided model in {name} is not an NDB model'
            ).format(name=cls.__name__))

        if not registry:
            registry = get_global_registry()

        assert isinstance(registry, Registry), (
            'The attribute registry in {} needs to be an instance of '
            'Registry, received "{}".'
        ).format(cls.__name__, registry)

        ndb_fields = fields_for_ndb_model(model, registry, only_fields, exclude_fields)
        ndb_fields = yank_fields_from_attrs(
            ndb_fields,
            _as=Field,
        )

        if use_connection is None and interfaces:
            use_connection = any((issubclass(interface, Node) for interface in interfaces))

        if use_connection and not connection:
            # We create the connection automatically
            connection = Connection.create_type('{}Connection'.format(cls.__name__), node=cls)

        if connection is not None:
            assert issubclass(connection, Connection), (
                "The connection must be a Connection. Received {}"
            ).format(connection.__name__)

        _meta = NdbObjectTypeOptions(cls)
        _meta.model = model
        _meta.registry = registry
        _meta.fields = ndb_fields
        _meta.connection = connection

        super(NdbObjectType, cls).__init_subclass_with_meta__(_meta=_meta, interfaces=interfaces, **options)

        if not skip_registry:
            registry.register(cls)

    @classmethod
    def is_type_of(cls, root, info):
        if isinstance(root, cls):
            return True

        if not isinstance(root, ndb.Model):
            raise Exception(('Received incompatible instance "{}".').format(root))

        # Returns True if `root` is a PolyModel subclass and `cls` is in the
        # class hierarchy of `root` which is retrieved with `_class_key`
        if hasattr(root, '_class_key') and cls._meta.model._get_kind() in root._class_key():
            return True

        return type(root) == cls._meta.model

    @classmethod
    def get_node(cls, info, urlsafe_key):
        try:
            key = ndb.Key(urlsafe=urlsafe_key)
        except:
            return None

        model = cls._meta.model
        assert key.kind() == model.__name__
        return key.get()

    @classmethod
    def resolve_id(cls, entity, info):
        return entity.key.urlsafe()
