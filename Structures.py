from enum import Enum
from SylphTypes import *
from Tokeniser import Token, Tokeniser
from common import SylphError

@dataclass
class PreParseFunction:
    token: Token
    signiture: FunctionType

    argumentTokens: list[Token]

    bodyTokens: list[Token]

    def __str__(self) -> str:
        return self.token.rep + " " + str(self.signiture) + "(" + ", ".join([i.rep for i in self.argumentTokens]) + "):\n" + str(self.bodyTokens)

@dataclass
class Symbol:
    token: Token
    sylphType: SylphType

class FrameType(Enum):
    LocalScope = 0,
    GlobalScope = 1,
    FunctionScope = 2

class SymbolFrame:
    def __init__(self, typeDict: TypeDict, parent):
        self.symbols: dict[str, Symbol] = {}
        self.parent: SymbolFrame = parent
        self.typeDict = typeDict

    def getFrameType(self) -> FrameType:
        return FrameType.LocalScope

    def getGlobalFrame(self):
        return self.parent

    def getReturnType(self) -> SylphType:
        return self.parent.getReturnType()

    def createChildFrame(self):
        return SymbolFrame(self)

    def insert(self, symbol: Symbol):
        self.symbols[symbol.token.rep] = symbol
    
    def getSymbol(self, name: str) -> Symbol | None:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent is not None:
            return self.parent.getSymbol(name)
        return None
    
    def hasSymbol(self, name: str) -> bool:
        return self.getSymbol(name) is not None
    
    def getType(self, name: str) -> SylphType | None:
        if name in self.typeDict:
            return self.typeDict[name]
        return None
    
    def hasType(self, name: str) -> bool:
        return self.getType(name) is not None

class FunctionFrame(SymbolFrame):
    def __init__(self, typeDict: TypeDict, parent, returnType: SylphType):
        super().__init__(typeDict, parent)
        self.returnType = returnType
    
    def getFrameType(self) -> FrameType:
        return FrameType.FunctionScope

    def getReturnType(self) -> SylphType:
        return self.returnType

class GlobalFrame(SymbolFrame):
    def __init__(self, typeDict: TypeDict):
        super().__init__(typeDict, None)
        self.preParsedFunctions: dict[str, list[PreParseFunction]] = {}

    def getGlobalFrame(self) -> SymbolFrame:
        return self

    def getFrameType(self) -> FrameType:
        return FrameType.GlobalScope

    def createFunctionFrame(self, returnType: SylphType):
        return FunctionFrame(typeDict, self, returnType)

    def registerType(self, name: str, sylphType: SylphType):
        self.typeDict[name] = sylphType

    def registerFunction(self, preParseFunc: PreParseFunction):
        if not preParseFunc.token.rep in self.preParsedFunctions.keys():
            self.preParsedFunctions[preParseFunc.token.rep] = []
        self.preParsedFunctions[preParseFunc.token.rep].append(preParseFunc)
    
    def getFunctionsWithName(self, name: str) -> list[PreParseFunction]:
        if name in self.preParsedFunctions.keys():
            return self.preParsedFunctions[name]
        return []

MAXIMUM_ERROR_COUNT = 10

@dataclass
class ParseBrain:
    globalFrame: GlobalFrame
    tList: Tokeniser
    errors: list[SylphError]
