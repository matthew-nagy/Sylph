from typing import List, Set
from dataclasses import dataclass
import os
import Core
from enum import Enum
from Scanner.Tokens import *

@dataclass
class File:
    contents: List[str]
    filename: str
    lineNumber: int = 0
    charNumber: int = 0

class ReadResult(Enum):
    Read = 0
    EndOfLine = 1
    EndOfFile = 2

class Reader:
    @Core.orErrorMethod
    def openFile(self, filename: str) -> None | Core.CompileError:
        if not (filename in self.lexedFiles):
            if not os.path.exists(filename):
                raise Core.CompileError("Cannot find file '" + filename + "'", self.getSourceInfo())
            io = open(filename, "r")
            self.files.append(File(io.readlines(), filename))
            self.lexedFiles.add(filename)
        return None

    def __init__(self, firstFilename: str):
        self.lexedFiles: Set[str] = set()
        self.files: List[File] = []
        self.openFile(firstFilename)

    def reading(self) -> bool:
        return len(self.files) > 0

    def peek(self) -> str:
        if len(self.files) == 0:
            raise Core.CompileError("No files left to parse", self.getSourceInfo())
        currFile = self.files[-1]
        return currFile.contents[currFile.lineNumber][currFile.charNumber]
    
    def get(self) -> tuple[str, ReadResult]:
        value = self.peek()
        result: ReadResult = ReadResult.Read
        currFile = self.files[-1]
        currFile.charNumber += 1
        if currFile.charNumber == len(currFile.contents[currFile.lineNumber]):
            currFile.charNumber = 0
            currFile.lineNumber += 1
            result = ReadResult.EndOfLine
            if currFile.lineNumber == len(currFile.contents):
                self.files.pop()
                result = ReadResult.EndOfFile

        return value, result

    def match(self, word: str) -> tuple[bool, Core.SourceInfo]:
        currFile = self.files[-1]
        line = currFile.contents[currFile.lineNumber]
        si = self.getSourceInfo()
        if len(line) >= (currFile.charNumber + len(word)):
            if line[currFile.charNumber : currFile.charNumber + len(word)] == word:
                # Check to make sure either we are at the end of the line, or that the next character couldn't be a continuation
                # We want to avoid matcing the keyword "while" to the start of the variable "whileRunning"
                if len(line[currFile.charNumber:]) == len(word) or not line[currFile.charNumber + len(word)] in charset.alphanumeric:
                    currFile.charNumber += len(word)
                    return True, si
        
        return False, si

    def getSourceInfo(self) -> Core.SourceInfo:
        currFile = self.files[-1]
        return Core.SourceInfo(currFile.filename, currFile.lineNumber, currFile.charNumber)
    
    def removeWhitespace(self):
        removing = True
        while removing:
            while self.peek() in charset.whitespace:
                self.get()
            if self.peek() == charset.commentChar:
                result = ReadResult.Read
                # Keep removing until the end of the line
                while result == ReadResult.Read:
                    _, result = self.get()
            # Not whitespace nor comment, its real
            else:
                removing = False

class Scanner:

    # TODO: We don't handle binary and hex literals yet
    @staticmethod
    @Core.orErrorMethod
    def tokeniseNumber(reader: Reader) -> List[Token] | Core.CompileError:
        innerString = ""
        parsingOneNumber = True
        had_dot = False
        si = reader.getSourceInfo()
        eof = False
        while parsingOneNumber and reader.peek() in (charset.digits + ["."]):
            if reader.peek() == ".":
                if had_dot:
                    parsingOneNumber = False
                    break
                had_dot = True
            
            nextChar, outcome = reader.get()
            innerString += nextChar
            if outcome != ReadResult.Read:
                parsingOneNumber = False
                if outcome == ReadResult.EndOfFile:
                    eof = True
        
        # Trailing f or d at end of float/double literals
        if had_dot and parsingOneNumber and reader.peek() in ["f", "d"]:
            reader.get()
        
        return [Token(
            TT.Literal, LiteralType.IntLit if not had_dot else LiteralType.FloatLit, si, innerString
        )] + ([] if not eof else [Token(TT.EOF, None, reader.getSourceInfo(), "")])
    
    # TODO: We don't handle escape characters yet
    @staticmethod
    @Core.orErrorMethod
    def tokeniseString(reader: Reader) -> List[Token] | Core.CompileError:
        si = reader.getSourceInfo()
        innerString = "\""
        # Burn the first "
        _, outcome = reader.get()
        if outcome == ReadResult.EndOfLine:
            raise Core.CompileError("Unexpected end of line while parsing string", si)
        if outcome == ReadResult.EndOfFile:
            raise Core.CompileError("Unexpected end of file while parsing string", si)
        while reader.peek() != "\"":
            nextChar, outcome = reader.get()
            innerString += nextChar
            if outcome == ReadResult.EndOfLine:
                raise Core.CompileError("Unexpected end of line while parsing string " + innerString + '"', si)
            if outcome == ReadResult.EndOfFile:
                raise Core.CompileError("Unexpected end of file while parsing string " + innerString + '"', si)
        # Burn that last "
        reader.get()
        innerString += "\""
        return [Token(
            TT.Literal, LiteralType.StrLit, si, innerString
        )]
    
    @staticmethod
    @Core.orErrorMethod
    def tokeniseTag(reader: Reader) -> List[Token] | Core.CompileError:
        si = reader.getSourceInfo()
        _, outcome = reader.get()
        if outcome == ReadResult.EndOfLine:
            raise Core.CompileError("Unexpected end of line while parsing tag", si)
        if outcome == ReadResult.EndOfFile:
            raise Core.CompileError("Unexpected end of file while parsing tag", si)
        
        for possibleTag in TagTypeMap.keys():
            matched, _ = reader.match(possibleTag)
            if matched:
                return [Token(
                    TT.Tag, TagTypeMap[possibleTag], si, "@" + possibleTag
                )]

    @staticmethod
    @Core.orErrorMethod
    def processToken(reader: Reader) -> List[Token] | Core.CompileError:
        si = reader.getSourceInfo()

        # Single character special tokens
        # TODO: Since ()[] and so forth are special tokens, it will be hard to create
        # and operator() equivilent later on...

        match reader.peek():
            case "\"":
                return Scanner.tokeniseString(reader)
            case "@":
                return Scanner.tokeniseTag(reader)
            case x if x in TokenTypeMap.keys():
                reader.get()
                return [Token(
                    TokenTypeMap[x], None, si, x
                )]
            case digit if digit in charset.digits:
                return Scanner.tokeniseNumber(reader)
            case alphanum if alphanum in charset.alphanumeric:
                for keyword in KeywordMap.keys():
                    isKeyword, si = reader.match(keyword)
                    if isKeyword:
                        return [Token(
                            TT.Keyword, KeywordMap[keyword], si, keyword
                        )]
                
                # Identifiers can't start with numbers, but we already checked for digits higher up!
                identifierString = ""
                sameLine = True
                while reader.peek() in charset.alphanumeric and sameLine:
                    nextChar, outcome = reader.get()
                    identifierString += nextChar
                    if outcome != ReadResult.Read:
                        sameLine = False
                return [Token(
                    TT.Identifier, IdentifierType.StandardIdentifier, si, identifierString
                )]
            case op if op in charset.operating:
                identifierString = ""
                sameLine = True
                while reader.peek() in charset.operating and sameLine:
                    nextChar, outcome = reader.get()
                    identifierString += nextChar
                    if outcome != ReadResult.Read:
                        sameLine = False
                return [Token(
                    TT.Identifier, IdentifierType.OperatingIdentifier, si, identifierString
                )]
            case _:
                char, _ = reader.get()
                return [Token(
                    TT.Error, None, si, char
                )]

    # TODO: meta not yet implemented properly- doesn't stop and start reading python
    # May change so rather than "meta" being a keyword token, the whole thing is stored
    # as a meta token, with the python being where the subtype normally is
    @staticmethod
    def scan(filename: str) -> tuple[bool, List[Token] | List[Core.CompileError]]:
        tokens: List[Token] = []
        errors: List[Core.CompileError] = []
        reader: Reader = Reader(filename)

        while reader.reading() and len(errors) < Core.MAX_ERRORS:
            reader.removeWhitespace()
            output = Scanner.processToken(reader)
            if isinstance(output, Core.CompileError):
                errors.append(output)
                # Panic and move to the next line/file
                _, outcome = reader.get()
                while outcome == ReadResult.Read and reader.reading():
                    _, outcome = reader.get()
            else:
                if len(output) == 1 and output[0].string == "include":
                    reader.removeWhitespace()
                    iFile = Scanner.tokeniseString(reader)
                    if isinstance(iFile, Core.CompileError):
                        errors.append(iFile)
                    else:
                        filepath = iFile[0].string[1:-1]
                        fileError = reader.openFile(filepath)
                        if fileError is not None:
                            errors.append(fileError)
                else:
                    for t in output:
                        tokens.append(t)

        if len(errors) > 0:
            return False, errors
        return True, tokens
