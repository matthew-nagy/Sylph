from enum import Enum
from dataclasses import dataclass
import Core
from typing import List

class charset:
    roman = [chr(i) for i in range(ord('a'), ord('z') + 1)] + [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    digits = [str(i) for i in range(10)]
    alphanumeric = roman + digits + ["_"]
    hex = digits + ["A", "B", "C", "D", "E", "F"]
    binary = ["0", "1"]
    operating = ["+", "-", "*", "/", "!", "<", ">", "=", "&", "|", "^", "~"]
    special = ["\"", "'", "@"]
    whitespace = [" ", "\t", "\n"]
    commentChar = "#"


class LiteralType(Enum):
    IntLit = 0
    FloatLit = 1
    StrLit = 2
    BoolLit = 3
    NullLit = 4
    
class IdentifierType(Enum):
    StandardIdentifier = 0
    OperatingIdentifier = 1

    # Not done by the scanner. The Parser will fill this in as it learns about types
    TypeIdentifier = 2

class Keywords(Enum):
    If = 0
    Elif = 1
    Else = 2
    Then = 3
    While = 4
    For = 5
    Do = 6
    Func = 7
    Ptr = 8
    Ref = 9
    Deref = 10
    As = 11
    Is = 12
    Using = 13
    Meta = 14
    Return = 15

KeywordMap = {
    "if": Keywords.If, "elif": Keywords.Elif, "else": Keywords.Else, "then": Keywords.Then, 
    "while": Keywords.While, "for": Keywords.For, "do": Keywords.Do,
    "func": Keywords.Func,
    "ptr": Keywords.Ptr, "ref": Keywords.Ref, "deref": Keywords.Deref,
    "as": Keywords.As, "is": Keywords.Is, "using": Keywords.Using,
    "meta": Keywords.Meta,
    "return": Keywords.Return
}

class TagType(Enum):
    Prefix = 0
    Infix = 1
    Postfix = 2

TagTypeMap = {
    "prefix": TagType.Prefix, "infix": TagType.Infix, "postfix": TagType.Postfix
}

class TokenType(Enum):
    OpenBracket = 0
    CloseBracket = 1
    OpenBrace = 2
    CloseBrace = 3
    OpenCurly = 4
    CloseCurly = 5
    Dot = 6
    Comma = 7
    Colon = 8
    Semicolon = 9

    Literal = 20
    Identifier = 21
    Keyword = 22
    Tag = 23

    Special = 30
    Error = 31
    EOF = 32
    
TT = TokenType

TokenTypeMap = {
    "(" : TT.OpenBracket, ")": TT.CloseBracket,
    "[": TT.OpenBrace, "]": TT.CloseBrace,
    "{": TT.OpenCurly, "}": TT.CloseCurly,
    ".": TT.Dot, ",": TT.Comma, 
    ":": TT.Colon, ";": TT.Semicolon
}

TokenSubtype = LiteralType | IdentifierType | Keywords | TagType | None

@dataclass
class Token:
    ttype: TT
    detail: TokenSubtype
    location: Core.SourceInfo
    string: str