class Registry(object):

    def __init__(self):
        self._registry = {}

    def register(self, cls):
        from .types import NdbObjectType
        assert issubclass(cls, NdbObjectType), (
            'Only classes of type NdbObjectType can be registered, ',
            'received "{}"'
        ).format(cls.__name__)
        assert cls._meta.registry == self, 'Registry for a Model have to match.'
        self._registry[cls._meta.model] = cls

    def get_type_for_model(self, model):
        return self._registry.get(model)

    def get_type_for_model_name(self, model_name):
        for ndb_model, type in self._registry.items():
            if ndb_model.__name__ == model_name:
                return type


registry = None


def get_global_registry():
    global registry
    if not registry:
        registry = Registry()
    return registry


def reset_global_registry():
    global registry
    registry = None
