from Parser.StructurePass import StructureModule, CollectedFunction
import Parser.AST as AST
from Parser.Types import *
from Parser.TypeParser import *
from typing import Tuple

NodeAndSuccess = tuple[AST.Node | None, bool]
ErrorList = List[Core.CompileError]

def parser(func):
    def inner(tList: TokenList, types: TypeDict, symbolFrame: SymbolFrame, errors: ErrorList) -> NodeAndSuccess:
        try:
            res = func(tList, types, symbolFrame, errors)
            return res
        except Core.CompileError as cError:
            errors.append(cError)
            tList.panic()
            return None, False
    return inner

@parser
def parseBlock(tList: TokenList, types: TypeDict, symbolFrame: SymbolFrame, errors: ErrorList) -> NodeAndSuccess:
    blockContents: List[AST.Node] = []
    newFrame = SymbolFrame(symbolFrame)
    tList.expect(TT.OpenCurly)
    while not tList.peekType() in [TT.CloseCurly, TT.Error]:
        node, success = parseExpression(tList, types, newFrame, errors)
        if not success:
            tList.panic()
            if len(errors) > Core.MAX_ERRORS:
                return None, False
        blockContents.append(node)
    tList.expect(TT.CloseCurly)
    return AST.Block(newFrame, blockContents), True

@parser 
def parseIf(tList: TokenList, types: TypeDict, symbolFrame: SymbolFrame, errors: ErrorList) -> NodeAndSuccess:
    if not tList.peek().detail in [Keywords.If, Keywords.Elif]:
        errors.append(Core.CompileError("Expected If or Elif keywords (this shouldn't really ever happen?)"))
        tList.panic()
        return None, False
    tList.get()
    conditionFrame = SymbolFrame(symbolFrame)
    condition, cSuccess = parseExpression(tList, types, conditionFrame, errors)
    if not cSuccess:
        tList.panic()
        return None, False
    
    tList.expect(Keywords.Then)
    bodyFrame = SymbolFrame(conditionFrame)
    body, bSuccess = parseExpression(tList, types, bodyFrame, errors)
    if not bSuccess:
        tList.panic()
        return None, False
    
    elseBodyFrame = SymbolFrame(conditionFrame)
    elseBody = AST.EmptyNode(elseBodyFrame)
    
    match tList.peekTypeSubtype():
        case [TT.Keyword, Keywords.Else]:
            tList.expect(Keywords.Else)
            elseBody, eSuccess = parseExpression(tList, types, elseBodyFrame, errors)
            if not eSuccess:
                tList.panic()
                return None, False
        case [TT.Keyword, Keywords.Elif]:
            elifExpr, eSuccess = parseIf(tList, types, elseBodyFrame, errors)
            if not eSuccess:
                tList.panic()
                return None, False
    
    return AST.If(symbolFrame, condition, body, elseBody), True

@parser
def parseFor(tList: TokenList, types: TypeDict, symbolFrame: SymbolFrame, errors: ErrorList) -> NodeAndSuccess:
    tList.expect(Keywords.For)
    forFrame = SymbolFrame(symbolFrame)
    setupNode = AST.EmptyNode(forFrame)
    conditionNode = AST.EmptyNode(forFrame)
    incrementNode = AST.EmptyNode(forFrame)

    if tList.peekType() != TT.Semicolon:
        setupNode = parseExpression(tList, types, forFrame, errors)
    tList.expect(TT.Semicolon)
    if tList.peekType() != TT.Semicolon:
        loc = tList.peek().location
        conditionNode = parseExpression(tList, types, forFrame, errors)
        conditionType = getTypeOfNode(conditionNode)
        if conditionType != BoolType():
            raise Core.CompileError("Cannot use type \"" + str(conditionType) + "\" as result type of for loop comparison", loc)
    tList.expect(TT.Semicolon)
    if False in tList.match(Keywords.Do):
        incrementNode = parseExpression(tList, types, forFrame, errors)
    tList.expect(Keywords.Do)
    bodyNode = parseExpression(tList, types, forFrame, errors)
    return AST.For(symbolFrame, setupNode, conditionNode, incrementNode, bodyNode), True


@parser
def parseWhile(tList: TokenList, types: TypeDict, symbolFrame: SymbolFrame, errors: ErrorList) -> NodeAndSuccess:
    tList.expect(Keywords.While)
    whileFrame = SymbolFrame(symbolFrame)
    loc = tList.peek().location
    conditionNode = parseExpression(tList, types, whileFrame, errors)
    conditionType = getTypeOfNode(conditionNode)
    if conditionNode != BoolType():
        raise Core.CompileError("Cannot use type \"" + str(conditionType) + "\" as result type of while loop comparison", loc)
    bodyNode = parseExpression(tList, types, whileFrame, errors)
    elseNode = AST.EmptyNode(whileFrame)
    if True in tList.match(Keywords.Else):
        tList.expect(Keywords.Else)
        elseNode = parseExpression(tList, types, whileFrame, errors)
    return AST.While(symbolFrame, conditionNode, bodyNode, elseNode), True

# TODO: Figure out precidence of operators, ref, deref, is and as
# Make a function chain for identifier led statements
# Maybe have some syntax for tighter/looser bindings?
# IE  `ref world[10]` being get the address of world[10]
# and `ref:world[10]` being index the address of world by 10
# idk, ask Nabeel XD
# For now they bind loosest

@parser
def parseLiteral(tList: TokenList, symbolFrame: SymbolFrame) -> NodeAndSuccess:
    lit = tList.expect(TT.Literal)
    return AST.Literal(symbolFrame, lit)

def getSingleIdentifierOrLiteral(tList: TokenList, module: StructureModule, symbolFrame: SymbolFrame) -> Node:
    token = tList.peek()
    if token.ttype == TT.Literal:
        return parseLiteral(tList, symbolFrame)
    elif token.ttype == TT.Identifier:
        if symbolFrame.get(token.string) is not None:
            return AST.Identifier(symbolFrame, token, token.string)
        raise Core.CompileError("Use of undefined identifier \"" + token.string + "\"", token.location)
    # Get a nice error
    tList.expect([TT.Identifier, TT.Literal])
    return None

# For parsing an identifier with all pre and post fixes
@parser
def parsePreAndPostIdentifier(tList:TokenList, module: StructureModule, symbolFrame: SymbolFrame, errors: ErrorList, canBeAssignment: bool = False) -> NodeAndSuccess:
    preTokens: List[Tuple[Token, CollectedFunction]] = []
    keyIdentifier: AST.Node = None
    postTokens: List[Tuple[Token, CollectedFunction]] = []

    while tList.peekType() == TT.Identifier and module.isFunctionWithArity(tList.peekStr(), 1):
        preToke = tList.get()
        colFunc = module.functions[preToke.string]
        if len(preTokens) > 0:
            # TODO: Check for valid conversion
            if preTokens[-1][1].signiture.argumentTypes[0] != colFunc.signiture.returnType:
                raise Core.CompileError(
                    "Cannot call unary function \"" + preTokens[-1][0].string + "\" with output from unary function \"" + preToke.string + ""
                    "(" + str(preTokens[-1][1].signiture.argumentTypes[0]) + " vs " + str(colFunc.signiture.returnType) + ")",
                    preToke.location
                )
        preTokens.append((preToke, colFunc))
    
    idToken = tList.peek()
    keyIdentifier = getSingleIdentifierOrLiteral(tList, module, symbolFrame)
    if len(preTokens) > 0:
        if preTokens[-1][1].signiture.argumentTypes[0] != getTypeOfNode(keyIdentifier):
            raise Core.CompileError(
                "Cannot pass \"" + idToken.string + "\" into unary function \"" + preTokens[-1][0].string + "\" "
                "(Expeting type " + preTokens[-1][1].signiture.argumentTypes[0] ", found " + getTypeOfNode(keyIdentifier) + ")",
                idToken.string
            )
        
    while tList.peekType() == TT.Identifier and module.isFunctionWithArity(tList.peekStr(), 1):
        postToke = tList.get()
        collectedFunc = module.functions[postToke.string]
        if len(postTokens) > 0:
            # TODO: Check for valid conversion
            if postTokens[-1][1].signiture.returnType != collectedFunc.signiture.argumentTypes[0]:
                raise Core.CompileError(
                    "Cannot call unary function \"" + preTokens[-1][0].string + "\" with output from unary function \"" + postTokens[-1][0].string + ""
                    "(" + str(collectedFunc.signiture.argumentTypes[0]) + " vs " + str(postTokens[-1][1].signiture.returnType) + ")",
                    postToke.location
                )
        postTokens.append((postToke, collectedFunc))

    preTokens.reverse()
    for _, cf in preTokens:
        keyIdentifier = AST.FunctionCall(symbolFrame, cf, keyIdentifier)
    for _, cf in postTokens:
        keyIdentifier = AST.FunctionCall(symbolFrame, cf, keyIdentifier)
    return keyIdentifier



def parseIdentifierLine(tList: TokenList, types: TypeDict, symbolFrame: SymbolFrame, errors: ErrorList) -> NodeAndSuccess:
    startingIdentifierToken = tList.get()
    allFunctions: Dict[str, CollectedFunction] = symbolFrame.getModule().functions



    return None, False

# REDO That deref thing to allow assignment afterwards
def parseExpression(tList: TokenList, types: TypeDict, symbolFrame: SymbolFrame, errors: ErrorList) -> NodeAndSuccess:
    match tList.peekType():
        case TT.OpenCurly:
            return parseBlock(tList, types, symbolFrame, errors)
        case TT.Keyword:
            match tList.peek().detail:
                case Keywords.If:
                    return parseIf(tList, types, symbolFrame, errors)
                case Keywords.For:
                    return parseFor(tList, types, symbolFrame, errors)
                case Keywords.While:
                    return parseWhile(tList, types, symbolFrame, errors)
                case Keywords.Ref:
                    refToken = tList.get()
                    refOf, sucecss = parseExpression(tList, types, symbolFrame, errors)
                    if sucecss:
                        if AST.NodeTrait.LValue in refOf.traits():
                            return AST.Reference(refOf), True
                        raise Core.CompileError("Cannot take reference of non lvalue", refToken.location)
                    return None, False
                case Keywords.Deref:
                    derefToken = tList.get()
                    derefOf, sucecss = parseExpression(tList, types, symbolFrame, errors)
                    if sucecss:
                        derefType = getTypeOfNode(derefOf)
                        if isinstance(derefType, PtrType):
                            if derefType.isArray == False:
                                return AST.Reference(refOf), True
                            else:
                                raise Core.CompileError("Cannot dereference array type \"" + str(derefType) + "\"", derefToken.location)
                        raise Core.CompileError("Cannot dereference non pointer type \"" + str(derefType + "\""), derefToken.location)
                    return None, False
                case Keywords.Return:
                    tList.expect(Keywords.Return)
                    returnVal, success = parseExpression(tList, types, symbolFrame, errors)
                    if success:
                        return AST.Return(symbolFrame, returnVal), True
                    return None, False
                case _:
                    errors.append(Core.CompileError("Expected expression, found \"" + str(tList.peek().string) + "\"", tList.peek().location))
                    tList.panic()
                    return None, False
        case TT.Identifier:
            return parseIdentifierLine(tList, types, symbolFrame, errors)
        case _:
            # TODO: EVERYTHING ELSE
            tList.get()
            return None, False
