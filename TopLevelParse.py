from Structures import *
from common import *
from Tokeniser import TokenType

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
    
    def __parseGetFunc(self) -> PreParseFunction:
        tList: Tokeniser = self.brain.tList
        tList.next()
        functionNameToken = tList.expect(TokenType.Identifier)
        tList.expect(TokenType.OpenBracket)
        
        signitureTokens: list[Token] = []
        openDepth = 1
        while openDepth > 0:
            nextToken = tList.next()
            signitureTokens.append(nextToken)
            if nextToken.ttype == TokenType.OpenBracket:
                openDepth += 1
            elif nextToken.ttype == TokenType.CloseBracket:
                openDepth -= 1
        while tList.peekType() != TokenType.OpenBrace:
            signitureTokens.append(tList.next())

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
            functionNameToken, FunctionType(NoneType(), []), signitureTokens, [], bodyTokens
        )
        return preParseFunc

    def parse(self) -> tuple[ParseBrain, bool]:
        # Quick escape if we weren't able to find the first file
        if len(self.brain.errors) > 0:
            return self.brain, False

        classDefs: list[tuple[Token, list[Token]]] = []

        tList: Tokeniser = self.brain.tList
        while tList.canTokenise() and len(self.brain.errors) < MAXIMUM_ERROR_COUNT:
            try:
                match tList.peekType():
                    # TODO: We shouldn't do these right away
                    # Make empty types for classes, then do aliases, then parse the class
                    case TokenType.Alias:
                        tList.next()
                        newTypeName = tList.expect(TokenType.Identifier)
                        tList.expectString("=")
                        newType = parseType(tList, self.brain.globalFrame.typeDict)
                        if isinstance(newType, SylphError):
                            raise newType
                        self.brain.globalFrame.typeDict[newTypeName.rep] = newType
                    case TokenType.Class:
                        tList.next()
                        className = tList.expect(TokenType.Identifier)
                        classTokens: list[Token] = []
                        tList.expect(TokenType.OpenBrace)
                        braceDepth = 1
                        while braceDepth > 0:
                            nextToken = tList.next()
                            if nextToken.ttype == TokenType.CloseBrace:
                                braceDepth -= 1
                                if braceDepth > 0:
                                    classTokens.append(nextToken)
                            else:
                                classTokens.append(nextToken)
                                if nextToken.ttype == TokenType.OpenBrace:
                                    braceDepth += 1
                        classDefs.append((className, classTokens))
                    case TokenType.Func:
                        preParseFunc = self.__parseGetFunc()
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
        
        #TODO: Classes
        if len(classDefs) > 0:
            raise SylphError(classDefs[0][0].sourceInfo, ErrorType.Unknown, ["Haven't implemented classes yet"])

        print("Time to parse the ppf")
        for funcList in self.brain.globalFrame.preParsedFunctions.values():
            for ppf in funcList:
                print("Parsing", ppf.token.rep)
                e = ppf.generateSigniture(self.brain.globalFrame.typeDict)
                if e is not None:
                    print("Oh no, error")
                    self.brain.errors.append(e)
                    if len(self.brain.errors) >= MAXIMUM_ERROR_COUNT:
                        break
            if len(self.brain.errors) >= MAXIMUM_ERROR_COUNT:
                break
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