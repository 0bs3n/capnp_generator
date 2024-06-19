import sys
from node import StructNode, RootNode
from rng import RNG
import capnp

schema = capnp.load(sys.argv[1], imports=[
    # This is jank to deal with a wonky environment, but I'll leave it
    # in case anyone runs into a similar issue. If you see something like
    # `Import failed: /capnp/c++.capnp`
    # when you try to run your program, you need to specify the include path
    # that has the missing import here in this list. Otherwise
    # you can just call `capnp.load("<capnp file>")`.
    "/home/ethansh/venv/lib/python3.8/site-packages/", 
    "/home/ethansh/interfaces/src/resources/"
    ]
)

# If instead of a root schema file, you have a python module path,
# you can import it like this instead:
#
# import importlib
# importlib.import_module("path.to.module_capnp")

# in this example, the type to be fuzzed and RNG seed are supplied via cli arguments
typeName = sys.argv[2]
seed = int(sys.argv[3], 0)

# you must load in the capnp file that defines the type you want to generate into a RootNode
root_node = RootNode(schema)

# Seed the RNG engine
rng = RNG(seed, 1000)

# instantiate a node for the type you'd like to generate a message 
# for, the top level type you'll send. Arguments are the capnp type
# for the struct, the root node (i.e. the RootNode above representing the
# file that contains your type), and the RNG engine
person_node = StructNode(root_node.structs_by_name[typeName], root_node, rng)

# Call generate to randomly generate all fields in the struct and output 
# a capnp message ready for serialization or whatever
for i in range(0, 10):
    msg = person_node.generate()
    print(msg)

# you can override specific fields if desired. For
# types defined in the same file your root node is
# derived from, you can do it as below:
# birthdate = schema.Date.new_message()
# birthdate.year = 1994
# birthdate.day = 12
# birthdate.month = 3
# msg.birthdate = birthdate

# if you need to override an imported type,
# you'll need to either load it and access the schema
# here (which might not work because the root node will
# have already capnp.load'ed it and you'll get an error)
# or just use dict/string syntax for structs/enums:
# msg.birthdate = { "year": 1, "month": 2, "day": 3}

#print(msg)


# From here act on the message as normal, send it wherever it's meant to go
serialized = msg.to_bytes_packed()
open("/tmp/test.out", "wb").write(serialized)
