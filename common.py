from dataclasses import dataclass
from enum import Enum
import os

@dataclass
class SourceInfo:
    column: int
    line: int
    filename: str

    def __str__(self):
        return self.filename + ":" + str(self.line) + "." + str(self.column)

class ErrorType(Enum):
    NoError,\
    FileNotFound,\
    UnexpectedEOF,\
    UnrecognisedToken,\
    UnexpectedTokenAtTopLevel,\
    UnexpectedToken,\
    ExpectedType,\
    Unknown = range(0, 8)

ErrorMessageMap: dict[ErrorType, str] = {
    ErrorType.NoError: "There is no error- you shouldn't be seeing this",
    ErrorType.FileNotFound: "FileError: Cannot find requested file",
    ErrorType.UnexpectedEOF: "FileError: Unexpected EOF",
    ErrorType.UnrecognisedToken: "TokenError: Unrecognised token type",
    ErrorType.UnexpectedTokenAtTopLevel: "ParseError: Unexpected token at top level",
    ErrorType.UnexpectedToken: "ParseError: Unexpected token (expected %0, found %1)",
    ErrorType.ExpectedType: "ParseError: Identifier is not a type",
    ErrorType.Unknown: r"UnknownError: This type of error is unknown! Details: %0 %1 %2"
}

class SylphError(Exception):
    def __init__(self, sourceInfo: SourceInfo, errorType: ErrorType, fillerStrings: list[str] = []):
        self.sourceInfo: SourceInfo = sourceInfo
        self.errorType: ErrorType = errorType
        self.fillerStrings: list[str] = fillerStrings
        super().__init__(self, self.getErrorString())

    def getErrorString(self) -> str:
        msg = "Error in " + str(self.sourceInfo) + "\n"
        if os.path.exists(self.sourceInfo.filename):
            o = open(self.sourceInfo.filename)
            lines = o.readlines()
            o.close()
            if len(lines) > self.sourceInfo.line:
                msg += lines[self.sourceInfo.line].rstrip() + "\n"
                msg += "".join(['~' for i in range(self.sourceInfo.column)]) + "^\n"
        errorMsg = ErrorMessageMap[self.errorType]
        for i in range(len(self.fillerStrings)):
            errorMsg.replace("%" + str(i), self.fillerStrings[i])
        msg += errorMsg

        return msg

    def printError(self):
        print(self.getErrorString())

def orError(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SylphError as error:
            return error
    return wrapper