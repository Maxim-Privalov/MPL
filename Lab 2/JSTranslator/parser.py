from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Type


@dataclass
class Node:
    pass

@dataclass(kw_only=True)
class Block(Node):
    parent : Optional[Block] = None
    variables : list[str] = field(default_factory=list)
    lines : list[Node]
    indent : int

@dataclass
class GLOBAL(Block):
    pass

@dataclass
class BlockIF(Block):
    condition : Optional[Node] = None

@dataclass
class BlockELSEIF(Block):
    condition : Optional[Node] = None

@dataclass
class BlockELSE(Block):
    pass

@dataclass
class BlockWHILE(Block):
    condition : Optional[Node] = None

@dataclass
class BlockFUNCTION(Block):
    name : str

@dataclass
class BinaryOperator(Node):
    op : str
    primary : bool
    left : Node
    right : Node

@dataclass
class UnaryOperator(Node):
    op : str
    primary : bool
    operand : Node

@dataclass
class CallOperator(Node):
    name : str
    arguments : Node

@dataclass
class Keyword(Node):
    name : str

@dataclass
class LiteralNumber(Node):
    value : float

@dataclass
class StringType(Node):
    content : str

@dataclass
class BooleanType(Node):
    value : bool

@dataclass
class Variable(Node):
    name : str
    declaration : bool


class Parser:
    BLOCK_TYPES = {
        "if" : BlockIF,
        "elif" : BlockELSEIF,
        "else" : BlockELSE,
        "while" : BlockWHILE,
    }
    
    OPERATORS = {
        "P1" : ["++", "--"],
        "P2" : ["*", "/", "//", "%"],
        "P3" : ["+", "-"],
        "P4" : ["==", "<=", ">=", ">", "<", "!="],
        "P5" : ["not"],
        "P6" : ["and"],
        "P7" : ["or"],
        "P8" : ["=", "+=", "-=", "*=", "/="]
    }
    KEYWORDS = ["break", "continue"]
    OPERATORS_UNARY = ["++", "--", "not"]
    OPERATORS_BINARY = ["=", "+=", "-=", "*=", "/=", "or", "and", "==", "<=", ">=", ">", "<", "!=", "+", "-", "*", "/", "//", "%"]

    def __init__(self, token_lines):
        self.token_lines = token_lines
        self.li = 0
        self.ci = 0

    def increment_index(self):
        self.ci += 1

    @property
    def current_token(self):
        return self.token_lines[self.li][0][self.ci]
    
    @property
    def current_tokens_line(self):
        return self.token_lines[self.li][0]

    @property
    def current_line_indent(self):
        return self.token_lines[self.li][1]
    
    @staticmethod
    def check_declaration(block : Block, name : str) -> bool:
        current_block = block
        while current_block != None:
            for var in current_block.variables:
                if var == name:
                    return True
                
            current_block = current_block.parent

        return False

    def parseBlock(self, BlockType : Type[Block], parent : Block = None, indent : int = 0) -> Block:
        # Создание блока
        block = BlockType(lines=[], parent=parent, indent=indent)
        # Работа с заголовком инструкции
        if (BlockType != GLOBAL):
            self.li -= 1
            self.ci = 0
            while self.current_token != ":":
                self.increment_index()
                
                if (self.ci == (len(self.current_tokens_line) - 1) and self.current_token != ":"):
                    raise SyntaxError(f"expected end of  (:) on {self.li + 1} token {self.ci + 1}")
                
                if isinstance(block, (BlockIF, BlockELSEIF, BlockWHILE)):
                    if self.current_token == ":":
                        raise SyntaxError(f"expected contition on token {self.ci + 1} on line {self.li + 1}")
                    block.condition = self.parseP7(block, terminators = {":"})

                else:
                    if len(self.current_tokens_line) != 2 or self.current_tokens_line[self.ci] != ":":
                        raise SyntaxError(f"expected end of  (:) on {self.li + 1} token {self.ci + 1}")
                    
                if self.ci >= len(self.current_tokens_line):
                    raise SyntaxError(f"expected : symbol, line {self.li + 1}")
                    
            self.li += 1
        
        block_indent = 0
        while self.li < len(self.token_lines):
            self.ci = 0
            first_token = self.current_token
            if (first_token in self.BLOCK_TYPES.keys()):
                # Если отступы больше, то ошибка
                if (self.current_line_indent > block.indent):
                    raise SyntaxError(f"inconsisted indentation {self.li + 1}")
                
                # Если оступы меньше, то выходим из текущего блока
                if (self.current_line_indent != block.indent):
                    break
                
                # берём отступ объявнения инструкции
                head_indent = self.current_line_indent
                # шаг вниз
                self.li += 1
                # новый отступ (может быть пользовательским, главное чтобы не нулевой или отрицательный)
                # Нельзя!
                #   if (условие):
                #  print("12") 
                block_indent = self.current_line_indent
                if (head_indent >= block_indent):
                    raise SyntaxError(f"inconsisted indentation {self.li + 1}")
                
                # пишем в блок новый блок учитывая его (тип, родителя и новый отступ) рекурсивно вызывая его создание
                block.lines.append(self.parseBlock(parent=block, BlockType=self.BLOCK_TYPES.get(first_token), indent=block_indent))

            else:
                # Если отступы больше, то ошибка
                if (self.current_line_indent > block.indent):
                    raise SyntaxError(f"inconsisted indentation {self.li + 1}")
                
                # Если оступы меньше, то выходим из текущего блока
                if (self.current_line_indent != block.indent):
                    break
                
                # записываем строку и спускаемя ниже
                if (self.current_token in self.KEYWORDS):
                    if len(self.current_tokens_line) != 1:
                        raise SyntaxError(f"Undefined token after keyword, line {self.li + 1}")
                    block.lines.append(Keyword(self.current_token))
                else:
                    block.lines.append(self.parseP8(block))
                self.li += 1

                
        return block
    

    # assigment expressions
    def parseP8(self, block : Block, primary : bool = False, terminators : set[str] = {}) -> Node:
        result = self.parseP7(block, terminators = terminators)
        if (
            self.ci < len(self.current_tokens_line) and 
            not(self.current_token in self.OPERATORS_BINARY) and
            self.current_token != ")"
            ):
            if not(self.current_token in terminators):
                raise SyntaxError(f"expected operator on token {self.ci + 1} on line {self.li + 1}")

        while self.ci < len(self.current_tokens_line) and self.current_token in self.OPERATORS["P8"]:
            operator = self.current_token
            self.increment_index()
            right = self.parseP7(block, terminators = terminators)
            result = BinaryOperator(operator, primary, result, right)

        return result

    # logic expressions
    def parseP7(self, block : Block, primary : bool = False, terminators : set[str] = {}) -> Node:
        result = self.parseP6(block, terminators = terminators)
        if (
            self.ci < len(self.current_tokens_line) and 
            not(self.current_token in self.OPERATORS_BINARY) and
            self.current_token != ")"
            ):
            if not(self.current_token in terminators):
                raise SyntaxError(f"expected operator on token {self.ci + 1} on line {self.li + 1}")

        while self.ci < len(self.current_tokens_line) and self.current_token in self.OPERATORS["P7"]:
            operator = self.current_token
            self.increment_index()
            right = self.parseP6(block, terminators = terminators)
            result = BinaryOperator(operator, primary, result, right)

        return result
    
    def parseP6(self, block, primary : bool = False, terminators : set[str] = {}) -> Node:
        result = self.parseP5(block, terminators = terminators)
        if (
            self.ci < len(self.current_tokens_line) and 
            not(self.current_token in self.OPERATORS_BINARY) and
            self.current_token != ")"
            ):
            if not(self.current_token in terminators):
                raise SyntaxError(f"expected operator on token {self.ci + 1} on line {self.li + 1}")
        
        while self.ci < len(self.current_tokens_line) and self.current_token in self.OPERATORS["P6"]:
            operator = self.current_token
            self.increment_index()
            right = self.parseP5(block, terminators = terminators)
            result = BinaryOperator(operator, primary, result, right)

        return result

    def parseP5(self, block : Block, primary : bool = False, terminators : set[str] = {}) -> Node:
        operator = self.current_token
        if operator in self.OPERATORS["P5"]:
            self.increment_index()
            operand = self.parseP4(block, terminators = terminators)
            result = UnaryOperator(operator, primary, operand)
        else:
            result = self.parseP4(block, terminators = terminators)

        return result

    def parseP4(self, block : Block, primary : bool = False, terminators : set[str] = {}) -> Node:
        result = self.parseP3(block, terminators = terminators)
        if (
            self.ci < len(self.current_tokens_line) and 
            not(self.current_token in self.OPERATORS_BINARY) and
            self.current_token != ")"
            ):
            if not(self.current_token in terminators):
                raise SyntaxError(f"expected operator on token {self.ci + 1} on line {self.li + 1}")
        
        while self.ci < len(self.current_tokens_line) and self.current_token in self.OPERATORS["P4"]:
            operator = self.current_token
            self.increment_index()
            right = self.parseP3(block, terminators = terminators)
            result = BinaryOperator(operator, primary, result, right)

        return result
    
    def parseP3(self, block : Block, primary : bool = False, terminators : set[str] = {}) -> Node:
        result = self.parseP2(block, terminators = terminators)
        if (
            self.ci < len(self.current_tokens_line) and 
            not(self.current_token in self.OPERATORS_BINARY) and
            self.current_token != ")"
            ):
            if not(self.current_token in terminators):
                raise SyntaxError(f"expected operator on token {self.ci + 1} on line {self.li + 1}")

        while self.ci < len(self.current_tokens_line) and self.current_token in self.OPERATORS["P3"]:
            operator = self.current_token
            self.increment_index()
            right = self.parseP2(block, terminators = terminators)
            result = BinaryOperator(operator, primary, result, right)

        return result
    
    def parseP2(self, block : Block, primary : bool = False, terminators : set[str] = {}) -> Node:
        result = self.parseP1(block)
        if (
            self.ci < len(self.current_tokens_line) and 
            not(self.current_token in self.OPERATORS_BINARY) and
            self.current_token != ")"
            ):
            if not(self.current_token in terminators):
                raise SyntaxError(f"expected operator on token {self.ci + 1} on line {self.li + 1}")

        while self.ci < len(self.current_tokens_line) and self.current_token in self.OPERATORS["P2"]:
            operator = self.current_token
            self.increment_index()
            right = self.parseP1(block)
            result = BinaryOperator(operator, primary, result, right)

        return result
    
    def parseP1(self, block : Block, primary : bool = False) -> Node:
        operator = self.current_token
        if (operator in self.OPERATORS["P1"]):
            self.increment_index()
            operand = self.parseCall(block)
            result = UnaryOperator(operator, primary, operand)
        else:
            result = self.parseCall(block)

        return result
    
    def parseCall(self, block) -> Node:
        call_name = self.current_token
        if (not(self.current_token[0].isdigit()) and
            (self.ci + 2 < len(self.current_tokens_line) and self.current_tokens_line[self.ci + 1] == "(")):
            self.increment_index()
            self.increment_index()

            args = []

            if self.current_token != ")":
                while True:
                    args.append(self.parseP8(block, terminators={",", ")"}))

                    if self.current_token == ")":
                        break
                    if self.current_token == ",":
                        self.increment_index()
                        continue
                    else:
                        raise SyntaxError(f"Expected , or ) in argument list, got {self.current_token}")

            self.increment_index()
            result = CallOperator(name=call_name, arguments=args)
        else:
            result = self.parseFactor(block)

        return result

    def parseFactor(self, block : Block) -> Node:
        current_token = self.current_token
        if (current_token == "("):
            self.increment_index()
            result = self.parseP8(block, primary = True)
            if self.ci < len(self.current_tokens_line) and self.current_token == ")":
                self.increment_index()
            else:
                raise SyntaxError("expected )")
        else:
            if current_token[0] == '"':
                result = StringType(current_token)
            elif current_token in ["True", "False"]:
                result = BooleanType(current_token == "True")
            elif current_token[0].isdigit():
                result = LiteralNumber(current_token)
            else:
                declaration = not(Parser.check_declaration(block, self.current_token))
                if declaration:
                    block.variables.append(self.current_token)

                result = Variable(current_token, declaration)

            self.increment_index()
        return result
    
    @staticmethod
    def bypass(root : Node, indent : int):

        if (isinstance(root, Block)):
            print(" " * indent + root.__class__.__name__)
            if (isinstance(root, (BlockIF, BlockELSEIF, BlockWHILE))):
                print(" " * indent + "<=>")
                Parser.bypass(root.condition, indent)
                print(" " * indent + "<code>")

            for line in root.lines:
                Parser.bypass(line, indent + 4)


        if (isinstance(root, LiteralNumber)):
            print(" " * indent + root.value)

        if (isinstance(root, StringType)):
            print(" " * indent + root.content)
            
        if (isinstance(root, BooleanType)):
            print(" " * indent + str(root.value))

        if (isinstance(root, Variable)):
            print(" " * indent + root.name + " dec=" + str(root.declaration))

        if (isinstance(root, BinaryOperator)):
            print(" " * indent + root.op)
            Parser.bypass(root.left, indent + 2)
            Parser.bypass(root.right, indent + 2)

        if (isinstance(root, CallOperator)):
            print(" " * indent + root.name)
            for arg in root.arguments:
                Parser.bypass(arg, indent + 2)

        if (isinstance(root, UnaryOperator)):
            print(" " * indent + root.op)
            Parser.bypass(root.operand, indent + 2)
