from dataclasses import dataclass
from typing import List

# How big is a pointer
ARCH_PTR_SIZE = 8

# TODO: All sorts of stuff to check which type gets a free cast and to compare if two types are equal

class SylphType:
    def getSize(self):
        pass

class BaseType(SylphType):
    pass

@dataclass
class IntType(BaseType):
    unsigned: bool
    sizeBytes: int
    def getSize(self):
        return self.sizeBytes

@dataclass
class FloatType(BaseType):
    double: bool
    def getSize(self):
        return 8 if self.double else 4

class BoolType(BaseType):
    def getSize(self):
        return 1

# Under the hood its just a pointer
class StringType(BaseType):
    def getSize(self):
        return ARCH_PTR_SIZE

class NullType(BaseType):
    # Now... I really hope 0 makes sense
    def getSize(self):
        return 0

@dataclass
class PtrType(SylphType):
    ptrOf: SylphType
    isArray: bool
    length: int | None
    def getSize(self):
        if self.isArray:
            return self.ptrOf.getSize() * self.length
        return ARCH_PTR_SIZE

@dataclass
class FunctionPtr(SylphType):
    argumentTypes: List[SylphType]
    returnType: SylphType
    def getSize(self):
        return ARCH_PTR_SIZE

@dataclass
class SumType(SylphType):
    options: List[SylphType]
    # Largest option, plus one 8 bit tag of what the type is rn
    def getSize(self):
        return max([i.getSize() for i in self.options]) + 1
