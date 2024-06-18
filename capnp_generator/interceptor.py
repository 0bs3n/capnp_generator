from node import StructNode



class Interceptor:
    # This class should take input capnp serialized messages, deserialize them
    # fiddle the contents in a type-aware way, reserialize, and output that data.
    def __init__(self, schema):
        self.schema = schema
        pass

    def tamper_serialized_bytes(self, type, data):
        typeInfo = getattr(self.schema, type)
        message = typeInfo.from_bytes(data)
        typeNode = StructNode(typeInfo)