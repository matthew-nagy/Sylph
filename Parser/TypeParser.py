import Parser.AST as AST
from Types import *
from Scanner.Tokens import *

# TODO: DO!!!
def getTypeOfBinaryOp(node: AST.BinaryOp) -> SylphType:
    raise Exception()
    return NullType()

def getTypeOfNode(node: AST.Node) -> SylphType:
    match node:
        case AST.Literal:
            # We assume the largest possible kind, and AST sweeps can fix it in post lmao
            return {
                LiteralType.IntType: IntType(True, 8),
                LiteralType.FloatLit: FloatType(True),
                LiteralType.BoolLit: BoolType(),
                LiteralType.StrLit: StringType(),
                LiteralType.NullLit: NullType()
            }[node.lit.detail]
        case AST.Identifier:
            sym = node.frame.get(node.name)
            if sym is not None:
                return sym.type
            raise Core.CompileError("Cannot type check undefined variable \"" + node.name + "\"", node.token.location)
        case AST.Block:
            if len(node.contents) > 0:
                return getTypeOfNode(node.contents[-1])
            return NullType()
        case AST.If:
            # TODO: Should change if ast so that there can be multiple conditions/bodies
            # This prevents a recursive sum type issue
            firstType = getTypeOfNode(node.body)
            secondType = getTypeOfNode(node.elseNode)
            if firstType == secondType:
                return firstType
            return SumType([firstType, secondType])
        case AST.While:
            # TODO when we get list types in this will be great
            # ... we could probably do it now though
            return NullType()
        case AST.For:
            # TODO: same as while
            return NullType
        case AST.FunctionCall:
            if isinstance(node.function, AST.Identifier):
                if node.function.name in node.frame.getModule().functions.keys():
                    return node.frame.getModule().functions[node.function.name].signiture.returnType
                raise Core.RuntimeError("Cannot type check a call to a non-callable identifier \"" + node.function.name + "\"", node.function.token.location)
            funcType = getTypeOfNode(node.function)
            if isinstance(funcType, FunctionPtr):
                return funcType.returnType
            # This shouldn't ever be the case so its OK that this is a little spooky
            raise Core.RuntimeError("Cannot type chec a call to a non-callable type \"" + str(funcType) + "\"", Core.SourceInfo("INTERNAL_ERROR", -1, -1))
        case AST.Index:
            indexingType = getTypeOfNode(node.of)
            match indexingType:
                case PtrType(ptrOf):
                    return ptrOf
                case _:
                    raise Core.RuntimeError("Cannot type check index on non-ptr type \"" + str(indexingType) + "\"", Core.SourceInfo("INTERNAL_ERROR", -1, -1))
        case AST.Is:
            return BoolType()
        case AST.As:
            return node.type
        case AST.Reference:
            return PtrType(getTypeOfNode(node.of), False, None)
        case AST.Dereference:
            derefType = getTypeOfNode(node.of)
            match derefType:
                case PtrType(of):
                    return of
                case _:
                    raise Core.RuntimeError("Cannot dereference non-ptr type \"" + str(derefType) + "\"", Core.SourceInfo("INTERNAL_ERROR", -1, -1))
        case AST.Return:
            return getTypeOfNode(node.val)
        case AST.Assign:
            return getTypeOfNode(node.left)
        case AST.BinaryOp:
            return getTypeOfBinaryOp(node)
        