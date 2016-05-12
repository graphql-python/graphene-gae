
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
