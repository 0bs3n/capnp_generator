import capnp
import pprint
import os
import sys
import site
import importlib
import capnp.includes
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

                # Here we need to do recursive checking for scoped types within structs.
                # Each type identified in that way should be added to the *_by_id object etc.
                # for the parent, and bubbled up eventually to the root
                nestedNode = Node(nodeSchema)
                self.struct_names.extend(nestedNode.struct_names)
                self.structs_by_name.update(nestedNode.structs_by_name)
                self.structs_by_id.update(nestedNode.structs_by_id)

                self.enum_names.extend(nestedNode.enum_names)
                self.enums_by_name.update(nestedNode.enums_by_name)
                self.enums_by_id.update(nestedNode.enums_by_id)

                self.interface_names.extend(nestedNode.interface_names)
                self.interfaces_by_name.update(nestedNode.interfaces_by_name)
                self.interfaces_by_id.update(nestedNode.interfaces_by_id)

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
    def __init__(self, node):
        super().__init__(node)
        capnp.lib.capnp.cleanup_global_schema_parser()
        self.set_imports()
        for node in self.imports:
            self.struct_names.extend(node.struct_names)
            self.structs_by_name.update(node.structs_by_name)
            self.structs_by_id.update(node.structs_by_id)

            self.enum_names.extend(node.enum_names)
            self.enums_by_name.update(node.enums_by_name)
            self.enums_by_id.update(node.enums_by_id)

            self.interface_names.extend(node.interface_names)
            self.interfaces_by_name.update(node.interfaces_by_name)
            self.interfaces_by_id.update(node.interfaces_by_id)

    def set_imports(self):
        self.imports_by_name = {}
        self.imports = []
        raw_data_file = open(self.node.__file__, "r")
        raw_data = raw_data_file.readlines()
        raw_data_file.close()
        import_lines = [line for line in raw_data if line.startswith("using")]
        for importline in import_lines:
            # print(importline)
            if "import" not in importline:
                continue
            import_name = importline.split(" ")[1]
            import_path = importline.split("\"")[1]
            if import_path.startswith("/capnp/"):
                continue
            if "/" in import_path:
                import_path = import_path[1:]

                import_path = import_path.replace("/", ".").replace(".capnp", "_capnp")
                import_node = RootNode(importlib.import_module(import_path))
            else:
                import_path = os.path.join(os.path.dirname(self.node.__file__), import_path)
                sys.path.append("/usr/local/include")
                USER_SITE_PACKAGES = [site.getusersitepackages()]
                GLOBAL_SITE_PACKAGES = site.getsitepackages()
                CAPNP_LIBRARY_SEARCH_PATH = USER_SITE_PACKAGES + GLOBAL_SITE_PACKAGES + sys.path
                import_node = RootNode(capnp.load(import_path, imports=CAPNP_LIBRARY_SEARCH_PATH))

                # print(sys.path)
                # import_path = os.path.join(sys.path, import_path)
            # else:
                # import_path = os.path.join(os.path.dirname(self.node.__file__), import_path)

            # sys.path.append("/usr/local/include")
            # USER_SITE_PACKAGES = [site.getusersitepackages()]
            # GLOBAL_SITE_PACKAGES = site.getsitepackages()
            # CAPNP_LIBRARY_SEARCH_PATH = USER_SITE_PACKAGES + GLOBAL_SITE_PACKAGES + sys.path
            # import_node = RootNode(capnp.load(import_path, imports=CAPNP_LIBRARY_SEARCH_PATH))

            self.imports.append(import_node)
            self.imports_by_name[import_name] = import_node


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
        # print(self.node.schema.node)

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

    def generate_field(self, msg, field, original_field=None):
        fieldname = field.name
        if self.is_union_field(field):
            original_field = field
            field = self.choose_union_type(field)
            # TODO: figure out why this fails with some unions
            try:
                getattr(msg, fieldname)
            except Exception as e:
                return
            self.generate_field(getattr(msg, fieldname), field, original_field)
            return
        typestring = self.get_type_for_field(field)
        if self._is_primitive_numerial_type(typestring):
            setattr(msg, fieldname, self.rng.type_function_map[typestring]())
        elif typestring == "text":
            setattr(msg, fieldname, self.rng.getText())
        elif typestring == "data":
            setattr(msg, fieldname, self.rng.getBlob(10))
        elif typestring == "struct":
            nodeId = self.node.schema.node.id
            id = field.slot.type.struct.typeId
            if nodeId == id:
                # print("recursive structure - bailing on generation of field to avoid infinite loop")
                return

            # for s in self.structs_by_id:
                # print(self.structs_by_id[s].schema.node)
            typedef = self.structs_by_id[id]
            innerStruct = StructNode(typedef, self.root_node, self.rng)
            inner_msg = innerStruct.generate()
            # Extreme jank below, this is here to accomodate imported structs, unions, and unions 
            # that contain imported structs. I do not know why the second try is necessary, or why
            # the redundant except that just does the original thing makes it work, reading this code,
            # the second except should never be reached (as it would have worked the first time), but
            # you can remove it and try it yourself if you don't believe me, it breaks unless its
            # there.
            try:
                setattr(msg, fieldname, inner_msg.to_dict())
            except capnp.lib.capnp.KjException as e:
                if "isSetInUnion" in e.message:
                    try:
                        setattr(msg, fieldname, inner_msg)
                    except capnp.lib.capnp.KjException as e:
                        setattr(msg, fieldname, inner_msg.to_dict())
                else:
                    raise e
        elif typestring == "list":
            length = self.rng.getRandom(0, 10)
            # msg.init(fieldname, length)
            self.generate_list(msg, field, length)
            pass
        elif typestring == "enum":
            id = field.slot.type.enum.typeId
            typedef = self.enums_by_id[id]
            enumerants = list(typedef.schema.enumerants.keys())
            setattr(msg, fieldname, self.rng.getEnum(enumerants))

    def generate_list(self, msg, field, length):
        memberType = field.slot.type
        innerTypeString = list(memberType.list.elementType.to_dict().keys())[0]
        if self._is_primitive_numerial_type(innerTypeString):
            setattr(msg, field.name, self.rng.getList(innerTypeString, length))
        if innerTypeString == "struct" or innerTypeString == "enum":
            innerTypeId = getattr(memberType.list.elementType, innerTypeString).typeId
            innerType = self.types[innerTypeString][innerTypeId]
            if innerTypeString == "struct":
                l = msg.init(field.name, length)
                structs = [StructNode(innerType, self.root_node, self.rng).generate() for _ in range(0, length)]
                self.set_structs_in_array(l, structs, length)
                # IF it is a list of structs, and the struct type that makes up the elements
                # contains a list as one of its fields, then those list fields must be
                # manually initialized. This must be recursive.
                for i, elem in enumerate(l):
                    for f in elem.schema.node.struct.fields:
                        nested_struct_field_type = self.get_type_for_field(f)
                        if nested_struct_field_type == "list":
                            innerLength = len(getattr(structs[i], f.name))
                            inner_l = elem.init(f.name, innerLength)
                            self.set_structs_in_array(inner_l, getattr(structs[i], f.name), innerLength)


            elif innerTypeString == "enum":
                setattr(msg, field.name, [self.rng.getEnum(list(innerType.schema.enumerants.keys())) for _ in range(0, length)])
        if innerTypeString == "list":
            innerLength = self.rng.getRandom(0, 10)
            # TODO
            # setattr(msg, field.name, [self.generate_list(msg, field, innerLength) for _ in range(0, length)])
            setattr(msg, field.name, [])
        if innerTypeString == "text":
            setattr(msg, field.name, [self.rng.getText() for _ in range(0, length)])
        if innerTypeString == "data":
            setattr(msg, field.name, [self.rng.getBlob(self.rng.getRandom(0, 10)) for _ in range(0, length)])

    def set_structs_in_array(self, d, s, length):
        for i in range(length):
            for key in d[i].to_dict().keys():
                setattr(d[i], key, getattr(s[i], key))


    def is_union_field(self, field):
        try:
            field.slot.type
        except capnp.lib.capnp.KjException as e:
            if "isSetInUnion" in e.message:
                return True 
            else:
                raise e
        return False

    def choose_union_type(self, field):
        options = self.node.schema.fields[field.name].schema.node.struct.fields
        return options[self.rng.getRandom(0, len(options) - 1)]

    def get_type_for_field(self, field) -> str:
        typestring = list(field.slot.type.to_dict().keys())[0]
        return typestring
