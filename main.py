from Scanner.Scanner import Scanner
from Parser.StructurePass import StructurePass
import Parser.AST
import Parser.FunctionPass as FunctionPass
from Parser.Types import SymbolFrame
from Parser.TokenList import TokenList
from Core import CompileError
import sys

success, scannerResult = Scanner.scan("simple.syl")
if not success:
    print("Scanner Errors:")
    for error in scannerResult:
        print("\t", error)
    sys.exit(-1)

success, structureResult = StructurePass(scannerResult)
if not success:
    print("Structure Pass Errors:")
    for error in scannerResult:
        print("\t", error)
    sys.exit(-1)

success, errors = structureResult.verify()
if not success:
    print("Verification Errors")
    for error in errors:
        print("\t", error)
    sys.exit(-1)

print(str(structureResult))