from Scanner.Tokens import *
from enum import Enum
from Types import *
from typing import Dict, List
import Core
from Parser.TokenList import TokenList
from Parser.Types import *

@dataclass
class CollectedFunction:
    signiture: FunctionSigniture

    # TODO: Having only one arg token and one def list means no pattern matching
    argTokens: List[Token]
    definition: List[Token]

class StructureModule:

    def __init__(self):
        self.types: TypeDict = StructureModule.getGlobalTypes()
        # TODO: Only one collected function here means no overloading
        self.functions: Dict[str, CollectedFunction] = {}

    def isFunctionWithArity(self, name: str, arity: int) -> bool:
        if name in self.functions.keys():
            return len(self.functions[name].signiture.argumentTypes) == arity
        return False

    @staticmethod
    # TODO: Support half width floating points? Fixed point? (For snes lmao)
    def getGlobalTypes() -> TypeDict:
        return {
            "i8": IntType(False, 1), "i16": IntType(False, 2), "i32": IntType(False, 4), "i64": IntType(False, 8),
            "u8": IntType(True, 1), "u16": IntType(True, 2), "u32": IntType(True, 4), "u64": IntType(True, 8),
            "float": FloatType(False), "double": FloatType(True),
            "bool": BoolType(), "string": StringType(), "Null": NullType(), 
        }

@Core.orError
def parseTypedef(types: TypeDict, tList: TokenList):
    tList.expect(Keywords.Using)
    newTypeName = tList.get()
    tList.expect("=")
    parsedTypeOrError = parseType(types, tList)
    if isinstance(parsedTypeOrError, Core.CompileError):
        raise parsedTypeOrError
    types[newTypeName.string] = parsedTypeOrError
    return None

# TODO: No forward declaration (not that you need it)
@Core.orError
def parseFunc(module: StructureModule, tList: TokenList, tags: List[Token] = []):
    tList.expect(Keywords.Func)
    nameToken = tList.expect(TT.Identifier)
    tList.expect(TT.OpenBracket)

    argTokens: List[Token] = []
    argTypes: List[SylphType] = []

    while tList.peekType() != TT.CloseBracket:
        if len(argTokens) > 0:
            tList.expect(TT.Comma)
        argTokens.append(tList.expect(TT.Identifier))
        tList.expect(TT.Colon)
        argType = parseType(module.types, tList)
        if isinstance(argType, Core.CompileError):
            raise argType
        argTypes.append(argType)
    tList.expect(TT.CloseBracket)

    returnType = NullType()

    if True in tList.match("->"):
        rtOrError = parseType(module.types, tList)
        if isinstance(rtOrError, Core.CompileError):
            raise rtOrError
        returnType = rtOrError
    
    contentsTokens: List[Token] = []
    # Get the contents of the function
    if tList.peekStr() == "=":
        tList.get()
        lineLoc = tList.peek().location.line_number
        while tList.peek().location.line_number == lineLoc:
            contentsTokens.append(tList.get())
    else:
        # TODO: This could be split up into a block grabbing thing
        startingCurly = tList.expect(TT.OpenCurly)
        depth = 1
        while depth > 0:
            token = tList.get()
            if token.location.source_name != startingCurly.location.source_name:
                raise Core.CompileError("Unexpected EOF while parsing definition for function \"" + nameToken.string + "\"", startingCurly.location)
            if token.ttype == TT.OpenCurly:
                depth += 1
            elif token.ttype == TT.CloseCurly:
                depth -= 1
            
            if depth > 0:
                contentsTokens.append(token)
    
    module.functions[nameToken.string] = CollectedFunction(FunctionSigniture(tags, argTypes, returnType), argTokens, contentsTokens)
    return None

@Core.orError
def parseTaggedFunc(module: StructureModule, tList: TokenList):
    tags: List[TagType] = []
    while tList.peekType() == TT.Tag:
        tags.append(tList.get().detail)
    match tList.peekTypeSubtype():
        case [TT.Keyword, Keywords.Func]:
            if x := parseFunc(module, tList, tags):
                raise x
        case _:
            raise Core.CompileError("")


def StructurePass(tokens: List[Token]) -> tuple[bool, StructureModule | List[Core.CompileError]]:

    tList = TokenList(tokens)
    module = StructureModule()
    errors: List[Core.CompileError] = []
    si = tList.peek().location

    # Error Contingency
    def EC(value: None | Core.CompileError):
        if value is not None:
            errors.append(value)
            tList.panic(si.line_number)

    while tList.hasTokens() and len(errors) < Core.MAX_ERRORS:
        si = tList.peek().location
        match tList.peekTypeSubtype():
            case [TT.Keyword, Keywords.Using]:
                EC(parseTypedef(module.types, tList))
            case [TT.Keyword, Keywords.Func]:
                EC(parseFunc(module, tList))
            case [TT.Tag, _]:
                EC(parseTaggedFunc(module, tList))
            case _:
                errors.append(Core.CompileError("Unexpected token found at top level \"" + str(tList.peek().string) +"\"", tList.peek().location))
                tList.panic()
    
    if len(errors) > 0:
        return False, errors
    return True, module


