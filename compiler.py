#!/usr/bin/env python3
"""
============================================================
COMPILER FRONTEND — Pure Python, No External Libraries
============================================================
A complete compiler frontend with:
  1. Lexer (Tokenizer)
  2. Parser (Recursive Descent)
  3. Semantic Analyzer

Usage:
  python compiler.py                    # Interactive mode
  python compiler.py source.txt         # Compile a file
  python compiler.py -e "let x = 10;"   # Compile a string

Author: Generated for educational purposes
============================================================
"""

import sys
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict


# ============================================================
# PART 1: LEXER (Tokenizer / Scanner)
# ============================================================

class TokenType(Enum):
    """All token types recognized by our language."""
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Keywords
    LET = auto()
    CONST = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    FUNCTION = auto()
    RETURN = auto()
    TRUE = auto()
    FALSE = auto()
    PRINT = auto()

    # Operators
    PLUS = auto()        # +
    MINUS = auto()       # -
    STAR = auto()        # *
    SLASH = auto()       # /
    PERCENT = auto()     # %
    ASSIGN = auto()      # =
    EQUALS = auto()      # ==
    NOT_EQUALS = auto()  # !=
    LESS = auto()        # <
    GREATER = auto()     # >
    LESS_EQ = auto()     # <=
    GREATER_EQ = auto()  # >=
    AND = auto()         # &&
    OR = auto()          # ||
    NOT = auto()         # !

    # Delimiters
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    LBRACE = auto()      # {
    RBRACE = auto()      # }
    LBRACKET = auto()    # [
    RBRACKET = auto()    # ]
    SEMICOLON = auto()   # ;
    COMMA = auto()       # ,

    # Special
    EOF = auto()


@dataclass
class Token:
    """Represents a single token from the source code."""
    type: TokenType
    value: str
    line: int
    column: int


KEYWORDS: Dict[str, TokenType] = {
    'let': TokenType.LET,
    'const': TokenType.CONST,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'for': TokenType.FOR,
    'function': TokenType.FUNCTION,
    'return': TokenType.RETURN,
    'true': TokenType.TRUE,
    'false': TokenType.FALSE,
    'print': TokenType.PRINT,
}

ESCAPE_MAP: Dict[str, str] = {
    'n': '\n', 't': '\t', 'r': '\r',
    '\\': '\\', '"': '"', "'": "'",
}

TWO_CHAR_OPS: Dict[str, TokenType] = {
    '==': TokenType.EQUALS,
    '!=': TokenType.NOT_EQUALS,
    '<=': TokenType.LESS_EQ,
    '>=': TokenType.GREATER_EQ,
    '&&': TokenType.AND,
    '||': TokenType.OR,
}

SINGLE_CHAR_OPS: Dict[str, TokenType] = {
    '+': TokenType.PLUS,   '-': TokenType.MINUS,
    '*': TokenType.STAR,   '/': TokenType.SLASH,
    '%': TokenType.PERCENT, '=': TokenType.ASSIGN,
    '<': TokenType.LESS,   '>': TokenType.GREATER,
    '!': TokenType.NOT,    '(': TokenType.LPAREN,
    ')': TokenType.RPAREN, '{': TokenType.LBRACE,
    '}': TokenType.RBRACE, '[': TokenType.LBRACKET,
    ']': TokenType.RBRACKET, ';': TokenType.SEMICOLON,
    ',': TokenType.COMMA,
}


class Lexer:
    """
    Reads source code character by character and produces a list of tokens.
    Handles whitespace, comments, numbers, strings, identifiers, and operators.
    """

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.errors: List[str] = []

    def peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else '\0'

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def add_token(self, token_type: TokenType, value: str,
                  line: int, column: int) -> None:
        self.tokens.append(Token(token_type, value, line, column))

    def skip_single_line_comment(self) -> None:
        while self.pos < len(self.source) and self.peek() != '\n':
            self.advance()

    def skip_multi_line_comment(self) -> None:
        self.advance()  # /
        self.advance()  # *
        while self.pos < len(self.source):
            if self.peek() == '*' and self.peek(1) == '/':
                self.advance()  # *
                self.advance()  # /
                return
            self.advance()
        self.errors.append(f"Line {self.line}: Unterminated multi-line comment")

    def read_number(self, start_line: int, start_col: int) -> None:
        num = ''
        while self.pos < len(self.source) and self.peek().isdigit():
            num += self.advance()
        if self.pos < len(self.source) and self.peek() == '.':
            num += self.advance()
            while self.pos < len(self.source) and self.peek().isdigit():
                num += self.advance()
        self.add_token(TokenType.NUMBER, num, start_line, start_col)

    def read_string(self, start_line: int, start_col: int) -> None:
        quote = self.advance()
        string_val = ''
        while self.pos < len(self.source) and self.peek() != quote and self.peek() != '\n':
            if self.peek() == '\\':
                self.advance()
                string_val += ESCAPE_MAP.get(self.advance(), '')
            else:
                string_val += self.advance()
        if self.pos < len(self.source) and self.peek() == quote:
            self.advance()
            self.add_token(TokenType.STRING, string_val, start_line, start_col)
        else:
            self.errors.append(f"Line {start_line}: Unterminated string literal")

    def read_identifier(self, start_line: int, start_col: int) -> None:
        ident = ''
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == '_'):
            ident += self.advance()
        self.add_token(KEYWORDS.get(ident, TokenType.IDENTIFIER), ident, start_line, start_col)

    def tokenize(self) -> Tuple[List[Token], List[str]]:
        """Main tokenization loop. Returns (tokens, errors)."""
        while self.pos < len(self.source):
            start_line = self.line
            start_col = self.column
            ch = self.peek()

            if ch in ' \t\r\n':
                self.advance()
                continue

            if ch == '/' and self.peek(1) == '/':
                self.skip_single_line_comment()
                continue

            if ch == '/' and self.peek(1) == '*':
                self.skip_multi_line_comment()
                continue

            if ch.isdigit():
                self.read_number(start_line, start_col)
                continue

            if ch in '"\'':
                self.read_string(start_line, start_col)
                continue

            if ch.isalpha() or ch == '_':
                self.read_identifier(start_line, start_col)
                continue

            two = self.source[self.pos:self.pos + 2]
            if two in TWO_CHAR_OPS:
                self.advance()
                self.advance()
                self.add_token(TWO_CHAR_OPS[two], two, start_line, start_col)
                continue

            if ch in SINGLE_CHAR_OPS:
                self.advance()
                self.add_token(SINGLE_CHAR_OPS[ch], ch, start_line, start_col)
                continue

            self.errors.append(f"Line {start_line}: Unexpected character '{ch}'")
            self.advance()

        self.add_token(TokenType.EOF, '', self.line, self.column)
        return self.tokens, self.errors


# ============================================================
# PART 2: AST NODE DEFINITIONS
# ============================================================

@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    pass


@dataclass
class Program(ASTNode):
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class NumericLiteral(ASTNode):
    value: float = 0


@dataclass
class StringLiteral(ASTNode):
    value: str = ""


@dataclass
class BooleanLiteral(ASTNode):
    value: bool = False


@dataclass
class Identifier(ASTNode):
    name: str = ""


@dataclass
class ArrayExpr(ASTNode):
    elements: List[ASTNode] = field(default_factory=list)


@dataclass
class BinaryExpr(ASTNode):
    operator: str = ""
    left: ASTNode = None
    right: ASTNode = None


@dataclass
class UnaryExpr(ASTNode):
    operator: str = ""
    operand: ASTNode = None


@dataclass
class AssignmentExpr(ASTNode):
    name: str = ""
    value: ASTNode = None


@dataclass
class CallExpr(ASTNode):
    callee: ASTNode = None
    arguments: List[ASTNode] = field(default_factory=list)


@dataclass
class MemberExpr(ASTNode):
    obj: ASTNode = None
    prop: ASTNode = None
    computed: bool = False


@dataclass
class VarDeclaration(ASTNode):
    kind: str = "let"  # "let" or "const"
    name: str = ""
    init: Optional[ASTNode] = None


@dataclass
class FuncDeclaration(ASTNode):
    name: str = ""
    params: List[str] = field(default_factory=list)
    body: 'BlockStmt' = None


@dataclass
class BlockStmt(ASTNode):
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class IfStmt(ASTNode):
    test: ASTNode = None
    consequent: BlockStmt = None
    alternate: Optional[ASTNode] = None


@dataclass
class WhileStmt(ASTNode):
    test: ASTNode = None
    body: BlockStmt = None


@dataclass
class ForStmt(ASTNode):
    init: Optional[ASTNode] = None
    test: Optional[ASTNode] = None
    update: Optional[ASTNode] = None
    body: BlockStmt = None


@dataclass
class ReturnStmt(ASTNode):
    argument: Optional[ASTNode] = None


@dataclass
class PrintStmt(ASTNode):
    argument: ASTNode = None


@dataclass
class ExprStmt(ASTNode):
    expression: ASTNode = None


# ============================================================
# PART 3: PARSER (Recursive Descent)
# ============================================================

class Parser:
    """
    Recursive Descent Parser that builds an AST from tokens.

    Grammar (simplified):
      program     → statement*
      statement   → varDecl | funcDecl | ifStmt | whileStmt | forStmt
                  | returnStmt | printStmt | block | exprStmt
      expression  → assignment
      assignment  → IDENTIFIER "=" assignment | logicOr
      logicOr     → logicAnd ("||" logicAnd)*
      logicAnd    → equality ("&&" equality)*
      equality    → comparison (("==" | "!=") comparison)*
      comparison  → addition (("<" | ">" | "<=" | ">=") addition)*
      addition    → multiplication (("+" | "-") multiplication)*
      multiplication → unary (("*" | "/" | "%") unary)*
      unary       → ("!" | "-") unary | call
      call        → primary ("(" arguments? ")" | "[" expr "]")*
      primary     → NUMBER | STRING | "true" | "false" | IDENTIFIER
                  | "(" expr ")" | "[" elements? "]"
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errors: List[str] = []

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, '', 0, 0)

    def peek(self) -> TokenType:
        return self.current().type

    def peek_ahead(self, offset: int = 1) -> TokenType:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx].type
        return TokenType.EOF

    def advance(self) -> Token:
        token = self.current()
        self.pos += 1
        return token

    def expect(self, token_type: TokenType, message: str = "") -> Token:
        if self.peek() == token_type:
            return self.advance()
        tok = self.current()
        msg = message or f"Expected {token_type.name} but got {tok.type.name} ('{tok.value}')"
        self.errors.append(f"Line {tok.line}: {msg}")
        return tok

    def match(self, *types: TokenType) -> bool:
        if self.peek() in types:
            self.advance()
            return True
        return False

    # --- Grammar Rules ---

    def parse_program(self) -> Program:
        body = []
        while self.peek() != TokenType.EOF:
            try:
                body.append(self.parse_statement())
            except Exception:
                tok = self.current()
                self.errors.append(f"Line {tok.line}: Unexpected token '{tok.value}'")
                self.advance()
        return Program(body=body)

    def parse_statement(self) -> ASTNode:
        t = self.peek()
        if t in (TokenType.LET, TokenType.CONST):
            return self.parse_var_decl()
        elif t == TokenType.FUNCTION:
            return self.parse_func_decl()
        elif t == TokenType.IF:
            return self.parse_if_stmt()
        elif t == TokenType.WHILE:
            return self.parse_while_stmt()
        elif t == TokenType.FOR:
            return self.parse_for_stmt()
        elif t == TokenType.RETURN:
            return self.parse_return_stmt()
        elif t == TokenType.PRINT:
            return self.parse_print_stmt()
        elif t == TokenType.LBRACE:
            return self.parse_block()
        else:
            return self.parse_expr_stmt()

    def parse_var_decl(self) -> VarDeclaration:
        kind = self.advance().value  # 'let' or 'const'
        name = self.expect(TokenType.IDENTIFIER, "Expected variable name").value
        init = None
        if self.match(TokenType.ASSIGN):
            init = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "Expected ';' after variable declaration")
        return VarDeclaration(kind=kind, name=name, init=init)

    def parse_func_decl(self) -> FuncDeclaration:
        self.advance()  # 'function'
        name = self.expect(TokenType.IDENTIFIER, "Expected function name").value
        self.expect(TokenType.LPAREN, "Expected '(' after function name")
        params = []
        if self.peek() != TokenType.RPAREN:
            params.append(self.expect(TokenType.IDENTIFIER, "Expected parameter name").value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENTIFIER, "Expected parameter name").value)
        self.expect(TokenType.RPAREN, "Expected ')' after parameters")
        body = self.parse_block()
        return FuncDeclaration(name=name, params=params, body=body)

    def parse_if_stmt(self) -> IfStmt:
        self.advance()  # 'if'
        self.expect(TokenType.LPAREN, "Expected '(' after 'if'")
        test = self.parse_expression()
        self.expect(TokenType.RPAREN, "Expected ')' after condition")
        consequent = self.parse_block()
        alternate = None
        if self.match(TokenType.ELSE):
            alternate = self.parse_if_stmt() if self.peek() == TokenType.IF else self.parse_block()
        return IfStmt(test=test, consequent=consequent, alternate=alternate)

    def parse_while_stmt(self) -> WhileStmt:
        self.advance()  # 'while'
        self.expect(TokenType.LPAREN, "Expected '(' after 'while'")
        test = self.parse_expression()
        self.expect(TokenType.RPAREN, "Expected ')' after condition")
        body = self.parse_block()
        return WhileStmt(test=test, body=body)

    def parse_for_stmt(self) -> ForStmt:
        self.advance()  # 'for'
        self.expect(TokenType.LPAREN, "Expected '(' after 'for'")

        init = None
        if self.peek() in (TokenType.LET, TokenType.CONST):
            init = self.parse_var_decl()
        elif self.peek() != TokenType.SEMICOLON:
            init = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
        else:
            self.advance()  # ;

        test = None
        if self.peek() != TokenType.SEMICOLON:
            test = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "Expected ';' after for condition")

        update = None
        if self.peek() != TokenType.RPAREN:
            update = self.parse_expression()
        self.expect(TokenType.RPAREN, "Expected ')' after for clauses")

        body = self.parse_block()
        return ForStmt(init=init, test=test, update=update, body=body)

    def parse_return_stmt(self) -> ReturnStmt:
        self.advance()  # 'return'
        argument = None
        if self.peek() != TokenType.SEMICOLON:
            argument = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "Expected ';' after return")
        return ReturnStmt(argument=argument)

    def parse_print_stmt(self) -> PrintStmt:
        self.advance()  # 'print'
        self.expect(TokenType.LPAREN, "Expected '(' after 'print'")
        argument = self.parse_expression()
        self.expect(TokenType.RPAREN, "Expected ')' after print argument")
        self.expect(TokenType.SEMICOLON, "Expected ';' after print statement")
        return PrintStmt(argument=argument)

    def parse_block(self) -> BlockStmt:
        self.expect(TokenType.LBRACE, "Expected '{'")
        body = []
        while self.peek() != TokenType.RBRACE and self.peek() != TokenType.EOF:
            body.append(self.parse_statement())
        self.expect(TokenType.RBRACE, "Expected '}'")
        return BlockStmt(body=body)

    def parse_expr_stmt(self) -> ExprStmt:
        expr = self.parse_expression()
        self.expect(TokenType.SEMICOLON, "Expected ';' after expression")
        return ExprStmt(expression=expr)

    # --- Expression Parsing ---

    def parse_expression(self) -> ASTNode:
        return self.parse_assignment()

    def parse_assignment(self) -> ASTNode:
        if self.peek() == TokenType.IDENTIFIER and self.peek_ahead() == TokenType.ASSIGN:
            name = self.advance().value
            self.advance()  # =
            value = self.parse_assignment()  # right-associative
            return AssignmentExpr(name=name, value=value)
        return self.parse_logic_or()

    def parse_logic_or(self) -> ASTNode:
        left = self.parse_logic_and()
        while self.peek() == TokenType.OR:
            op = self.advance().value
            left = BinaryExpr(operator=op, left=left, right=self.parse_logic_and())
        return left

    def parse_logic_and(self) -> ASTNode:
        left = self.parse_equality()
        while self.peek() == TokenType.AND:
            op = self.advance().value
            left = BinaryExpr(operator=op, left=left, right=self.parse_equality())
        return left

    def parse_equality(self) -> ASTNode:
        left = self.parse_comparison()
        while self.peek() in (TokenType.EQUALS, TokenType.NOT_EQUALS):
            op = self.advance().value
            left = BinaryExpr(operator=op, left=left, right=self.parse_comparison())
        return left

    def parse_comparison(self) -> ASTNode:
        left = self.parse_addition()
        while self.peek() in (TokenType.LESS, TokenType.GREATER,
                               TokenType.LESS_EQ, TokenType.GREATER_EQ):
            op = self.advance().value
            left = BinaryExpr(operator=op, left=left, right=self.parse_addition())
        return left

    def parse_addition(self) -> ASTNode:
        left = self.parse_multiplication()
        while self.peek() in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            left = BinaryExpr(operator=op, left=left, right=self.parse_multiplication())
        return left

    def parse_multiplication(self) -> ASTNode:
        left = self.parse_unary()
        while self.peek() in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.advance().value
            left = BinaryExpr(operator=op, left=left, right=self.parse_unary())
        return left

    def parse_unary(self) -> ASTNode:
        if self.peek() in (TokenType.NOT, TokenType.MINUS):
            op = self.advance().value
            return UnaryExpr(operator=op, operand=self.parse_unary())
        return self.parse_call()

    def parse_call(self) -> ASTNode:
        expr = self.parse_primary()
        while True:
            if self.peek() == TokenType.LPAREN:
                self.advance()
                args = []
                if self.peek() != TokenType.RPAREN:
                    args.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expression())
                self.expect(TokenType.RPAREN, "Expected ')' after arguments")
                expr = CallExpr(callee=expr, arguments=args)
            elif self.peek() == TokenType.LBRACKET:
                self.advance()
                prop = self.parse_expression()
                self.expect(TokenType.RBRACKET, "Expected ']'")
                expr = MemberExpr(obj=expr, prop=prop, computed=True)
            else:
                break
        return expr

    def parse_primary(self) -> ASTNode:
        tok = self.current()

        if self.peek() == TokenType.NUMBER:
            self.advance()
            return NumericLiteral(value=float(tok.value))

        if self.peek() == TokenType.STRING:
            self.advance()
            return StringLiteral(value=tok.value)

        if self.peek() == TokenType.TRUE:
            self.advance()
            return BooleanLiteral(value=True)

        if self.peek() == TokenType.FALSE:
            self.advance()
            return BooleanLiteral(value=False)

        if self.peek() == TokenType.IDENTIFIER:
            self.advance()
            return Identifier(name=tok.value)

        if self.peek() == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')'")
            return expr

        if self.peek() == TokenType.LBRACKET:
            self.advance()
            elements = []
            if self.peek() != TokenType.RBRACKET:
                elements.append(self.parse_expression())
                while self.match(TokenType.COMMA):
                    elements.append(self.parse_expression())
            self.expect(TokenType.RBRACKET, "Expected ']'")
            return ArrayExpr(elements=elements)

        self.errors.append(f"Line {tok.line}: Unexpected token '{tok.value}'")
        self.advance()
        return Identifier(name="<error>")


# ============================================================
# PART 4: SEMANTIC ANALYZER
# ============================================================

@dataclass
class SymbolInfo:
    """Information about a declared symbol."""
    name: str
    kind: str  # 'variable', 'function', 'parameter'
    mutable: bool
    scope: int
    param_count: Optional[int] = None


class SemanticAnalyzer:
    """
    Walks the AST and performs semantic checks:
      - Undeclared variable usage
      - Duplicate declarations in same scope
      - Constant reassignment
      - Return statement outside function
      - Wrong number of function arguments
    """

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.scope_stack: List[Dict[str, SymbolInfo]] = [{}]
        self.all_symbols: List[SymbolInfo] = []
        self.scope_level = 0
        self.inside_function = False

    def current_scope(self) -> Dict[str, SymbolInfo]:
        return self.scope_stack[-1]

    def lookup(self, name: str) -> Optional[SymbolInfo]:
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def declare(self, name: str, kind: str, mutable: bool = True,
                param_count: Optional[int] = None) -> None:
        scope = self.current_scope()
        if name in scope:
            self.errors.append(f"'{name}' is already declared in this scope")
        info = SymbolInfo(name=name, kind=kind, mutable=mutable,
                          scope=self.scope_level, param_count=param_count)
        scope[name] = info
        self.all_symbols.append(info)

    def enter_scope(self) -> None:
        self.scope_level += 1
        self.scope_stack.append({})

    def exit_scope(self) -> None:
        self.scope_stack.pop()
        self.scope_level -= 1

    def analyze(self, node: ASTNode) -> None:
        method_name = f'visit_{type(node).__name__}'
        getattr(self, method_name, self.generic_visit)(node)

    def generic_visit(self, node: ASTNode) -> None:
        pass

    def visit_Program(self, node: Program) -> None:
        for stmt in node.body:
            self.analyze(stmt)

    def visit_VarDeclaration(self, node: VarDeclaration) -> None:
        if node.init:
            self.analyze(node.init)
        self.declare(node.name, 'variable', mutable=(node.kind == 'let'))

    def visit_FuncDeclaration(self, node: FuncDeclaration) -> None:
        self.declare(node.name, 'function', mutable=False, param_count=len(node.params))
        prev = self.inside_function
        self.inside_function = True
        self.enter_scope()
        for param in node.params:
            self.declare(param, 'parameter')
        self.analyze(node.body)
        self.exit_scope()
        self.inside_function = prev

    def visit_ReturnStmt(self, node: ReturnStmt) -> None:
        if not self.inside_function:
            self.errors.append("'return' used outside of a function")
        if node.argument:
            self.analyze(node.argument)

    def visit_IfStmt(self, node: IfStmt) -> None:
        self.analyze(node.test)
        self.enter_scope()
        self.analyze(node.consequent)
        self.exit_scope()
        if node.alternate:
            self.enter_scope()
            self.analyze(node.alternate)
            self.exit_scope()

    def visit_WhileStmt(self, node: WhileStmt) -> None:
        self.analyze(node.test)
        self.enter_scope()
        self.analyze(node.body)
        self.exit_scope()

    def visit_ForStmt(self, node: ForStmt) -> None:
        self.enter_scope()
        if node.init:
            self.analyze(node.init)
        if node.test:
            self.analyze(node.test)
        if node.update:
            self.analyze(node.update)
        self.analyze(node.body)
        self.exit_scope()

    def visit_BlockStmt(self, node: BlockStmt) -> None:
        for stmt in node.body:
            self.analyze(stmt)

    def visit_PrintStmt(self, node: PrintStmt) -> None:
        self.analyze(node.argument)

    def visit_ExprStmt(self, node: ExprStmt) -> None:
        self.analyze(node.expression)

    def visit_BinaryExpr(self, node: BinaryExpr) -> None:
        self.analyze(node.left)
        self.analyze(node.right)

    def visit_UnaryExpr(self, node: UnaryExpr) -> None:
        self.analyze(node.operand)

    def visit_AssignmentExpr(self, node: AssignmentExpr) -> None:
        sym = self.lookup(node.name)
        if sym is None:
            self.errors.append(f"Cannot assign to undeclared variable '{node.name}'")
        elif not sym.mutable:
            self.errors.append(f"Cannot reassign constant '{node.name}'")
        self.analyze(node.value)

    def visit_CallExpr(self, node: CallExpr) -> None:
        self.analyze(node.callee)
        for arg in node.arguments:
            self.analyze(arg)
        if isinstance(node.callee, Identifier):
            sym = self.lookup(node.callee.name)
            if sym and sym.kind == 'function' and sym.param_count is not None:
                if len(node.arguments) != sym.param_count:
                    self.warnings.append(
                        f"'{node.callee.name}' expects {sym.param_count} "
                        f"argument(s) but got {len(node.arguments)}"
                    )

    def visit_MemberExpr(self, node: MemberExpr) -> None:
        self.analyze(node.obj)
        self.analyze(node.prop)

    def visit_Identifier(self, node: Identifier) -> None:
        if node.name != "<error>" and self.lookup(node.name) is None:
            self.errors.append(f"Undeclared variable '{node.name}'")

    def visit_ArrayExpr(self, node: ArrayExpr) -> None:
        for el in node.elements:
            self.analyze(el)


# ============================================================
# PART 5: PRETTY PRINTING
# ============================================================

def print_tokens(tokens: List[Token]) -> None:
    print("\n" + "=" * 60)
    print("TOKENS")
    print("=" * 60)
    print(f"{'#':<4} {'Type':<15} {'Value':<20} {'Location':<10}")
    print("-" * 60)
    for i, tok in enumerate(tokens):
        val = repr(tok.value) if tok.value else '(empty)'
        print(f"{i:<4} {tok.type.name:<15} {val:<20} {tok.line}:{tok.column}")


class ASTPrinter:
    """Visitor that pretty-prints an AST to stdout."""

    def print(self, node: ASTNode, indent: int = 0) -> None:
        method_name = f'visit_{type(node).__name__}'
        getattr(self, method_name, self.generic_visit)(node, indent)

    def _line(self, indent: int, text: str) -> None:
        print("  " * indent + text)

    def generic_visit(self, node: ASTNode, indent: int) -> None:
        self._line(indent, f"{type(node).__name__}: {node}")

    def visit_Program(self, node: Program, indent: int) -> None:
        self._line(indent, "Program")
        for stmt in node.body:
            self.print(stmt, indent + 1)

    def visit_NumericLiteral(self, node: NumericLiteral, indent: int) -> None:
        self._line(indent, f"NumericLiteral: {node.value}")

    def visit_StringLiteral(self, node: StringLiteral, indent: int) -> None:
        self._line(indent, f'StringLiteral: "{node.value}"')

    def visit_BooleanLiteral(self, node: BooleanLiteral, indent: int) -> None:
        self._line(indent, f"BooleanLiteral: {node.value}")

    def visit_Identifier(self, node: Identifier, indent: int) -> None:
        self._line(indent, f"Identifier: {node.name}")

    def visit_VarDeclaration(self, node: VarDeclaration, indent: int) -> None:
        self._line(indent, f"VarDeclaration ({node.kind}): {node.name}")
        if node.init:
            self.print(node.init, indent + 1)

    def visit_FuncDeclaration(self, node: FuncDeclaration, indent: int) -> None:
        self._line(indent, f"FuncDeclaration: {node.name}({', '.join(node.params)})")
        self.print(node.body, indent + 1)

    def visit_BlockStmt(self, node: BlockStmt, indent: int) -> None:
        self._line(indent, "Block")
        for stmt in node.body:
            self.print(stmt, indent + 1)

    def visit_IfStmt(self, node: IfStmt, indent: int) -> None:
        self._line(indent, "IfStmt")
        self._line(indent, "  test:")
        self.print(node.test, indent + 2)
        self._line(indent, "  then:")
        self.print(node.consequent, indent + 2)
        if node.alternate:
            self._line(indent, "  else:")
            self.print(node.alternate, indent + 2)

    def visit_WhileStmt(self, node: WhileStmt, indent: int) -> None:
        self._line(indent, "WhileStmt")
        self._line(indent, "  test:")
        self.print(node.test, indent + 2)
        self._line(indent, "  body:")
        self.print(node.body, indent + 2)

    def visit_ForStmt(self, node: ForStmt, indent: int) -> None:
        self._line(indent, "ForStmt")
        if node.init:
            self._line(indent, "  init:")
            self.print(node.init, indent + 2)
        if node.test:
            self._line(indent, "  test:")
            self.print(node.test, indent + 2)
        if node.update:
            self._line(indent, "  update:")
            self.print(node.update, indent + 2)
        self._line(indent, "  body:")
        self.print(node.body, indent + 2)

    def visit_ReturnStmt(self, node: ReturnStmt, indent: int) -> None:
        self._line(indent, "ReturnStmt")
        if node.argument:
            self.print(node.argument, indent + 1)

    def visit_PrintStmt(self, node: PrintStmt, indent: int) -> None:
        self._line(indent, "PrintStmt")
        self.print(node.argument, indent + 1)

    def visit_ExprStmt(self, node: ExprStmt, indent: int) -> None:
        self._line(indent, "ExprStmt")
        self.print(node.expression, indent + 1)

    def visit_BinaryExpr(self, node: BinaryExpr, indent: int) -> None:
        self._line(indent, f"BinaryExpr: {node.operator}")
        self.print(node.left, indent + 1)
        self.print(node.right, indent + 1)

    def visit_UnaryExpr(self, node: UnaryExpr, indent: int) -> None:
        self._line(indent, f"UnaryExpr: {node.operator}")
        self.print(node.operand, indent + 1)

    def visit_AssignmentExpr(self, node: AssignmentExpr, indent: int) -> None:
        self._line(indent, f"AssignmentExpr: {node.name} =")
        self.print(node.value, indent + 1)

    def visit_CallExpr(self, node: CallExpr, indent: int) -> None:
        self._line(indent, "CallExpr")
        self._line(indent, "  callee:")
        self.print(node.callee, indent + 2)
        self._line(indent, "  args:")
        for arg in node.arguments:
            self.print(arg, indent + 2)

    def visit_MemberExpr(self, node: MemberExpr, indent: int) -> None:
        self._line(indent, "MemberExpr")
        self.print(node.obj, indent + 1)
        self.print(node.prop, indent + 1)

    def visit_ArrayExpr(self, node: ArrayExpr, indent: int) -> None:
        self._line(indent, "ArrayExpr")
        for el in node.elements:
            self.print(el, indent + 1)


def print_semantic_results(analyzer: SemanticAnalyzer) -> None:
    print("\n" + "=" * 60)
    print("SEMANTIC ANALYSIS")
    print("=" * 60)

    if analyzer.errors:
        print("\n❌ ERRORS:")
        for err in analyzer.errors:
            print(f"   • {err}")

    if analyzer.warnings:
        print("\n⚠️  WARNINGS:")
        for warn in analyzer.warnings:
            print(f"   • {warn}")

    if not analyzer.errors and not analyzer.warnings:
        print("\n✅ No semantic errors or warnings!")

    print("\n📋 SYMBOL TABLE:")
    print(f"   {'Name':<15} {'Kind':<12} {'Mutable':<10} {'Scope':<8}")
    print("   " + "-" * 45)
    for sym in analyzer.all_symbols:
        print(f"   {sym.name:<15} {sym.kind:<12} {'Yes' if sym.mutable else 'No':<10} {sym.scope:<8}")


# ============================================================
# PART 6: MAIN COMPILER FUNCTION
# ============================================================

@dataclass
class CompileResult:
    tokens: List[Token] = field(default_factory=list)
    lexer_errors: List[str] = field(default_factory=list)
    ast: Optional[Program] = None
    parser_errors: List[str] = field(default_factory=list)
    semantic_errors: List[str] = field(default_factory=list)
    semantic_warnings: List[str] = field(default_factory=list)
    symbols: List[SymbolInfo] = field(default_factory=list)
    success: bool = True


def compile_source(source: str, verbose: bool = True) -> CompileResult:
    """Run all compiler phases on the source code."""
    result = CompileResult()

    # Phase 1: Lexing
    if verbose:
        print("\n🔤 " + "=" * 57)
        print("PHASE 1: LEXICAL ANALYSIS (Tokenization)")
        print("=" * 60)

    lexer = Lexer(source)
    result.tokens, result.lexer_errors = lexer.tokenize()

    if result.lexer_errors:
        result.success = False
        if verbose:
            print("\n❌ Lexer Errors:")
            for err in result.lexer_errors:
                print(f"   {err}")

    if verbose:
        print_tokens(result.tokens)

    # Phase 2: Parsing
    if verbose:
        print("\n🌳 " + "=" * 57)
        print("PHASE 2: SYNTACTIC ANALYSIS (Parsing)")
        print("=" * 60)

    parser = Parser(result.tokens)
    result.ast = parser.parse_program()
    result.parser_errors = parser.errors

    if result.parser_errors:
        result.success = False
        if verbose:
            print("\n❌ Parser Errors:")
            for err in result.parser_errors:
                print(f"   {err}")

    if verbose:
        print("\nAbstract Syntax Tree:")
        print("-" * 60)
        ASTPrinter().print(result.ast)

    # Phase 3: Semantic Analysis
    if verbose:
        print("\n🔍 " + "=" * 57)
        print("PHASE 3: SEMANTIC ANALYSIS")
        print("=" * 60)

    analyzer = SemanticAnalyzer()
    analyzer.analyze(result.ast)
    result.semantic_errors = analyzer.errors
    result.semantic_warnings = analyzer.warnings
    result.symbols = analyzer.all_symbols

    if analyzer.errors:
        result.success = False

    if verbose:
        print_semantic_results(analyzer)

    # Summary
    if verbose:
        print("\n" + "=" * 60)
        print("COMPILATION SUMMARY")
        print("=" * 60)
        total_errors = len(result.lexer_errors) + len(result.parser_errors) + len(result.semantic_errors)
        if result.success:
            print("✅ Compilation successful!")
        else:
            print(f"❌ Compilation failed with {total_errors} error(s)")
        print(f"   Tokens:   {len(result.tokens) - 1}")  # -1 for EOF
        print(f"   Errors:   {total_errors}")
        print(f"   Warnings: {len(result.semantic_warnings)}")

    return result


# ============================================================
# PART 7: COMMAND-LINE INTERFACE
# ============================================================

def interactive_mode() -> None:
    """Run the compiler in interactive REPL mode."""
    print("=" * 60)
    print("  COMPILER FRONTEND - Interactive Mode")
    print("  Type your code and press Enter twice to compile.")
    print("  Type 'exit' or 'quit' to exit.")
    print("=" * 60)

    while True:
        print("\n>>> ", end="")
        lines = []
        while True:
            try:
                line = input()
                if line.lower() in ('exit', 'quit'):
                    print("Goodbye!")
                    return
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            except EOFError:
                print("\nGoodbye!")
                return

        source = "\n".join(lines[:-1]) if lines else ""
        if source.strip():
            compile_source(source)


def main() -> None:
    if len(sys.argv) == 1:
        interactive_mode()
    elif len(sys.argv) == 2:
        filepath = sys.argv[1]
        try:
            with open(filepath, 'r') as f:
                source = f.read()
            compile_source(source)
        except FileNotFoundError:
            print(f"Error: File '{filepath}' not found.")
            sys.exit(1)
    elif len(sys.argv) == 3 and sys.argv[1] == '-e':
        compile_source(sys.argv[2])
    else:
        print("Usage:")
        print("  python compiler.py              # Interactive mode")
        print("  python compiler.py <file>       # Compile a file")
        print("  python compiler.py -e '<code>'  # Compile a string")
        sys.exit(1)


if __name__ == '__main__':
    main()
