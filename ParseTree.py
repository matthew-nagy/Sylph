from Structures import *
from SylphTypes import *
from Tokeniser import TokenType

@dataclass
class ParseNode:
    frame: SymbolFrame
    def getResultingType(self) -> SylphType:
        return ErrorType()
    def isAssignable(self) -> bool:
        return False
    def print(self, depth: int):
        print("".join('\t' for i in range(depth)), end=None)

@dataclass
class Block(ParseNode):
    innerNodes: list[ParseNode]

    def getResultingType(self):
        if len(self.innerNodes) == 0:
            return NoneType()
        return self.innerNodes[-1].getResultingType()
    
    def print(self, depth):
        for node in self.innerNodes:
            node.print(depth + 1)

@dataclass
class Literal(ParseNode):
    literalTok: Token

    def getResultingType(self):
        mapping: dict[TokenType, SylphType] = {
            TokenType.IntLiteral: IntType(64, self.literalTok.rep[-1] != 'u'),
            TokenType.FloatLiteral: FloatType(32), TokenType.DoubleLiteral: FloatType(64),
            TokenType.BoolLiteral: BoolType(), TokenType.NoneLiteral: NoneType(),
            TokenType.ByteLiteral: ByteType(), TokenType.StringLiteral: StringType()
        }
        if self.literalTok.ttype in mapping.keys():
            return mapping[self.literalTok.ttype]
        return ErrorType()
    
    def print(self, depth):
        super().print(depth)
        print(self.literalTok.rep)

@dataclass
class If(ParseNode):
    condition: ParseNode
    thenBody: ParseNode
    elseBody: ParseNode | None

    def getResultingType(self):
        # TODO: Update this to a sum type later!
        thenBodyType: SylphType = self.thenBody.getResultingType()
        if self.elseBody is None:
            return thenBodyType
        else:
            elseBodyType = self.elseBody.getResultingType()
            if thenBodyType == elseBodyType:
                return thenBodyType
            # SUM TYPES!!!
            return NoneType()
    
    def print(self, depth):
        super().print(depth)
        print("IF:")
        self.condition.print(depth + 1)
        super().print(depth)
        print("THEN:")
        self.thenBody.print(depth + 1)
        if self.elseBody is not None:
            super().print(depth)
            print("ELSE:")
            self.elseBody.print(depth + 1)

@dataclass
class For(ParseNode):
    creationNode: ParseNode | None
    conditionNode: ParseNode | None
    iterationNode: ParseNode | None
    loopBody: ParseNode

    # TODO: uhh, list types?
    def getResultingType(self):
        return NoneType()
    def print(self, depth):
        super().print(depth)
        print("FOR:")
        for name, node in [("CREATE:", self.creationNode), ("COND:", self.conditionNode), ("ITER:", self.iterationNode)]:
            if node is not None:
                super().print(depth)
                print(name)
                node.print(depth + 1)
        super().print(depth)
        self.loopBody.print(depth + 1)

# TODO: Add while
# class While(ParseNode)....

@dataclass
class FunctionCall(ParseNode):
    func: PreParseFunction
    arguments: list[ParseNode]

    def getResultingType(self):
        return self.func.signiture.returnType
    def print(self, depth):
        super().print(depth)
        print("CALL", self.func.token.rep)
        for arg in self.arguments:
            arg.print(depth + 1)

@dataclass
# The genuine- like int + int. A genuine binary operation
class BinaryOp(ParseNode):
    op: Token
    left: ParseNode
    right: ParseNode
    opType: SylphType

    def getResultingType(self):
        return self.op
    
    def print(self, depth):
        super().print(depth)
        print("OP", self.op.rep + ":")
        self.left.print(depth + 1)
        self.right.print(depth + 1)



@dataclass
# For genuine assigns, rather than func overloads
class Assign(ParseNode):
    left: ParseNode
    right: ParseNode

    def getResultingType(self):
        return self.left.getResultingType()
    
    def print(self, depth):
        super().print(depth)
        print("ASSIGN:")
        self.left.print(depth + 1)
        super().print(depth)
        print("TO:")
        self.right.print()


@dataclass
class Identifier(ParseNode):
    symbol: Symbol

    def getResultingType(self):
        return self.symbol.sylphType
    def isAssignable(self):
        # TODO: Check for const
        return True
    def print(self, depth):
        super().print(depth)
        print(self.symbol.token.rep)

@dataclass
class Return(ParseNode):
    returnValue: ParseNode

    def getResultingType(self):
        return self.returnValue.getResultingType()
    
    def print(self, depth):
        super().print(depth)
        print("RETURN:")
        self.returnValue.print(depth + 1)

# TODO: Ref and Deref, Break and Continue
