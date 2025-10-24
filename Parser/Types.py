from Types import *
from Scanner.Tokens import *
from Parser.TokenList import TokenList
from typing import Dict

@dataclass
class FunctionSigniture:
    # We may have more than one thing here later!
    tags: List[TagType]
    argumentTypes: List[SylphType]
    returnType: SylphType

    def getFnPtrType(self):
        return FunctionPtr(self.argumentTypes, self.returnType)


TypeDict = Dict[str, SylphType]

@Core.orError
def parseType(types: TypeDict, tList: TokenList) -> SylphType | Core.CompileError:
    # No sum, ptr or arrays allowed
    def parseSingularType(types: TypeDict, tList: TokenList) -> SylphType:
        if tList.peekType() == TT.OpenBracket:
            openBracketToken = tList.get()
            # Assume its a func ptr until you do or don't get ->
            parsedTypes: List[SylphType] = []
            while tList.peekType() != TT.CloseBracket:
                if len(parsedTypes) > 0:
                    tList.expect(TT.Comma)
                parsedTypes.append(parseType(types, tList))
                if isinstance(parsedTypes[-1], Core.CompileError):
                    raise parsedTypes[-1]
                
            tList.expect(TT.CloseBracket)
            if tList.peekStr() != "->":
                if len(parsedTypes) == 1:
                    return parsedTypes[0]
                else:
                    raise Core.CompileError(
                        "Expected ->, found " + tList.peekStr() + " (multiple types in bracket, did you want a function pointer?)", 
                        openBracketToken.location)
            tList.get()
            returnType = parseType(types, tList)
            if isinstance(returnType, Core.CompileError):
                raise returnType
            return FunctionPtr(parsedTypes, returnType)
        # Should be as simple as a type name
        foundID, typeName = tList.match(TT.Identifier)
        foundType = foundID
        if foundID:
            if not typeName.string in types.keys():
                foundType = False
            #else
            return types[typeName.string]
        if not foundType:
            raise Core.CompileError("Expected a type, found \"" + tList.peek().string + "\"", tList.peek().location)
    # End def parseSingularType
    
    def parseNonSumType(types: TypeDict, tList: TokenList) -> SylphType:
        builtType = parseSingularType(types, tList)

        getting_additions = True
        while getting_additions:
            match tList.peek():
                case Token(TT.Keyword, Keywords.Ptr):
                    builtType = PtrType(builtType, False, None)
                    tList.get()
                case Token(TT.OpenBrace):
                    tList.get()
                    iLiteral = tList.expect(TT.Literal)
                    if iLiteral.detail != LiteralType.IntLit:
                        raise Core.CompileError("Expected int literal for length of array, found " + iLiteral.string, iLiteral.location)
                    tList.expect(TT.CloseBrace)
                    builtType = PtrType(builtType, True, int(iLiteral.string))
                case _:
                    getting_additions = False
        return builtType

    pType = parseNonSumType(types, tList)
    isSumType = False
    lookingForSumType = True

    while lookingForSumType:
        if tList.peekStr() == "or":
            tList.get()
            nextType = parseNonSumType(types, tList)
            if isSumType:
                pType.options.append(nextType)
            else:
                isSumType = True
                pType = SumType([pType, nextType])
        else:
            lookingForSumType = False
    return pType


@dataclass
class Symbol:
    token: Token
    type: SylphType
    location: Core.CompileError

# TODO: Because of how things are rn, functions aren't symbols
# so you can't use them as identifiers :/
class SymbolFrame:
    
    def __init__(self, parent):
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.module = None if parent is None else parent.module

    def getModule(self):
        return self.module

    def get(self, name: str) -> Symbol | None:
        if name in self.symbols.keys():
            return self.symbols[name]
        elif self.parent is not None:
            return self.parent.get(name)
        return None
    
    def add(self, symbol: Symbol):
        self.symbols[symbol.token.string] = symbol
