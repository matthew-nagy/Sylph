from Structures import *
from common import *
from Tokeniser import TokenType

# TODO: Currently, function types for arguments and return types are parsed before imports are finished
# This should be delayed a but until we are sure that all types have been defined

class TopLevelParser:
    def __init__(self, startingFile: str):
        typeDict: TypeDict = {
            "bool": BoolType(), "byte": ByteType(), "float": FloatType(32), "double": FloatType(64),
            "i8": IntType(8, True), "i16": IntType(16, True), "i32": IntType(32, True), "i64": IntType(64, True),
            "u8": IntType(8, False), "u16": IntType(16, False), "u32": IntType(32, False), "u64": IntType(64, False),
            "string": StringType(), "None": NoneType()
        }
        self.brain: ParseBrain = ParseBrain(GlobalFrame(typeDict), Tokeniser(), [])
        errorType = self.brain.tList.addFile(startingFile)
        if errorType != ErrorType.NoError:
            self.brain.errors.append(SylphError(SourceInfo(0, 0, startingFile), errorType))
    
    def parse(self) -> tuple[ParseBrain, bool]:
        # Quick escape if we weren't able to find the first file
        if len(self.brain.errors) > 0:
            return self.brain, False

        tList: Tokeniser = self.brain.tList
        while tList.canTokenise() and len(self.brain.errors) < MAXIMUM_ERROR_COUNT:
            try:
                match tList.peekType():
                    case TokenType.Alias:
                        tList.next()
                        newTypeName = tList.expect(TokenType.Identifier)
                        tList.expectString("=")
                        newType = parseType(tList, self.brain.globalFrame.typeDict)
                        if isinstance(newType, SylphError):
                            raise newType
                        self.brain.globalFrame.typeDict[newTypeName.rep] = newType
                    case TokenType.Class:
                        # TODO: Implement this!
                        raise SylphError(tList.peek().sourceInfo, ErrorType.Unknown, ["Haven't implemented classes yet"])
                    case TokenType.Func:
                        tList.next()
                        functionNameToken = tList.expect(TokenType.Identifier)
                        tList.expect(TokenType.OpenBracket)
                        argumentTokens: list[Token] = []
                        argumentTypes: list[SylphType] = []
                        while tList.peekType() != TokenType.CloseBracket:
                            if len(argumentTokens) > 0:
                                tList.expect(TokenType.Comma)
                            argumentTokens.append(tList.expect(TokenType.Identifier))
                            tList.expect(TokenType.Colon)
                            argType = parseType(tList, self.brain.globalFrame.typeDict)
                            if isinstance(argType, SylphError):
                                raise argType
                            argumentTypes.append(argType)
                        
                        tList.expect(TokenType.CloseBracket)
                        returnType = NoneType()
                        if tList.peekType() != TokenType.OpenBrace:
                            tList.expectString("->")
                            returnType = parseType(tList, self.brain.globalFrame.typeDict)
                            if isinstance(returnType, SylphError):
                                raise returnType

                        bodyTokens: list[Token] = []
                        tList.expect(TokenType.OpenBrace)
                        depth = 1
                        while depth > 0:
                            if tList.peekType() == TokenType.OpenBrace:
                                depth += 1
                                bodyTokens.append(tList.next())
                            elif tList.peekType() == TokenType.CloseBrace:
                                depth -= 1
                                cb = tList.next()
                                if depth > 0:
                                    bodyTokens.append(cb)
                            else:
                                bodyTokens.append(tList.next())

                        preParseFunc: PreParseFunction = PreParseFunction(
                            functionNameToken, FunctionType(returnType, argumentTypes), argumentTokens, bodyTokens
                        )
                        self.brain.globalFrame.registerFunction(preParseFunc)

                    case TokenType.Import:
                        tList.next()
                        filename = tList.expect(TokenType.StringLiteral)
                        e = tList.addFile(filename.rep)
                        if e != ErrorType.NoError:
                            raise SylphError(filename.sourceInfo, e)
                    case TokenType.EndOfFile:
                        # Move it along                        
                        tList.next()
                    case _:
                        errorToken = tList.next()
                        self.brain.errors.append(SylphError(errorToken.sourceInfo, ErrorType.UnexpectedTokenAtTopLevel))
                        # Synchronise
                        while tList.canTokenise() and tList.peek().sourceInfo.line == errorToken.sourceInfo.line:
                            tList.next()
            except SylphError as error:
                print("Error caught")
                self.brain.errors.append(error)
        return self.brain, len(self.brain.errors) == 0
        
if __name__ == "__main__":
    tlp = TopLevelParser("tests/Simple/TopLevelParse.syl")
    brain, success = tlp.parse()
    if not success:
        print("Errors:")
        for error in brain.errors:
            error.printError()
    else:
        for ppf_list in brain.globalFrame.preParsedFunctions.values():
            for ppf in ppf_list:
                print(ppf)
        print(brain.globalFrame.typeDict)