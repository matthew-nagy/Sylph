from common import *
from dataclasses import dataclass
from Tokeniser import *

POINTER_SIZE = 8
LIBRARY_STRING_SIZE = 8

class SylphType:
    def getByteSize(self) -> int:
        pass

    def canIndex(self) -> bool:
        return False

    def canCall(self) -> bool:
        return False

class IndexableType(SylphType):
    def canIndex(self) -> bool:
        return True

@dataclass
class IntType(SylphType):
    numOfBits: int
    signed: bool
    def getByteSize(self) -> int:
        return int(self.numOfBits / 8)

@dataclass
class FloatType(SylphType):
    numOfBits: int
    def getByteSize(self) -> int:
        return int(self.numOfBits / 8)

@dataclass
class BoolType(SylphType):
    def getByteSize(self) -> int:
        return 1
        
@dataclass
class ByteType(SylphType):
    def getByteSize(self) -> int:
        return 1

@dataclass
class StringType(SylphType):
    def getByteSize(self) -> int:
        return LIBRARY_STRING_SIZE

@dataclass
class NoneType(SylphType):
    # ... I sure hope that 0 isn't an issue here
    def getByteSize(self) -> int:
        return 0

@dataclass
class FunctionType(SylphType):
    returnType: SylphType
    argumentTypes: list[SylphType]

    def canCall(self)->bool:
        return True

@dataclass
class PointerType(IndexableType):
    pointeeType: SylphType
    def getByteSize(self) -> int:
        return POINTER_SIZE

@dataclass
class ErrorType(SylphType):
    pass

TypeDict = dict[str, SylphType]

# This will be harder once there are sum types...
# TODO: Function pointers!
@orError
def parseType(tList: Tokeniser, typeDict: TypeDict) -> SylphType | SylphError:
    startToken = tList.expect([TokenType.Identifier, TokenType.NoneLiteral])
    if startToken.ttype == TokenType.NoneLiteral:
        return NoneType()
    
    if not startToken.rep in typeDict.keys():
        raise SylphError(startToken.sourceInfo, ErrorType.ExpectedType)
    
    returnType = typeDict[startToken.rep]

    while tList.peekType() == TokenType.Ptr:
        returnType = PointerType(returnType)
        tList.next()
    
    return returnType

