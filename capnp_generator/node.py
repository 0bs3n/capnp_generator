import capnp
import pprint
from .rng import RNG

"""
For the top level schema, the list of all top-level defined structs, 
enums, consts, interfaces can be retrieved with schema.schema.node.nestedNodes.
This returns a list of DynamicStructReaders, and a handle to the actual
type can be acquired with `getattr(schema, <node>.name)`. The value returned
in this case will be of a specific type, one of:

    capnp.lib.capnp._EnumModule
    capnp.lib.capnp._StructModule
    capnp.lib.capnp.InterfaceModule
    some primitive python type for `const` values

a call to `type()` can be used to check against one of these types
(with a fallthrough for const), and decide how to handle the type
from there. Only a struct can be the root of a capnp message, and so
anything other than a struct is either something that will be used inside
one of the defined structs (i.e. an enum or another struct). As far as
I can tell, you'll never have a const or interface encoded in a capnp 
message - interfaces have to be used with an RPC mechanism, and consts
are just referenced in code that imports the schema.

For struct types, the list of fields can be accessed with 
<struct>.schema.fields. The type of a field can be 

For Enum types, the list of possible enumerants can be accessed from 
type.schema.enumerants, which is a python dict in the format 
{ enumerant_name: enumerant_value }
"""

class Node:
    def __init__(self, root_node):
        self.struct_names = []
        self.structs_by_name = {}
        self.structs_by_id = {}
        self.enum_names = []
        self.enums_by_name = {}
        self.enums_by_id = {}
        self.interface_names = []
        self.interfaces_by_name = {}
        self.interfaces_by_id = {}

        self.node = root_node
        
        for node in self.node.schema.node.nestedNodes:
            nodeSchema = getattr(self.node, node.name)
            if type(nodeSchema) == capnp.lib.capnp._StructModule:
                self.struct_names.append(node.name)
                self.structs_by_name[node.name] = nodeSchema
                self.structs_by_id[node.id] = nodeSchema
            elif type(nodeSchema) == capnp.lib.capnp._EnumModule:
                self.enum_names.append(node.name)
                self.enums_by_name[node.name] = nodeSchema
                self.enums_by_id[node.id] = nodeSchema
            elif type(nodeSchema) == capnp.lib.capnp._InterfaceModule:
                self.interface_names.append(node.name)
                self.interfaces_by_name[node.name] = nodeSchema
                self.interfaces_by_id[node.id] = nodeSchema
            else: # primitive type, const or so
                pass

    def __repr__(self):
        reprstr = ""
        reprstr += pprint.pformat(self.node.schema.node.to_dict())
        return reprstr

class RootNode(Node):
    def get_message_types(self):
        # The unit of communication in Cap'n Proto is a "message". A message is a tree of 
        # objects, with the root always being a struct.
        for structname in self.struct_names:
            print(structname)
        return self.structs_by_name

    def get_types(self):
        for structname in self.struct_names:
            print(structname)
        for enumname in self.enum_names:
            print(enumname)


class StructNode(Node):
    def __init__(self, node, root_node: RootNode, rng):
        super().__init__(node)
        self.root_node = root_node
        self.enums_by_id.update(self.root_node.enums_by_id)
        self.structs_by_id.update(self.root_node.structs_by_id)
        self.rng: RNG = rng
        self.types = { "struct": self.structs_by_id, "enum": self.enums_by_id }

    def enumerate_fields(self):
        return [field for field in self.node.schema.node.struct.fields]

    def _is_primitive_numerial_type(self, typestring):
        primtypes = [
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "int8",
            "int16",
            "int32",
            "int64",
            "float32",
            "float64",
            "bool"
        ]
        return typestring in primtypes

    def generate(self):
        msg = self.node.new_message()
        for field in self.enumerate_fields():
            self.generate_field(msg, field)
        return msg

    def generate_field(self, msg, field):
        typestring = self.get_type_for_field(field)
        if self._is_primitive_numerial_type(typestring):
            setattr(msg, field.name, self.rng.type_function_map[typestring]())
        elif typestring == "text":
            setattr(msg, field.name, self.rng.getText())
        elif typestring == "data":
            setattr(msg, field.name, self.rng.getBlob(10))
        elif typestring == "struct":
            nodeId = self.node.schema.node.id
            id = field.slot.type.struct.typeId
            if nodeId == id:
                # print("recursive structure - bailing on generation of field to avoid infinite loop")
                return
            typedef = self.structs_by_id[id]
            innerStruct = StructNode(typedef, self.root_node, self.rng)
            setattr(msg, field.name, innerStruct.generate())
        elif typestring == "list":
            length = self.rng.getRandom(0, 10)
            msg.init(field.name, length)
            setattr(msg, field.name, self.generate_list(field.slot.type, length))
            pass
        elif typestring == "enum":
            id = field.slot.type.enum.typeId
            typedef = self.enums_by_id[id]
            enumerants = list(typedef.schema.enumerants.keys())
            setattr(msg, field.name, self.rng.getEnum(enumerants))

    def generate_list(self, memberType, length):
        innerTypeString = list(memberType.list.elementType.to_dict().keys())[0]
        if self._is_primitive_numerial_type(innerTypeString):
            return self.rng.getList(innerTypeString, length)
        if innerTypeString == "struct" or innerTypeString == "enum":
            innerTypeId = getattr(memberType.list.elementType, innerTypeString).typeId
            innerType = self.types[innerTypeString][innerTypeId]
            if innerTypeString == "struct":
                return [StructNode(innerType, self.root_node, self.rng)
                        .generate() for _ in range(0, length)]
            elif innerTypeString == "enum":
                return [self.rng.getEnum(list(innerType.schema.enumerants.keys())) for _ in range(0, length)]
        if innerTypeString == "list":
            innerLength = self.rng.getRandom(0, 10)
            return [self.generate_list(memberType.list.elementType, innerLength) for _ in range(0, length)]
        if innerTypeString == "text":
            return [self.rng.getText() for _ in range(0, length)]
        if innerTypeString == "data":
            return [self.rng.getBlob(self.rng.getRandom(0, 10)) for _ in range(0, length)]

    def get_type_for_field(self, field) -> str:
        typestring = list(field.slot.type.to_dict().keys())[0]
        return typestring
