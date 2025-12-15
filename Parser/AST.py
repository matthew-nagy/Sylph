from enum import Enum
from Scanner.Tokens import *
from Types import SylphType
from Parser.Types import SymbolFrame
from dataclasses import dataclass
from typing import Dict, Set
from Parser.StructurePass import CollectedFunction

class NodeTrait(Enum):
    # Assignable or addressable
    LValue = 0
    Constant = 1
    

def ast(*nodeTraits):
    traits = set()
    for trait in nodeTraits:
        traits.add(trait)
    def inner(cls):
        cls.traits = lambda self: traits
        return dataclass(cls)
    return inner


@dataclass
class Node:
    frame: SymbolFrame

@ast()
class EmptyNode(Node):
    pass

@ast(NodeTrait.Constant)
class Literal(Node):
    lit: Token

@ast(NodeTrait.LValue)
class Identifier(Node):
    token: Token
    name: str

@ast()
class Block(Node):
    contents: List[Node]

@ast()
class If(Node):
    condition: Node
    body: Node
    elseNode: Node

@ast()
class While(Node):
    condition: Node
    body: Node
    elseNode: Node

@ast()
class For(Node):
    setup: Node
    condition: Node
    increment: Node
    body: Node

@ast()
class FunctionCall(Node):
    function: Node | CollectedFunction
    arguments: List[Node]

@ast(NodeTrait.LValue)
class Index(Node):
    of: Node
    by: Node

@ast()
class Is(Node):
    expr: Node
    type: SylphType

@ast(NodeTrait.LValue)
class As(Node):
    expr: Node
    type: SylphType

@ast()
class Reference(Node):
    of: Node

@ast(NodeTrait.LValue)
class Dereference(Node):
    of: Node

@ast()
class Return(Node):
    val: Node

@ast()
class BinaryOp(Node):
    left: Node
    operator: Token
    right: Node