from common import *
from typing import IO
import os

class TokenType(Enum):
    If, Else, Elif, Then,\
    For, While, Do, Continue, Break,\
    Class, Func, Alias, Import,\
    Return,\
    Ptr, Ref, Deref,\
    \
    OpenBracket, CloseBracket, OpenBrace, CloseBrace, OpenSquare, CloseSquare,\
    Colon, Semicolon, Dot, Comma,\
    \
    IntLiteral, FloatLiteral, DoubleLiteral, StringLiteral, BoolLiteral, ByteLiteral, NoneLiteral,\
    Identifier,\
    \
    EndOfFile, Error\
    \
    = range(0, 37)

KeywordMap: dict[str, TokenType] = {
    "if": TokenType.If, "else": TokenType.Else, "elif": TokenType.Elif, "then": TokenType.Then,
    "for": TokenType.For, "while": TokenType.While, "do": TokenType.Do, "continue": TokenType.Continue, "break": TokenType.Break,
    "class": TokenType.Class, "func": TokenType.Func, "alias": TokenType.Alias, "import": TokenType.Import,
    "return": TokenType.Return,
    "ptr": TokenType.Ptr, "ref": TokenType.Ref, "deref": TokenType.Deref
}

WhitespaceList: list[str] = [' ', '\t', '\n']

EscapeCharacterMap: dict[str, str] = {
    "n": "\n", "t": "\t", "\"": "\"", "\\": "\\", "0": "\0"
}

SingleCharTokenMap: dict[str, TokenType] = {
    '(': TokenType.OpenBracket, ')': TokenType.CloseBracket, "{": TokenType.OpenBrace, "}": TokenType.CloseBrace,
    "[": TokenType.OpenSquare, "]": TokenType.CloseSquare, ":": TokenType.Colon, ";": TokenType.Semicolon,
    ".": TokenType.Dot, ",": TokenType.Comma
}

CommentChar = '#'

def isAlphabetic(val: str)-> bool:
    if val in [chr(i) for i in ([i for i in range(ord('a'), ord('z') + 1)] + [i for i in range(ord('A'), ord('Z') + 1)])]:
        return True
    return False

def isNumeric(val: str)-> bool:
    return val in [str(i) for i in range(0, 10)]

def isAlphanumeric(val: str)-> bool:
    return isAlphabetic(val) or isNumeric(val) or val == '_'

def isOperatoric(val: str)-> bool:
    return val in ['+', '-', '*', '/', '%', '&', '|', "!", '~', '<', '>', '=']

@dataclass
class Token:
    ttype : TokenType
    sourceInfo : SourceInfo
    rep : str

    def __str__(self):
        return "Token(" + str(self.ttype) + ",'" + self.rep + "' " + str(self.sourceInfo) + ")"

def isLiteral(tt: Token | TokenType) -> bool:
    if isinstance(tt, Token):
        return Token.isLiteral(tt.ttype)
    return tt in range(TokenType.IntLiteral, TokenType.NoneLiteral + 1)

def isKeyword(tt: Token | TokenType) -> bool:
    if isinstance(tt, Token):
        return Token.isLiteral(tt.ttype)
    return tt in range(TokenType.If, TokenType.Deref + 1)
    
class Tokeniser:
    def __init__(self):
        self.filesToParse: list[tuple[str, IO]] = []
        self.currentFileContents: list[str] = []
        self.currentLine: str = ""
        self.lineIndex: int = 0
        self.columnIndex: int = 0
        self.hasFileOpen: bool = False

        self.tokenBuffer: list[Token] = []

    def __getSourceInfo(self) -> SourceInfo:
        return SourceInfo(self.columnIndex, self.lineIndex, self.filesToParse[0][0])

    def __peekChar(self) -> str:
        if not self.hasFileOpen:
            return '\0'
        if len(self.currentFileContents) == self.lineIndex:
            return '\0'
        return self.currentLine[self.columnIndex]
    
    def __incrementCharacter(self):
        self.columnIndex += 1
        # New line needed. Need to shortcircuit the left for when they are equal for the EOF Token
        if self.lineIndex >= len(self.currentFileContents) or len(self.currentLine) <= self.columnIndex:
            self.lineIndex += 1
            self.columnIndex = 0
            # New file needed. If line index equals length of the contents, we return EOF
            if len(self.currentFileContents) < self.lineIndex:
                self.lineIndex = 0
                # Close the old file
                self.filesToParse[0][1].close()
                self.filesToParse = self.filesToParse[1:]
                # If we have no files left, make sure we know that!
                if len(self.filesToParse) == 0:
                    self.hasFileOpen = False
                else:
                    self.currentFileContents = self.filesToParse[0][1].readlines()
            # This is false for the eof character
            if len(self.currentFileContents) > self.lineIndex:
                self.currentLine = self.currentFileContents[self.lineIndex]

    def __nextChar(self) -> str:
        toReturn = self.__peekChar()
        self.__incrementCharacter()
        
        return toReturn

    def __getNumericLiteralToken(self, si: SourceInfo):
        rep = self.__nextChar()
        # TODO: Can't do binary or hex, because x or b could be the start of the next token which is an infix function

        while isNumeric(self.__peekChar()):
            rep += self.__nextChar()
        
        if self.__peekChar() == '.': # TODO: if its then not numeric, return two tokens- int and dot
            rep += self.__nextChar()
            while isNumeric(self.__peekChar()):
                rep += self.__nextChar()
            if self.__peekChar() == 'f':
                rep += self.__nextChar()
                return Token(TokenType.FloatLiteral, si, rep)
            return Token(TokenType.DoubleLiteral, si, rep)
        
        if self.__peekChar() == 'f':
            rep += self.__nextChar()
            return Token(TokenType.FloatLiteral, si, rep)
        return Token(TokenType.IntLiteral, si, rep)
        

    def __getByteLiteralToken(self, si: SourceInfo):
        self.__nextChar()
        rep = self.__nextChar()
        preNextCharSI = self.__getSourceInfo()
        nextChar = self.__nextChar()
        # Shfnangle this for escape characters
        if rep == '\\' and nextChar in EscapeCharacterMap.keys():
            rep = EscapeCharacterMap[nextChar]
            preNextCharSI = self.__getSourceInfo()
            nextChar = self.__nextChar()
        
        if nextChar != "'":
            return Token(TokenType.Error, preNextCharSI, nextChar)
        return Token(TokenType.ByteLiteral, si, rep)

    def __getAlphabeticToken(self, si: SourceInfo):
        identifierStr = ""
        while isAlphanumeric(self.__peekChar()):
            identifierStr += self.__nextChar()
        
        # We may have snagged a keyword
        if identifierStr in KeywordMap.keys():
            return Token(KeywordMap[identifierStr], si, identifierStr)
        # Could be a boolean
        elif identifierStr in ["false", "true"]:
            return Token(TokenType.BoolLiteral, si, identifierStr)
        # Or none literal
        elif identifierStr == "None":
            return Token(TokenType.NoneLiteral, si, identifierStr)
        return Token(TokenType.Identifier, si, identifierStr)

    def __getStringLiteralToken(self, si: SourceInfo):
        self.__nextChar() # Burn the open quotes
        rep = ""
        # If we do, make sure we remember so we can return an error instead
        cameAcrossBadEscapeCharacter = False
        preEscapeSI = None
        badEscape = ''
        while self.__peekChar() != '"' and self.__peekChar() != '\0':
            if self.__peekChar() == '\\' and not cameAcrossBadEscapeCharacter: # Escape character time!!
                self.__nextChar()
                preEscapeSI = self.__getSourceInfo()
                if self.__peekChar() in EscapeCharacterMap.keys():
                    rep += EscapeCharacterMap[self.__nextChar()]
                else:
                    cameAcrossBadEscapeCharacter = True
                    badEscape = self.__nextChar()
            else:
                rep += self.__nextChar()
        
        if self.__peekChar() == '"':
            self.__nextChar()
            if cameAcrossBadEscapeCharacter:
                return Token(TokenType.Error, preEscapeSI, badEscape)
            return Token(TokenType.StringLiteral, si, rep)
        if self.__peekChar() == '\0':
            return Token(TokenType.Error, self.__getSourceInfo(), self.__getNewToken())
        if cameAcrossBadEscapeCharacter:
            return Token(TokenType.Error, preEscapeSI, badEscape)

    def __getNewTokenImpl(self) -> Token | list[Token]:
        while self.__peekChar() in WhitespaceList:
            self.__nextChar()
            if self.hasFileOpen == False:
                return Token(TokenType.Error, SourceInfo(0, 0, "NO OPEN FILE"), "")
            if len(self.filesToParse) == 0 or self.hasFileOpen == False:
                return Token(TokenType.EndOfFile, SourceInfo(0, 0, "NO OPEN FILE"), "")
        
        si = self.__getSourceInfo()

        if self.__peekChar() == '\0':
            self.__nextChar()
            return Token(TokenType.EndOfFile, si, "<EOF>")

        # Is this going to be simple or not
        if self.__peekChar() in SingleCharTokenMap.keys():
            return Token(SingleCharTokenMap[self.__peekChar()], si, self.__nextChar())

        # Get operative identifier
        if isOperatoric(self.__peekChar()):
            operativeStr = ""
            while isOperatoric(self.__peekChar()):
                operativeStr += self.__nextChar()
            return Token(TokenType.Identifier, si, operativeStr)
        # Get non-operative identifier
        if isAlphabetic(self.__peekChar()) or self.__peekChar() == '_':
            return self.__getAlphabeticToken(si)
        
        # Literal time
        if isNumeric(self.__peekChar()):
            return self.__getNumericLiteralToken(si)
        elif self.__peekChar() == "'":
            return self.__getByteLiteralToken(si)
        elif self.__peekChar() == '"':
            return self.__getStringLiteralToken(si)

        return Token(TokenType.Error, si, self.__nextChar())

    def __getNewToken(self):
        result = self.__getNewTokenImpl()
        if isinstance(result, Token):
            self.tokenBuffer.append(result)
        else:
            # We assume its a list
            self.tokenBuffer += result

    # TODO: Want more than just relative paths here
    # Should have a "Add Include Path" func
    # If could be more than one file, return a special error token on import
    def addFile(self, filename: str) -> ErrorType:
        if os.path.exists(filename):
            f = open(filename, "r")
            self.filesToParse.append((filename, f))
            if not self.hasFileOpen or len(self.filesToParse) == 1:
                self.hasFileOpen = True
                self.currentFileContents = f.readlines()
                self.currentLine = self.currentFileContents[0]
            return ErrorType.NoError
        return ErrorType.FileNotFound
    
    def peek(self) -> Token:
        if len(self.tokenBuffer) == 0:
            self.__getNewToken()
        return self.tokenBuffer[0]

    def peekType(self) -> TokenType:
        return self.peek().ttype

    def next(self) -> Token:
        nextToken = self.peek()
        self.tokenBuffer = self.tokenBuffer[1:]
        return nextToken
    
    def match(self, types: list[TokenType]) -> bool:
        while len(self.tokenBuffer) < len(types):
            self.__getNewToken()
        nextTypes = [i.ttype for i in self.tokenBuffer]
        return not (False in [nextTypes[i] == types[i] for i in range(len(types))])
    
    # Raises an error on fail
    def expect(self, ttype: TokenType | list[TokenType]) -> Token:
        if isinstance(ttype, TokenType):
            if ttype == self.peekType():
                return self.next()
        elif self.peekType() in ttype:
            return self.next()
        raise SylphError(self.peek().sourceInfo, ErrorType.UnexpectedToken, [str(ttype), str(self.peekType())])
        # Unreachable
        return None
    
    def expectString(self, string: str) -> Token:
        if self.peek().rep == string:
            return self.next()
        raise SylphError(self.peek().sourceInfo, ErrorType.UnexpectedToken, [string, self.peek().rep])

    def canTokenise(self) -> bool:
        return self.hasFileOpen or len(self.filesToParse) > 0 or len(self.tokenBuffer) > 0

if __name__ == "__main__":
    t = Tokeniser()
    testPath = "tests/Simple/tokeniser.syl"

    errortype = t.addFile(testPath)
    if errortype != ErrorType.NoError:
        print("Error finding test file", testPath)
    else:
        print("File is open")

    errorCount = 0
    maxErrorCount = 20
    
    while True:
        token = t.next()
        print(token)
        if not t.canTokenise():
            break
        elif token.ttype == TokenType.Error:
            errorCount += 1
            if errorCount >= maxErrorCount:
                break