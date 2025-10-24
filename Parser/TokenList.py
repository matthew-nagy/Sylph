from typing import List
from Scanner.Tokens import *

class TokenList:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.currentIndex = 0
    
    def hasTokens(self) -> bool:
        return self.currentIndex < len(self.tokens)

    def peek(self, extraAhead: int = 0) -> Token:
        if self.currentIndex + extraAhead >= len(self.tokens):
            return Token(TT.Error, None, Core.SourceInfo("NULL", -1, -1), "")
        return self.tokens[self.currentIndex + extraAhead]
    
    def peekType(self, extraAhead: int = 0) -> TT:
        return self.peek(extraAhead).ttype
    
    def peekTypeSubtype(self, extraAhead: int = 0) -> tuple[TT, TokenSubtype]:
        t = self.peek(extraAhead)
        return t.ttype, t.detail
    
    def peekStr(self, extraAhead: int = 0) -> str:
        return self.peek(extraAhead).string
    
    def get(self) -> Token:
        val = self.peek()
        self.currentIndex += 1
        return val
    
    def putBack(self, amount: int = 1):
        self.currentIndex -= amount

    # Panic down to the next line hoping that the errors stop
    def panic(self, startingLineNum: int | None = None):

        newLoc = self.peek().location.line_number
        # if for whatever reason we don't have the line number, we can estimate one
        if startingLineNum is None:
            startingLineNum = newLoc

        while startingLineNum == newLoc and self.hasTokens():
            newLoc = self.get().location.line_number
    
    def match(self, value: TT | List[TT] | Keywords | str) -> tuple[bool, Token | None]:
        match value:
            case TT() if self.peek().ttype == value:
                return True, self.get()
            case [TT(), *_] if self.peekType() in value:
                return True, self.get()
            case Keywords() if isinstance(self.peek().detail, Keywords):
                if self.peek().detail == value:
                    return True, self.get()
            case str() if self.peek().string == value:
                return True, self.get()
        return False, None
    
    def expect(self, value: TT | List[TT] | Keywords | str) -> Token:
        matched, tokens = self.match(value)
        if matched:
            return tokens
        else:
            message = "Undefined"
            match value:
                case TT():
                    message = "Expected " + str(value) + " found " + self.peek().string
                case [TT(), *_]:
                    message = "Expected one of [" + ",".join([str(i) for i in value]) + "], found " + self.peek().string
                case Keywords():
                    message = "Expected " + str(value) + " found " + self.peek().string
                case str():
                    message = "Expected " + value + ", found " + self.peek().string
            
            raise Core.CompileError(message, self.peek().location)
