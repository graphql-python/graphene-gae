import inspect
import six

from graphene import relay
from graphene.core.classtypes.objecttype import ObjectType, ObjectTypeMeta

from google.appengine.ext import ndb
from google.appengine.ext.db import BadArgumentError

from .options import NdbOptions

__author__ = 'ekampf'


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
        super(NdbObjectTypeMeta, cls).construct(*args, **kwargs)
        if not cls._meta.abstract:
            if not cls._meta.model:
                raise Exception('NdbObjectType %s must have a model in the Meta class attr' % cls)

            if not inspect.isclass(cls._meta.model) or not issubclass(cls._meta.model, ndb.Model):
                raise Exception('Provided model in %s is not an NDB model' % cls)

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

    def to_global_id(self):
        entity_id = self.key.id() if self.key else None
        return self.global_id(entity_id)

    @classmethod
    def get_node(cls, id, info=None):
        try:
            instance = cls._meta.model.get_by_id(id)
            return cls(instance)
        except cls._meta.model.DoesNotExist:
            return None

