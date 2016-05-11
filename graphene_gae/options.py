from graphene.core.classtypes.objecttype import ObjectTypeOptions
from graphene.relay.types import Node
from graphene.relay.utils import is_node

VALID_ATTRS = ('model', 'only_fields', 'exclude_fields')

class NdbOptions(ObjectTypeOptions):

    def __init__(self, *args, **kwargs):
        super(NdbOptions, self).__init__(*args, **kwargs)
        self.model = None
        self.valid_attrs += VALID_ATTRS
        self.only_fields = None
        self.exclude_fields = []
        self.filter_fields = None
        self.filter_order_by = None

    def contribute_to_class(self, cls, name):
        super(NdbOptions, self).contribute_to_class(cls, name)
        if is_node(cls):
            self.exclude_fields = list(self.exclude_fields) + ['id']
            self.interfaces.append(Node)
