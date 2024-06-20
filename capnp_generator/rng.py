import random
import struct
import sys
import math

special_values = [ '<','>', '?', '>', ')', '(', '*', '&', '^', '%', '$', '#', '@', '/', '-', '+', '?', '~', '`', '|', '\\' ]
chars = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0x3d, 0x3f, 0x40, 0x41, 0x7f, 0x80, 0x81, 0xfe, 0xff ]
shorts = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0x3f, 0x40, 0x41, 0x7f, 0x80, 0x81, 0xff, 0x100, 0x101, 0x3fff, 0x4000, 0x4001, 0x7fff, 0x8000, 0x8001, 0xffff ]
ints = [ 0,1,2,3,4,5,6,7,8,9,10,11,0x3f, 0x40, 0x41, 0x7f, 0x80, 0x81,  0xff, 0x100, 0x101, 0x3fff, 0x4000, 0x4001, 0x7fff, 0x8000, 0x8001, 0xffff, 0x10000, 0x10001, 0x3fffffff, 0x40000000, 0x40000001, 0x7fffffff, 0x80000000, 0x80000001, 0xffffffff ]
qwords = [ 0,1,2,3,4,5,6,7,8,9,10,11,0x3f, 0x40, 0x41, 0x7f, 0x80, 0x81,  0xff, 0x100, 0x101, 0x3fff, 0x4000, 0x4001, 0x7fff, 0x8000, 0x8001, 0xffff, 0x10000, 0x10001, 0x3fffffff, 0x40000000, 0x40000001, 0x7fffffff, 0x80000000, 0x80000001, 0xffffffff, 0x100000000, 0x100000001, 0x3fffffffffffffff, 0x4000000000000000, 0x4000000000000001, 0x7fffffffffffffff, 0x8000000000000000, 0x8000000000000001, 0xffffffffffffffff ]
floats = [float('inf'), float('-inf'), float('nan'), 0.0, -0.0, sys.float_info.min, -sys.float_info.min, sys.float_info.max, -sys.float_info.max, math.ulp(0.0)]

class RNG:
    def __init__(self, seed, step, reseed_cb=None, logger=None):
        self.seed = seed
        self.iterations = 0
        self.step = step
        random.seed(seed)
        self.reseed_cb = reseed_cb
        self.type_function_map = {
            "uint8":   self.getUInt8,
            "uint16":  self.getUInt16,
            "uint32":  self.getUInt32,
            "uint64":  self.getUInt64,
            "int8":    self.getInt8,
            "int16":   self.getInt16,
            "int32":   self.getInt32,
            "int64":   self.getInt64,
            "float32": self.getFloat32,
            "float64": self.getFloat64,
            "bool":    self.getBool
        }
        self.typestring_to_elem_size = {
            "uint8":   1,
            "uint16":  2,
            "uint32":  4,
            "uint64":  8,
            "int8":    1,
            "int16":   2,
            "int32":   4,
            "int64":   8,
            "float32": 4,
            "float64": 8,
            "bool":    -1
        }

    def set_seed(self, seed):
        self.seed = seed
        self.iterations = 0
        random.seed(seed)

    def reset(self, seed):
        self.set_seed(seed)
        if self.reseed_cb is not None:
            self.reseed_cb()
        if self.logger is not None:
            self.logger.info(f"RNG hit defined step count {self.step} at {self.iterations} iterations, reseeding with {seed} and resetting")

    def _twos_comp(self, val, mask, size):
        if ((val & mask) & (1 << (size - 1))):
            val = (val ^ mask) + 1
            return -val
        else:
            return val

    def advance(self):
        self.iterations += 1
        if self.iterations >= self.step:
            self.reset(self.getRandom(0, 0xffffffffffffffff))
            # print here maybe, to notify of the iteration count and new seed

    def getBool(self):
        return True if random.randint(0, 1) == 1 else False

    def getInt8(self):
        switch = self.getRandom(0, 2)
        if switch == 0:
            val = ord(special_values[self.getRandom(0, len(special_values) - 1)])
        elif switch == 1:
            val = chars[self.getRandom(0, len(chars) - 1)]
        else:
            val = self.getRandom(0, 0xff)
        return self._twos_comp(val, 0xff, 8)

    def getUInt8(self):
        switch = self.getRandom(0, 2)
        if switch == 0:
            val = ord(special_values[self.getRandom(0, len(special_values) - 1)])
        elif switch == 1:
            val = chars[self.getRandom(0, len(chars) - 1)]
        else:
            val = self.getRandom(0, 0xff)
        return val

    def getInt16(self):
        switch = self.getRandom(0, 3)
        if switch == 0:
            val = ord(special_values[self.getRandom(0, len(special_values) - 1)])
        elif switch == 1:
            val = chars[self.getRandom(0, len(chars) - 1)]
        elif switch == 2:
            val = shorts[self.getRandom(0, len(chars) - 1)]
        else:
            val = self.getRandom(0, 0xffff)
        return self._twos_comp(val, 0xffff, 16)

    def getUInt16(self):
        switch = self.getRandom(0, 3)
        if switch == 0:
            val = ord(special_values[self.getRandom(0, len(special_values) - 1)])
        elif switch == 1:
            val = chars[self.getRandom(0, len(chars) - 1)]
        elif switch == 2:
            val = shorts[self.getRandom(0, len(shorts) - 1)]
        else:
            val = self.getRandom(0, 0xffff)
        return val

    def getInt32(self):
        switch = self.getRandom(0, 4)
        if switch == 0:
            val = ord(special_values[self.getRandom(0, len(special_values) - 1)])
        elif switch == 1:
            val = chars[self.getRandom(0, len(chars) - 1)]
        elif switch == 2:
            val = shorts[self.getRandom(0, len(shorts) - 1)]
        elif switch == 3:
            val = ints[self.getRandom(0, len(ints) - 1)]
        else:
            val = self.getRandom(0, 0xffffffff)
        return self._twos_comp(val, 0xffffffff, 32)

    def getUInt32(self):
        switch = self.getRandom(0, 4)
        if switch == 0:
            val = ord(special_values[self.getRandom(0, len(special_values) - 1)])
        elif switch == 1:
            val = chars[self.getRandom(0, len(chars) - 1)]
        elif switch == 2:
            val = shorts[self.getRandom(0, len(shorts) - 1)]
        elif switch == 3:
            val = ints[self.getRandom(0, len(ints) - 1)]
        else:
            val = self.getRandom(0, 0xffffffff)
        return val

    def getInt64(self):
        switch = self.getRandom(0, 5)
        if switch == 0:
            val = ord(special_values[self.getRandom(0, len(special_values) - 1)])
        elif switch == 1:
            val = chars[self.getRandom(0, len(chars) - 1)]
        elif switch == 2:
            val = shorts[self.getRandom(0, len(shorts) - 1)]
        elif switch == 3:
            val = ints[self.getRandom(0, len(ints) - 1)]
        elif switch == 4:
            val = qwords[self.getRandom(0, len(qwords) - 1)]
        else:
            val = self.getRandom(0, 0xffffffffffffffff)
        return self._twos_comp(val, 0xffffffffffffffff, 64)

    def getUInt64(self):
        switch = self.getRandom(0, 5)
        if switch == 0:
            val = ord(special_values[self.getRandom(0, len(special_values) - 1)])
        elif switch == 1:
            val = chars[self.getRandom(0, len(chars) - 1)]
        elif switch == 2:
            val = shorts[self.getRandom(0, len(shorts) - 1)]
        elif switch == 3:
            val = ints[self.getRandom(0, len(ints) - 1)]
        elif switch == 4:
            val = qwords[self.getRandom(0, len(qwords) - 1)]
        else:
            val = self.getRandom(0, 0xffffffffffffffff)
        return val

    def getFloat32(self):
        switch = self.getRandom(0, 2)
        if switch == 0:
            val = floats[self.getRandom(0, len(floats) - 1)]
        elif switch == 1:
            val = self.getInt32()
        else:
            val = self.getRandom(0, 0xffffffff)
        return val

    def getFloat64(self):
        switch = self.getRandom(0, 2)
        if switch == 0:
            val = floats[self.getRandom(0, len(floats) - 1)]
        elif switch == 1:
            val = self.getInt64()
        else:
            val = self.getRandom(0, 0xffffffffffffffff)
        return val

    def getRandom(self, minimum: int, maximum: int):
        return random.randint(minimum, maximum)

    def getEnum(self, options):
        return options[random.randint(0, len(options) - 1)]

    def mutBool(self):
        return self.getBool()

    def mutInt8(self, d):
        return struct.unpack("B", self._mutate_bytes(struct.pack("B", d))[0])
    
    def mutInt16(self, d):
        return struct.unpack("<H", self._mutate_bytes(struct.pack("<H", d))[0])
    
    def mutInt32(self, d):
        return struct.unpack("<I", self._mutate_bytes(struct.pack("<I", d))[0])
    
    def mutInt64(self, d):
        return struct.unpack("<Q", self._mutate_bytes(struct.pack("<Q", d))[0])

    def mutFloat32(self, d):
        return self.mutInt32(d)

    def mutFloat64(self, d):
        return self.mutInt64(d)
    
    def getList(self, typestring, length=None):
        # maximum length for lists is encoded in a 29 bit field.
        # the length is interpreted differently depending on the
        # list pointer pointing at the list, but the largest
        # possible interpretation of the size field is size in
        # 64 bit words (though could be smaller, including size
        # in bits for bools and other 1 bit types).
        # 
        # Default elem size is 1 for simplicity.

        output = []
        getFunc = self.type_function_map[typestring]

        if length is None:
            length = random.randint(0, int((2**29)) - 1)

        for i in range(0, length):
            output.append(getFunc())

        return output

    def getBlob(self, length=None):
        return bytes(self.getList("uint8", length=length))
    
    def getText(self, length=None, byte_list=None):
        count = 0
        output = b""
        if length == None:
            length = random.randint(0, 10)

        if length == 0:
            return b""

        length = length - 1
        while count < length:
            if length - count < 4:
                codepoint = self._random_utf8(length - count)
            else:
                codepoint = self._random_utf8(random.randint(1, 4))
            output += codepoint
            count += len(codepoint)
        
        output += b"\x00"
        return output.decode("utf-8")

    def _random_utf8(self, size=4):
        if size == 1:
            val = random.randint(0, 0x7f)
        elif size == 2:
            val = random.randint(0x80, 0x7ff)
        elif size == 3:
            val = random.randint(0x800, 0xffff)
            # Account for utf-16 surrogate ranges. Should we bother? or just let it happen
            while ((0xd800 <= val) and (val <= 0xdfff)):
                val = random.randint(0x800, 0xffff)
        elif size == 4:
            val = random.randint(0x10000, 0x10fffe)
        else:
            val = random.randint(0x0, 0x10fffe) 

        if val < 0x80:
            return bytes([val])
        elif val < 0x0800:
            byte1 = ((val & 0x07c0) >> 6) | 0xC0
            byte2 =  (val & 0x003f)       | 0x80
            return bytes([byte1, byte2])
        elif val < 0x10000:
            byte1 = ((val & 0xf000) >> 12) | 0xe0
            byte2 = ((val & 0x0fc0) >> 6)  | 0x80
            byte3 =  (val & 0x003f)        | 0x80
            return bytes([byte1, byte2, byte3])
        elif val < 0x10ffff:
            byte1 = ((val & 0x1c0000) >> 18) | 0xf0
            byte2 = ((val & 0x03f000) >> 12) | 0x80
            byte3 = ((val & 0x000fc0) >> 6)  | 0x80
            byte4 =  (val & 0x00003f)        | 0x80
            return bytes([byte1, byte2, byte3, byte4])

    def _mutate_bytes(self, data, prob_byte=0.1, prob_bit=1):
        data = list(data)
        out = []
        for b in data:
            if random.random() < prob_byte:
                mask = 0
                for p in range(0, 8):
                    if random.randint(1, 8) < prob_bit:
                        mask |= 1 << p
                b ^= mask 
            out.append(b)
        return bytes(out)
