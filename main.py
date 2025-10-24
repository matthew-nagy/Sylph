from Scanner.Scanner import Scanner
from Parser.StructurePass import StructurePass
import Parser.AST
import Parser.FunctionPass as FunctionPass
from Parser.Types import SymbolFrame
from Parser.TokenList import TokenList

# succeeded, results = Scanner.scan("test.syl")
# if succeeded:
#     succeeded, module = StructurePass(results)
#     if succeeded:
#         print("Structure Module")
#         print("TYPES")
#         print(module.types)
#         print("FUNCTIONS")
#         print(module.functions)
#     else:
#         print("Errors:")
#         for error in module:
#             print(error)
# else:
#     print("Errors:")
#     for error in results:
#         print(error)

_, module = StructurePass(Scanner.scan("simple.syl")[1])
frame = SymbolFrame(None)
frame.module = module
errors = []
print(FunctionPass.parseExpression(TokenList(module.functions["a"].definition), module.types, frame, errors))
for e in errors:
    print(e)