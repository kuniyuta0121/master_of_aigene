"""
============================================================================
COMPILER & RUNTIME INTERNALS -- Textbook-Level Learning Program
============================================================================
From source code to machine execution: lexer, parser, type inference,
IR optimization, register allocation, garbage collection, JIT compilation,
and runtime memory management.

Run: python compiler_runtime.py
============================================================================
"""

from __future__ import annotations
import re
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import (
    Any, Optional, Union, Callable,
    Dict, List, Tuple, Set,
)
import random
import time


# ==========================================================================
# 1. LEXER -- Regex-Based Tokenizer for a Mini-Language
# ==========================================================================

class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    BOOL = auto()
    # Keywords
    LET = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    FN = auto()
    RETURN = auto()
    WHILE = auto()
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQ = auto()         # =
    EQEQ = auto()       # ==
    NEQ = auto()         # !=
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    SEMICOLON = auto()
    ARROW = auto()       # ->
    COLON = auto()
    # Special
    EOF = auto()


@dataclass
class Position:
    line: int
    column: int
    offset: int

    def __repr__(self):
        return f"({self.line}:{self.column})"


@dataclass
class Token:
    type: TokenType
    value: Any
    pos: Position

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.pos})"


# Token specification: (regex_pattern, token_type_or_handler)
TOKEN_SPEC: List[Tuple[str, Optional[TokenType]]] = [
    (r'[ \t]+',            None),                 # skip whitespace
    (r'#[^\n]*',           None),                 # comments
    (r'\n',                None),                 # newlines (tracked)
    (r'->',                TokenType.ARROW),
    (r'==',                TokenType.EQEQ),
    (r'!=',                TokenType.NEQ),
    (r'<=',                TokenType.LTE),
    (r'>=',                TokenType.GTE),
    (r'&&',                TokenType.AND),
    (r'\|\|',              TokenType.OR),
    (r'!',                 TokenType.NOT),
    (r'=',                 TokenType.EQ),
    (r'<',                 TokenType.LT),
    (r'>',                 TokenType.GT),
    (r'\+',                TokenType.PLUS),
    (r'-',                 TokenType.MINUS),
    (r'\*',                TokenType.STAR),
    (r'/',                 TokenType.SLASH),
    (r'%',                 TokenType.PERCENT),
    (r'\(',                TokenType.LPAREN),
    (r'\)',                TokenType.RPAREN),
    (r'\{',                TokenType.LBRACE),
    (r'\}',                TokenType.RBRACE),
    (r',',                 TokenType.COMMA),
    (r';',                 TokenType.SEMICOLON),
    (r':',                 TokenType.COLON),
    (r'\d+(\.\d+)?',       TokenType.NUMBER),
    (r'"([^"\\]|\\.)*"',   TokenType.STRING),
    (r'[a-zA-Z_]\w*',      TokenType.IDENTIFIER), # keywords resolved later
]

KEYWORDS = {
    'let': TokenType.LET,
    'if': TokenType.IF,
    'then': TokenType.THEN,
    'else': TokenType.ELSE,
    'fn': TokenType.FN,
    'return': TokenType.RETURN,
    'while': TokenType.WHILE,
    'true': TokenType.BOOL,
    'false': TokenType.BOOL,
}


class LexerError(Exception):
    def __init__(self, msg: str, pos: Position):
        super().__init__(f"{msg} at {pos}")
        self.pos = pos


class Lexer:
    """Regex-based tokenizer with position tracking."""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
        # Build combined regex
        parts = []
        for i, (pattern, _) in enumerate(TOKEN_SPEC):
            parts.append(f'(?P<G{i}>{pattern})')
        self.master_re = re.compile('|'.join(parts))

    def _make_pos(self) -> Position:
        return Position(self.line, self.col, self.pos)

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        for m in self.master_re.finditer(self.source):
            start = m.start()
            # Detect skipped characters (illegal chars)
            if start > self.pos:
                bad = self.source[self.pos:start]
                if bad.strip():
                    raise LexerError(f"Unexpected character '{bad.strip()[0]}'",
                                     self._make_pos())
            text = m.group()
            # Advance position tracking
            for ch in self.source[self.pos:start]:
                if ch == '\n':
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
            pos = self._make_pos()
            # Find which group matched
            group_idx = None
            for i in range(len(TOKEN_SPEC)):
                if m.group(f'G{i}') is not None:
                    group_idx = i
                    break
            _, tok_type = TOKEN_SPEC[group_idx]

            # Update position for current token text
            for ch in text:
                if ch == '\n':
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
            self.pos = m.end()

            if tok_type is None:
                continue  # skip whitespace/comments/newlines

            # Resolve keywords and convert values
            value: Any = text
            if tok_type == TokenType.IDENTIFIER and text in KEYWORDS:
                tok_type = KEYWORDS[text]
                if tok_type == TokenType.BOOL:
                    value = text == 'true'
            elif tok_type == TokenType.NUMBER:
                value = float(text) if '.' in text else int(text)
            elif tok_type == TokenType.STRING:
                value = text[1:-1]  # strip quotes

            tokens.append(Token(tok_type, value, pos))

        tokens.append(Token(TokenType.EOF, None, self._make_pos()))
        return tokens


def demo_lexer():
    print("=" * 70)
    print("1. LEXER -- Regex-Based Tokenizer")
    print("=" * 70)
    print("""
The lexer (scanner) converts raw source text into a stream of tokens.
Each token has a type, a value, and a source position for error reporting.

Key design choices:
  - Combined regex: all patterns merged into one regex with named groups
    -> Python's re engine picks the first match (longest match per group)
  - Position tracking: line/column updated as we scan
  - Keyword resolution: identifiers checked against keyword table post-match
  - Handles: integers, floats, strings (with escapes), operators, delimiters

Real compilers (GCC, Clang, V8) use hand-written lexers for speed,
but regex-based lexers (flex, Python re) are fine for learning.
""")
    source = 'let x = 42 + y * (3 - 1); # compute\nif x > 10 then "big" else "small"'
    print(f"  Source: {source!r}\n")
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    for tok in tokens:
        print(f"    {tok}")
    print()


# ==========================================================================
# 2. PARSER -- Pratt Parser (Operator Precedence)
# ==========================================================================

# --- AST Node Definitions ---

@dataclass
class ASTNumber:
    value: Union[int, float]

@dataclass
class ASTString:
    value: str

@dataclass
class ASTBool:
    value: bool

@dataclass
class ASTIdentifier:
    name: str

@dataclass
class ASTBinaryOp:
    op: str
    left: Any
    right: Any

@dataclass
class ASTUnaryOp:
    op: str
    operand: Any

@dataclass
class ASTFunctionCall:
    callee: Any
    args: List[Any]

@dataclass
class ASTIfExpr:
    condition: Any
    then_branch: Any
    else_branch: Any

@dataclass
class ASTLetBinding:
    name: str
    value: Any

@dataclass
class ASTBlock:
    stmts: List[Any]

ASTNode = Union[ASTNumber, ASTString, ASTBool, ASTIdentifier,
                ASTBinaryOp, ASTUnaryOp, ASTFunctionCall,
                ASTIfExpr, ASTLetBinding, ASTBlock]


class ParseError(Exception):
    pass


# Precedence levels for Pratt parser
PREC_NONE = 0
PREC_OR = 1
PREC_AND = 2
PREC_EQUALITY = 3    # == !=
PREC_COMPARISON = 4  # < > <= >=
PREC_SUM = 5         # + -
PREC_PRODUCT = 6     # * / %
PREC_UNARY = 7       # - !
PREC_CALL = 8        # ()

BINARY_PREC = {
    TokenType.OR: PREC_OR,
    TokenType.AND: PREC_AND,
    TokenType.EQEQ: PREC_EQUALITY, TokenType.NEQ: PREC_EQUALITY,
    TokenType.LT: PREC_COMPARISON, TokenType.GT: PREC_COMPARISON,
    TokenType.LTE: PREC_COMPARISON, TokenType.GTE: PREC_COMPARISON,
    TokenType.PLUS: PREC_SUM, TokenType.MINUS: PREC_SUM,
    TokenType.STAR: PREC_PRODUCT, TokenType.SLASH: PREC_PRODUCT,
    TokenType.PERCENT: PREC_PRODUCT,
}

OP_SYMBOL = {
    TokenType.PLUS: '+', TokenType.MINUS: '-', TokenType.STAR: '*',
    TokenType.SLASH: '/', TokenType.PERCENT: '%', TokenType.EQEQ: '==',
    TokenType.NEQ: '!=', TokenType.LT: '<', TokenType.GT: '>',
    TokenType.LTE: '<=', TokenType.GTE: '>=', TokenType.AND: '&&',
    TokenType.OR: '||', TokenType.NOT: '!',
}


class PrattParser:
    """
    Pratt parser (top-down operator precedence).
    Each token type has a 'nud' (null denotation, prefix) and
    'led' (left denotation, infix) handler.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, tt: TokenType) -> Token:
        tok = self.advance()
        if tok.type != tt:
            raise ParseError(f"Expected {tt.name}, got {tok.type.name} at {tok.pos}")
        return tok

    def match(self, tt: TokenType) -> Optional[Token]:
        if self.peek().type == tt:
            return self.advance()
        return None

    # --- Pratt core ---

    def parse_expr(self, min_prec: int = 0) -> ASTNode:
        """Parse expression with given minimum precedence."""
        left = self.nud()
        while True:
            tok = self.peek()
            prec = BINARY_PREC.get(tok.type, -1)
            if prec <= min_prec:
                # Also handle call expressions
                if tok.type == TokenType.LPAREN and PREC_CALL > min_prec:
                    left = self.parse_call(left)
                    continue
                break
            op_tok = self.advance()
            # Right-associative would use prec instead of prec
            right = self.parse_expr(prec)
            left = ASTBinaryOp(OP_SYMBOL[op_tok.type], left, right)
        return left

    def nud(self) -> ASTNode:
        """Null denotation: prefix / atom."""
        tok = self.peek()
        if tok.type == TokenType.NUMBER:
            self.advance()
            return ASTNumber(tok.value)
        if tok.type == TokenType.STRING:
            self.advance()
            return ASTString(tok.value)
        if tok.type == TokenType.BOOL:
            self.advance()
            return ASTBool(tok.value)
        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            return ASTIdentifier(tok.name if hasattr(tok, 'name') else tok.value)
        if tok.type == TokenType.MINUS:
            self.advance()
            operand = self.parse_expr(PREC_UNARY)
            return ASTUnaryOp('-', operand)
        if tok.type == TokenType.NOT:
            self.advance()
            operand = self.parse_expr(PREC_UNARY)
            return ASTUnaryOp('!', operand)
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr
        if tok.type == TokenType.IF:
            return self.parse_if()
        if tok.type == TokenType.LET:
            return self.parse_let()
        raise ParseError(f"Unexpected token {tok.type.name} at {tok.pos}")

    def parse_call(self, callee: ASTNode) -> ASTFunctionCall:
        self.expect(TokenType.LPAREN)
        args = []
        if self.peek().type != TokenType.RPAREN:
            args.append(self.parse_expr())
            while self.match(TokenType.COMMA):
                args.append(self.parse_expr())
        self.expect(TokenType.RPAREN)
        return ASTFunctionCall(callee, args)

    def parse_if(self) -> ASTIfExpr:
        self.expect(TokenType.IF)
        cond = self.parse_expr()
        self.expect(TokenType.THEN)
        then_b = self.parse_expr()
        self.expect(TokenType.ELSE)
        else_b = self.parse_expr()
        return ASTIfExpr(cond, then_b, else_b)

    def parse_let(self) -> ASTLetBinding:
        self.expect(TokenType.LET)
        name_tok = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.EQ)
        value = self.parse_expr()
        return ASTLetBinding(name_tok.value, value)

    def parse_program(self) -> List[ASTNode]:
        stmts = []
        while self.peek().type != TokenType.EOF:
            stmts.append(self.parse_expr())
            self.match(TokenType.SEMICOLON)  # optional semicolons
        return stmts


def pretty_print_ast(node: ASTNode, indent: str = "", last: bool = True) -> str:
    """Print AST as a tree with branch lines."""
    connector = "+-" if last else "|-"
    lines = []

    def fmt(n, ind, lst):
        conn = "+-" if lst else "|-"
        prefix = ind + conn + " "
        child_ind = ind + ("   " if lst else "|  ")

        if isinstance(n, ASTNumber):
            lines.append(f"{prefix}Number({n.value})")
        elif isinstance(n, ASTString):
            lines.append(f"{prefix}String({n.value!r})")
        elif isinstance(n, ASTBool):
            lines.append(f"{prefix}Bool({n.value})")
        elif isinstance(n, ASTIdentifier):
            lines.append(f"{prefix}Ident({n.name})")
        elif isinstance(n, ASTBinaryOp):
            lines.append(f"{prefix}BinOp({n.op})")
            fmt(n.left, child_ind, False)
            fmt(n.right, child_ind, True)
        elif isinstance(n, ASTUnaryOp):
            lines.append(f"{prefix}UnaryOp({n.op})")
            fmt(n.operand, child_ind, True)
        elif isinstance(n, ASTFunctionCall):
            lines.append(f"{prefix}Call")
            fmt(n.callee, child_ind, False)
            for i, a in enumerate(n.args):
                fmt(a, child_ind, i == len(n.args) - 1)
        elif isinstance(n, ASTIfExpr):
            lines.append(f"{prefix}If")
            fmt(n.condition, child_ind, False)
            fmt(n.then_branch, child_ind, False)
            fmt(n.else_branch, child_ind, True)
        elif isinstance(n, ASTLetBinding):
            lines.append(f"{prefix}Let({n.name})")
            fmt(n.value, child_ind, True)
        else:
            lines.append(f"{prefix}{n}")

    fmt(node, "", True)
    return "\n".join(lines)


def demo_parser():
    print("=" * 70)
    print("2. PARSER -- Pratt Parser (Operator Precedence)")
    print("=" * 70)
    print("""
Pratt parsing (TDOP) elegantly handles operator precedence without
separate grammar rules per precedence level.

Core idea:
  - Each token has a binding power (precedence number)
  - nud (null denotation): how token acts as prefix/atom (e.g. -x, literal)
  - led (left denotation): how token acts as infix (e.g. x + y)
  - parse_expr(min_prec) keeps consuming tokens while their prec > min_prec

Advantages over recursive descent:
  - Adding operators = adding one entry, not new grammar rule
  - Precedence is just a number comparison
  - Used in real compilers: V8 (JavaScript), rustc (partially), Lua
""")
    source = "let result = if x > 0 then x * 2 + f(y, 3) else -x"
    print(f"  Source: {source}\n")
    tokens = Lexer(source).tokenize()
    parser = PrattParser(tokens)
    stmts = parser.parse_program()
    for stmt in stmts:
        print(pretty_print_ast(stmt))
    print()


# ==========================================================================
# 3. TYPE INFERENCE -- Simplified Hindley-Milner
# ==========================================================================

class TypeVar:
    _counter = 0

    def __init__(self, name: Optional[str] = None):
        if name is None:
            TypeVar._counter += 1
            name = f"t{TypeVar._counter}"
        self.name = name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, TypeVar) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


@dataclass(frozen=True)
class TypeCon:
    """Concrete type: Int, Bool, String, etc."""
    name: str

    def __repr__(self):
        return self.name


@dataclass(frozen=True)
class TypeFun:
    """Function type: arg_types -> return_type."""
    args: tuple
    ret: Any

    def __repr__(self):
        if len(self.args) == 1:
            return f"{self.args[0]} -> {self.ret}"
        args_str = ", ".join(str(a) for a in self.args)
        return f"({args_str}) -> {self.ret}"


MonoType = Union[TypeVar, TypeCon, TypeFun]

T_INT = TypeCon("Int")
T_FLOAT = TypeCon("Float")
T_BOOL = TypeCon("Bool")
T_STRING = TypeCon("String")


class TypeInferenceError(Exception):
    pass


class Substitution:
    """Maps type variables to types. Immutable-style with compose."""

    def __init__(self, mapping: Optional[Dict[str, MonoType]] = None):
        self.mapping: Dict[str, MonoType] = mapping or {}

    def apply(self, t: MonoType) -> MonoType:
        if isinstance(t, TypeVar):
            if t.name in self.mapping:
                return self.apply(self.mapping[t.name])
            return t
        if isinstance(t, TypeCon):
            return t
        if isinstance(t, TypeFun):
            return TypeFun(
                tuple(self.apply(a) for a in t.args),
                self.apply(t.ret)
            )
        return t

    def compose(self, other: 'Substitution') -> 'Substitution':
        """self after other: apply self to all of other's mappings, then merge."""
        merged = {k: self.apply(v) for k, v in other.mapping.items()}
        merged.update(self.mapping)
        return Substitution(merged)

    def __repr__(self):
        items = ", ".join(f"{k} := {v}" for k, v in self.mapping.items())
        return f"{{{items}}}"


def occurs_in(var: TypeVar, t: MonoType) -> bool:
    """Occurs check: prevent infinite types like t1 = List[t1]."""
    if isinstance(t, TypeVar):
        return var == t
    if isinstance(t, TypeCon):
        return False
    if isinstance(t, TypeFun):
        return any(occurs_in(var, a) for a in t.args) or occurs_in(var, t.ret)
    return False


def unify(t1: MonoType, t2: MonoType) -> Substitution:
    """Robinson's unification algorithm."""
    if isinstance(t1, TypeVar):
        if t1 == t2:
            return Substitution()
        if occurs_in(t1, t2):
            raise TypeInferenceError(f"Infinite type: {t1} ~ {t2}")
        return Substitution({t1.name: t2})
    if isinstance(t2, TypeVar):
        return unify(t2, t1)
    if isinstance(t1, TypeCon) and isinstance(t2, TypeCon):
        if t1.name == t2.name:
            return Substitution()
        raise TypeInferenceError(f"Type mismatch: {t1} vs {t2}")
    if isinstance(t1, TypeFun) and isinstance(t2, TypeFun):
        if len(t1.args) != len(t2.args):
            raise TypeInferenceError(
                f"Arity mismatch: {len(t1.args)} vs {len(t2.args)}")
        sub = Substitution()
        for a1, a2 in zip(t1.args, t2.args):
            s = unify(sub.apply(a1), sub.apply(a2))
            sub = s.compose(sub)
        s = unify(sub.apply(t1.ret), sub.apply(t2.ret))
        return s.compose(sub)
    raise TypeInferenceError(f"Cannot unify {t1} with {t2}")


class TypeEnv:
    """Type environment: maps variable names to types."""

    def __init__(self, parent: Optional['TypeEnv'] = None):
        self.bindings: Dict[str, MonoType] = {}
        self.parent = parent

    def lookup(self, name: str) -> MonoType:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.lookup(name)
        raise TypeInferenceError(f"Unbound variable: {name}")

    def bind(self, name: str, t: MonoType):
        self.bindings[name] = t


def infer(node: ASTNode, env: TypeEnv) -> Tuple[MonoType, Substitution]:
    """Infer the type of an AST node, returning (type, substitution)."""
    if isinstance(node, ASTNumber):
        if isinstance(node.value, float):
            return T_FLOAT, Substitution()
        return T_INT, Substitution()
    if isinstance(node, ASTString):
        return T_STRING, Substitution()
    if isinstance(node, ASTBool):
        return T_BOOL, Substitution()
    if isinstance(node, ASTIdentifier):
        return env.lookup(node.name), Substitution()

    if isinstance(node, ASTBinaryOp):
        lt, s1 = infer(node.left, env)
        rt, s2 = infer(node.right, env)
        sub = s2.compose(s1)
        lt = sub.apply(lt)
        rt = sub.apply(rt)
        if node.op in ('+', '-', '*', '/', '%'):
            s3 = unify(lt, rt)
            sub = s3.compose(sub)
            result_t = sub.apply(lt)
            # Ensure numeric
            s4 = unify(result_t, T_INT)  # try int first
            return sub.apply(result_t), s4.compose(sub)
        if node.op in ('==', '!=', '<', '>', '<=', '>='):
            s3 = unify(lt, rt)
            return T_BOOL, s3.compose(sub)
        if node.op in ('&&', '||'):
            s3 = unify(lt, T_BOOL)
            s4 = unify(s3.apply(rt), T_BOOL)
            return T_BOOL, s4.compose(s3.compose(sub))
        return TypeVar(), sub

    if isinstance(node, ASTUnaryOp):
        ot, sub = infer(node.operand, env)
        if node.op == '-':
            return ot, sub
        if node.op == '!':
            s = unify(ot, T_BOOL)
            return T_BOOL, s.compose(sub)
        return ot, sub

    if isinstance(node, ASTIfExpr):
        ct, s1 = infer(node.condition, env)
        s2 = unify(s1.apply(ct), T_BOOL)
        sub = s2.compose(s1)
        tt, s3 = infer(node.then_branch, env)
        sub = s3.compose(sub)
        et, s4 = infer(node.else_branch, env)
        sub = s4.compose(sub)
        s5 = unify(sub.apply(tt), sub.apply(et))
        sub = s5.compose(sub)
        return sub.apply(tt), sub

    if isinstance(node, ASTLetBinding):
        vt, sub = infer(node.value, env)
        env.bind(node.name, sub.apply(vt))
        return sub.apply(vt), sub

    if isinstance(node, ASTFunctionCall):
        ret_var = TypeVar()
        ft, sub = infer(node.callee, env)
        arg_types = []
        for arg in node.args:
            at, s = infer(arg, env)
            sub = s.compose(sub)
            arg_types.append(sub.apply(at))
        expected_fun = TypeFun(tuple(arg_types), ret_var)
        s = unify(sub.apply(ft), expected_fun)
        sub = s.compose(sub)
        return sub.apply(ret_var), sub

    return TypeVar(), Substitution()


def demo_type_inference():
    print("=" * 70)
    print("3. TYPE INFERENCE -- Simplified Hindley-Milner")
    print("=" * 70)
    print("""
Hindley-Milner (HM) type inference can determine types WITHOUT annotations.
Used in: ML, Haskell, Rust (partially), TypeScript (partially).

Algorithm W steps:
  1. Assign fresh type variables to unknowns
  2. Generate constraints from AST structure
  3. Solve constraints via unification (Robinson's algorithm)
  4. Apply resulting substitution to get concrete types

Key concepts:
  - Substitution: maps type variables to types {t1 := Int, t2 := Bool}
  - Unification: given t1 and t2, find substitution making them equal
  - Occurs check: prevents infinite types (t1 = List[t1])

Comparison across languages:
  Language     | Type System       | Inference Level
  -------------|-------------------|------------------
  Python       | Dynamic (gradual) | None (runtime)
  TypeScript   | Structural        | Local + contextual
  Rust         | Nominal + traits  | Local (within fn body)
  Haskell/ML   | HM + extensions   | Global (full program)
  Java/C#      | Nominal           | Limited (var, diamond)
""")
    examples = [
        ("let x = 42", "Int from literal"),
        ("let y = if true then 1 else 2", "Int from if-branches"),
        ("let a = 3 + 4", "Int from arithmetic"),
        ("let b = 10 > 5", "Bool from comparison"),
    ]
    for src, desc in examples:
        tokens = Lexer(src).tokenize()
        parser = PrattParser(tokens)
        stmts = parser.parse_program()
        env = TypeEnv()
        for stmt in stmts:
            t, sub = infer(stmt, env)
            final_t = sub.apply(t)
            print(f"  {src:35s}  =>  {final_t}   ({desc})")

    # Type error demo
    print("\n  Type error detection:")
    try:
        src = "let bad = 1 + true"
        tokens = Lexer(src).tokenize()
        stmts = PrattParser(tokens).parse_program()
        env = TypeEnv()
        for s in stmts:
            infer(s, env)
    except TypeInferenceError as e:
        print(f"    '{src}' => ERROR: {e}")
    print()


# ==========================================================================
# 4. IR & OPTIMIZATION -- Three-Address Code
# ==========================================================================

@dataclass
class IRInstr:
    """Three-address code instruction."""
    op: str          # 'add', 'sub', 'mul', 'div', 'assign', 'label', 'goto',
                     # 'if_goto', 'call', 'return', 'param', 'nop'
    dest: Optional[str] = None
    arg1: Optional[Any] = None
    arg2: Optional[Any] = None

    def __repr__(self):
        if self.op == 'assign':
            return f"  {self.dest} = {self.arg1}"
        if self.op in ('add', 'sub', 'mul', 'div', 'mod'):
            sym = {
                'add': '+', 'sub': '-', 'mul': '*', 'div': '/', 'mod': '%'
            }[self.op]
            return f"  {self.dest} = {self.arg1} {sym} {self.arg2}"
        if self.op == 'label':
            return f"{self.dest}:"
        if self.op == 'goto':
            return f"  goto {self.dest}"
        if self.op == 'if_goto':
            return f"  if {self.arg1} goto {self.dest}"
        if self.op == 'call':
            return f"  {self.dest} = call {self.arg1}({self.arg2})"
        if self.op == 'return':
            return f"  return {self.arg1}"
        if self.op == 'param':
            return f"  param {self.arg1}"
        if self.op == 'nop':
            return f"  nop"
        if self.op == 'neg':
            return f"  {self.dest} = -{self.arg1}"
        return f"  {self.op} {self.dest} {self.arg1} {self.arg2}"


class IRGenerator:
    """Generate three-address code from AST."""

    def __init__(self):
        self.instructions: List[IRInstr] = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self) -> str:
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, instr: IRInstr):
        self.instructions.append(instr)

    def gen(self, node: ASTNode) -> str:
        """Generate IR, return name of result temporary."""
        if isinstance(node, ASTNumber):
            t = self.new_temp()
            self.emit(IRInstr('assign', t, node.value))
            return t
        if isinstance(node, ASTIdentifier):
            return node.name
        if isinstance(node, ASTBinaryOp):
            l = self.gen(node.left)
            r = self.gen(node.right)
            t = self.new_temp()
            op_map = {
                '+': 'add', '-': 'sub', '*': 'mul', '/': 'div', '%': 'mod'
            }
            ir_op = op_map.get(node.op, node.op)
            self.emit(IRInstr(ir_op, t, l, r))
            return t
        if isinstance(node, ASTUnaryOp):
            o = self.gen(node.operand)
            t = self.new_temp()
            self.emit(IRInstr('neg', t, o))
            return t
        if isinstance(node, ASTLetBinding):
            v = self.gen(node.value)
            self.emit(IRInstr('assign', node.name, v))
            return node.name
        if isinstance(node, ASTIfExpr):
            cond = self.gen(node.condition)
            l_then = self.new_label()
            l_else = self.new_label()
            l_end = self.new_label()
            result = self.new_temp()
            self.emit(IRInstr('if_goto', l_then, cond))
            self.emit(IRInstr('goto', l_else))
            self.emit(IRInstr('label', l_then))
            then_val = self.gen(node.then_branch)
            self.emit(IRInstr('assign', result, then_val))
            self.emit(IRInstr('goto', l_end))
            self.emit(IRInstr('label', l_else))
            else_val = self.gen(node.else_branch)
            self.emit(IRInstr('assign', result, else_val))
            self.emit(IRInstr('label', l_end))
            return result
        if isinstance(node, ASTFunctionCall):
            arg_temps = []
            for arg in node.args:
                arg_temps.append(self.gen(arg))
            for at in arg_temps:
                self.emit(IRInstr('param', None, at))
            t = self.new_temp()
            callee_name = node.callee.name if isinstance(node.callee, ASTIdentifier) else '?'
            self.emit(IRInstr('call', t, callee_name, len(node.args)))
            return t
        return "?"


# --- Optimization Passes ---

def constant_fold(instrs: List[IRInstr]) -> List[IRInstr]:
    """Evaluate operations on constants at compile time."""
    result = []
    for i in instrs:
        if i.op in ('add', 'sub', 'mul', 'div') and \
           isinstance(i.arg1, (int, float)) and isinstance(i.arg2, (int, float)):
            ops = {'add': lambda a, b: a+b, 'sub': lambda a, b: a-b,
                   'mul': lambda a, b: a*b, 'div': lambda a, b: a/b if b else 0}
            val = ops[i.op](i.arg1, i.arg2)
            if isinstance(val, float) and val == int(val):
                val = int(val)
            result.append(IRInstr('assign', i.dest, val))
        else:
            result.append(i)
    return result


def copy_propagation(instrs: List[IRInstr]) -> List[IRInstr]:
    """Replace uses of x where x = y with y directly."""
    copies: Dict[str, Any] = {}  # dest -> source
    result = []
    for i in instrs:
        # Apply existing copies
        a1 = copies.get(i.arg1, i.arg1) if isinstance(i.arg1, str) else i.arg1
        a2 = copies.get(i.arg2, i.arg2) if isinstance(i.arg2, str) else i.arg2
        new_i = IRInstr(i.op, i.dest, a1, a2)
        # Track new copies
        if i.op == 'assign' and isinstance(a1, str):
            copies[i.dest] = a1
        result.append(new_i)
    return result


def dead_code_elimination(instrs: List[IRInstr]) -> List[IRInstr]:
    """Remove assignments to temporaries that are never read."""
    # Collect all used variables (as arg1 or arg2)
    used: Set[str] = set()
    for i in instrs:
        if isinstance(i.arg1, str):
            used.add(i.arg1)
        if isinstance(i.arg2, str):
            used.add(i.arg2)
    # Remove assignments to unused temporaries (only temps starting with 't')
    result = []
    for i in instrs:
        if i.op == 'assign' and i.dest and i.dest.startswith('t') \
           and i.dest not in used:
            result.append(IRInstr('nop'))
            continue
        result.append(i)
    return result


def common_subexpr_elim(instrs: List[IRInstr]) -> List[IRInstr]:
    """If a op b was already computed, reuse the result."""
    seen: Dict[Tuple, str] = {}  # (op, arg1, arg2) -> dest
    result = []
    for i in instrs:
        if i.op in ('add', 'sub', 'mul', 'div', 'mod'):
            key = (i.op, i.arg1, i.arg2)
            if key in seen:
                result.append(IRInstr('assign', i.dest, seen[key]))
            else:
                seen[key] = i.dest
                result.append(i)
        else:
            result.append(i)
    return result


def demo_ir_optimization():
    print("=" * 70)
    print("4. IR & OPTIMIZATION -- Three-Address Code")
    print("=" * 70)
    print("""
Intermediate Representation (IR) bridges the gap between AST and machine code.
Three-address code: at most one operator per instruction, explicit temporaries.

  Source:  x = (a + b) * (a + b) - 2 * 3
  IR:     t1 = a + b
          t2 = a + b      <- common subexpression
          t3 = t1 * t2
          t4 = 2 * 3      <- constant foldable
          t5 = t3 - t4

Optimization passes (applied in order):
  1. Constant folding: evaluate 2*3 -> 6 at compile time
  2. Common subexpression elimination: t2 = t1 (reuse a+b)
  3. Copy propagation: replace t2 with t1 in later uses
  4. Dead code elimination: remove unused assignments

Real compilers (LLVM, GCC) apply 50+ optimization passes iteratively.
""")
    # Build IR for: let x = (a + b) * (a + b) - 2 * 3
    src = "let x = (a + b) * (a + b) - 2 * 3"
    tokens = Lexer(src).tokenize()
    ast = PrattParser(tokens).parse_program()
    gen = IRGenerator()
    for node in ast:
        gen.gen(node)

    print(f"  Source: {src}\n")
    print("  --- Unoptimized IR ---")
    for i in gen.instructions:
        print(f"    {i}")

    optimized = gen.instructions[:]
    optimized = constant_fold(optimized)
    print("\n  --- After constant folding ---")
    for i in optimized:
        print(f"    {i}")

    optimized = common_subexpr_elim(optimized)
    print("\n  --- After CSE ---")
    for i in optimized:
        print(f"    {i}")

    optimized = copy_propagation(optimized)
    print("\n  --- After copy propagation ---")
    for i in optimized:
        print(f"    {i}")

    optimized = dead_code_elimination(optimized)
    print("\n  --- After dead code elimination ---")
    for i in optimized:
        print(f"    {i}")
    print()


# ==========================================================================
# 5. REGISTER ALLOCATION -- Graph Coloring & Linear Scan
# ==========================================================================

def compute_liveness(instrs: List[IRInstr]) -> List[Tuple[Set[str], Set[str]]]:
    """
    Compute live-in and live-out sets for each instruction.
    Backward dataflow analysis.
    """
    n = len(instrs)
    live_in: List[Set[str]] = [set() for _ in range(n)]
    live_out: List[Set[str]] = [set() for _ in range(n)]

    def defs_of(i: IRInstr) -> Set[str]:
        if i.dest and i.op not in ('label', 'goto', 'if_goto', 'param', 'nop'):
            return {i.dest}
        return set()

    def uses_of(i: IRInstr) -> Set[str]:
        u = set()
        if isinstance(i.arg1, str) and not i.arg1.startswith('L'):
            u.add(i.arg1)
        if isinstance(i.arg2, str) and not i.arg2.startswith('L'):
            u.add(i.arg2)
        return u

    # Iterate until fixed point
    changed = True
    while changed:
        changed = False
        for idx in range(n - 1, -1, -1):
            instr = instrs[idx]
            old_in = live_in[idx].copy()
            old_out = live_out[idx].copy()

            # live_out = union of live_in of successors
            if idx + 1 < n:
                live_out[idx] = live_in[idx + 1].copy()
            else:
                live_out[idx] = set()

            # live_in = uses U (live_out - defs)
            live_in[idx] = uses_of(instr) | (live_out[idx] - defs_of(instr))

            if live_in[idx] != old_in or live_out[idx] != old_out:
                changed = True

    return list(zip(live_in, live_out))


def build_interference_graph(
    instrs: List[IRInstr],
    liveness: List[Tuple[Set[str], Set[str]]]
) -> Dict[str, Set[str]]:
    """Two variables interfere if one is live when the other is defined."""
    graph: Dict[str, Set[str]] = {}

    def ensure(v: str):
        if v not in graph:
            graph[v] = set()

    for idx, instr in enumerate(instrs):
        _, live_out = liveness[idx]
        if instr.dest and instr.op not in ('label', 'goto', 'if_goto', 'param', 'nop'):
            ensure(instr.dest)
            for v in live_out:
                if v != instr.dest:
                    ensure(v)
                    ensure(instr.dest)
                    graph[instr.dest].add(v)
                    graph[v].add(instr.dest)
    return graph


def graph_coloring(graph: Dict[str, Set[str]], num_regs: int) -> Dict[str, str]:
    """
    Chaitin's algorithm: simplify-select with spilling.
    Returns mapping: variable -> register name or 'SPILL'.
    """
    REG_NAMES = [f"R{i}" for i in range(num_regs)]
    stack: List[Tuple[str, Set[str]]] = []
    remaining = {v: neighbors.copy() for v, neighbors in graph.items()}

    # Simplify: remove nodes with degree < num_regs
    while remaining:
        # Find a node with degree < num_regs
        found = None
        for v, neighbors in remaining.items():
            active_neighbors = neighbors & remaining.keys()
            if len(active_neighbors) < num_regs:
                found = v
                break
        if found is None:
            # Must spill: pick node with highest degree
            found = max(remaining, key=lambda v: len(remaining[v] & remaining.keys()))
        stack.append((found, remaining[found] & remaining.keys()))
        del remaining[found]

    # Select: assign colors (registers) in reverse order
    coloring: Dict[str, str] = {}
    for var, neighbors in reversed(stack):
        used_colors = {coloring[n] for n in neighbors if n in coloring}
        available = [r for r in REG_NAMES if r not in used_colors]
        if available:
            coloring[var] = available[0]
        else:
            coloring[var] = "SPILL"  # needs memory

    return coloring


def linear_scan_alloc(
    intervals: List[Tuple[str, int, int]],
    num_regs: int
) -> Dict[str, str]:
    """
    Linear scan register allocation (used in JIT compilers for speed).
    intervals: [(var_name, start, end), ...]
    """
    REG_NAMES = [f"R{i}" for i in range(num_regs)]
    intervals = sorted(intervals, key=lambda x: x[1])
    active: List[Tuple[str, int, int, str]] = []  # (var, start, end, reg)
    free_regs = list(reversed(REG_NAMES))
    allocation: Dict[str, str] = {}

    for var, start, end in intervals:
        # Expire old intervals
        active = [(v, s, e, r) for v, s, e, r in active if e > start]
        freed = set(REG_NAMES) - {r for _, _, _, r in active}
        free_regs = [r for r in REG_NAMES if r in freed]

        if free_regs:
            reg = free_regs.pop()
            allocation[var] = reg
            active.append((var, start, end, reg))
        else:
            # Spill the one with latest end point
            if active and active[-1][2] > end:
                spill_var, _, _, spill_reg = max(active, key=lambda x: x[2])
                allocation[var] = spill_reg
                allocation[spill_var] = "SPILL"
                active = [(v, s, e, r) for v, s, e, r in active if v != spill_var]
                active.append((var, start, end, spill_reg))
            else:
                allocation[var] = "SPILL"

    return allocation


def demo_register_allocation():
    print("=" * 70)
    print("5. REGISTER ALLOCATION -- Graph Coloring & Linear Scan")
    print("=" * 70)
    print("""
Register allocation maps unlimited virtual registers (temporaries) to
a fixed number of physical CPU registers. This is an NP-hard problem
(equivalent to graph coloring), so compilers use heuristics.

Two main approaches:

  Graph Coloring (Chaitin, 1981):
    1. Build interference graph: edge between vars alive at same time
    2. Simplify: remove nodes with degree < K (K = num registers)
    3. Select: assign colors in reverse removal order
    4. Spill: if stuck, move a variable to memory (stack)
    Used in: GCC, LLVM (with enhancements)

  Linear Scan (Poletto, 1999):
    1. Compute live intervals (start/end for each variable)
    2. Walk intervals left-to-right, greedily assign registers
    3. Spill the longest-lived variable when registers exhausted
    Used in: JIT compilers (V8, HotSpot C1) for fast compilation
""")
    # Example IR for register allocation
    instrs = [
        IRInstr('assign', 'a', 1),
        IRInstr('assign', 'b', 2),
        IRInstr('add', 'c', 'a', 'b'),
        IRInstr('assign', 'd', 3),
        IRInstr('mul', 'e', 'c', 'd'),
        IRInstr('sub', 'f', 'e', 'a'),
        IRInstr('add', 'g', 'f', 'b'),
    ]

    print("  IR instructions:")
    for i in instrs:
        print(f"    {i}")

    liveness = compute_liveness(instrs)
    print("\n  Liveness (live-in, live-out):")
    for idx, (li, lo) in enumerate(liveness):
        print(f"    [{idx}] in={str(li or '{}'):<20s} out={str(lo or '{}')}")

    graph = build_interference_graph(instrs, liveness)
    print("\n  Interference graph:")
    for v in sorted(graph):
        print(f"    {v} -- {sorted(graph[v])}")

    coloring = graph_coloring(graph, num_regs=3)
    print(f"\n  Graph coloring (3 registers):")
    for v in sorted(coloring):
        print(f"    {v} -> {coloring[v]}")

    # Linear scan
    intervals = [
        ('a', 0, 5), ('b', 1, 6), ('c', 2, 4),
        ('d', 3, 4), ('e', 4, 5), ('f', 5, 6), ('g', 6, 7),
    ]
    ls_alloc = linear_scan_alloc(intervals, num_regs=3)
    print(f"\n  Linear scan (3 registers):")
    for v in sorted(ls_alloc):
        print(f"    {v} -> {ls_alloc[v]}")
    print()


# ==========================================================================
# 6. GARBAGE COLLECTION
# ==========================================================================

# --- 6a. Mark-Sweep ---

class HeapObject:
    _id_counter = 0

    def __init__(self, name: str, size: int = 1):
        HeapObject._id_counter += 1
        self.id = HeapObject._id_counter
        self.name = name
        self.size = size
        self.marked = False
        self.refs: List['HeapObject'] = []

    def add_ref(self, other: 'HeapObject'):
        self.refs.append(other)

    def __repr__(self):
        return f"Obj({self.name}, id={self.id})"


class MarkSweepGC:
    """Mark-Sweep garbage collector with actual heap objects."""

    def __init__(self):
        self.heap: List[HeapObject] = []
        self.roots: List[HeapObject] = []
        self.collections = 0

    def allocate(self, name: str, size: int = 1) -> HeapObject:
        obj = HeapObject(name, size)
        self.heap.append(obj)
        return obj

    def add_root(self, obj: HeapObject):
        self.roots.append(obj)

    def remove_root(self, obj: HeapObject):
        self.roots = [r for r in self.roots if r is not obj]

    def mark(self, obj: HeapObject):
        if obj.marked:
            return
        obj.marked = True
        for ref in obj.refs:
            self.mark(ref)

    def collect(self) -> int:
        """Run mark-sweep, return number of objects freed."""
        self.collections += 1
        # Mark phase
        for obj in self.heap:
            obj.marked = False
        for root in self.roots:
            self.mark(root)
        # Sweep phase
        before = len(self.heap)
        self.heap = [obj for obj in self.heap if obj.marked]
        freed = before - len(self.heap)
        return freed

    def status(self) -> str:
        alive = [o.name for o in self.heap]
        return f"Heap: {alive}, Roots: {[r.name for r in self.roots]}"


# --- 6b. Copying Collector (Cheney's Algorithm) ---

class CopyingGC:
    """Semi-space (Cheney's) copying collector."""

    def __init__(self, space_size: int = 16):
        self.space_size = space_size
        self.from_space: List[Optional[HeapObject]] = [None] * space_size
        self.to_space: List[Optional[HeapObject]] = [None] * space_size
        self.alloc_ptr = 0
        self.roots: List[int] = []  # indices into from_space
        self.forwarding: Dict[int, int] = {}  # old_idx -> new_idx

    def allocate(self, name: str) -> int:
        if self.alloc_ptr >= self.space_size:
            self.collect()
            if self.alloc_ptr >= self.space_size:
                raise MemoryError("Out of heap space")
        idx = self.alloc_ptr
        self.from_space[idx] = HeapObject(name)
        self.alloc_ptr += 1
        return idx

    def add_ref(self, from_idx: int, to_idx: int):
        obj = self.from_space[from_idx]
        target = self.from_space[to_idx]
        if obj and target:
            obj.add_ref(target)

    def collect(self) -> int:
        """Cheney's algorithm: BFS copy from from_space to to_space."""
        self.to_space = [None] * self.space_size
        self.forwarding = {}
        scan_ptr = 0
        copy_ptr = 0

        def copy_obj(old_idx: int) -> int:
            nonlocal copy_ptr
            if old_idx in self.forwarding:
                return self.forwarding[old_idx]
            obj = self.from_space[old_idx]
            if obj is None:
                return -1
            new_idx = copy_ptr
            self.to_space[new_idx] = obj
            self.forwarding[old_idx] = new_idx
            copy_ptr += 1
            return new_idx

        # Copy roots
        new_roots = []
        for root_idx in self.roots:
            new_idx = copy_obj(root_idx)
            new_roots.append(new_idx)
        self.roots = new_roots

        # Scan copied objects (BFS)
        while scan_ptr < copy_ptr:
            obj = self.to_space[scan_ptr]
            if obj:
                new_refs = []
                for ref in obj.refs:
                    # Find ref in from_space
                    for old_i, o in enumerate(self.from_space):
                        if o is ref:
                            new_i = copy_obj(old_i)
                            if new_i >= 0:
                                new_refs.append(self.to_space[new_i])
                            break
                obj.refs = new_refs
            scan_ptr += 1

        freed = self.alloc_ptr - copy_ptr
        # Swap spaces
        self.from_space = self.to_space
        self.to_space = [None] * self.space_size
        self.alloc_ptr = copy_ptr
        return freed

    def dump(self) -> str:
        objs = [o.name for o in self.from_space[:self.alloc_ptr] if o]
        return f"Space[0..{self.alloc_ptr}]: {objs}"


# --- 6c. Generational GC ---

class GenerationalGC:
    """Generational GC with nursery (young gen) and tenured (old gen)."""

    def __init__(self, nursery_size: int = 8, tenured_size: int = 32):
        self.nursery_size = nursery_size
        self.tenured_size = tenured_size
        self.nursery: List[HeapObject] = []
        self.tenured: List[HeapObject] = []
        self.roots: List[HeapObject] = []
        self.remembered_set: Set[int] = set()  # write barrier: tenured obj ids -> nursery
        self.survive_count: Dict[int, int] = {}  # obj_id -> survival count
        self.promotion_threshold = 2
        self.minor_collections = 0
        self.major_collections = 0

    def allocate(self, name: str) -> HeapObject:
        if len(self.nursery) >= self.nursery_size:
            self.minor_collect()
        obj = HeapObject(name)
        self.nursery.append(obj)
        self.survive_count[obj.id] = 0
        return obj

    def write_barrier(self, old_obj: HeapObject, new_ref: HeapObject):
        """Track old-to-young references for minor GC correctness."""
        old_obj.add_ref(new_ref)
        if old_obj in self.tenured and new_ref in self.nursery:
            self.remembered_set.add(old_obj.id)

    def _mark_reachable(self, roots: List[HeapObject],
                        target_set: List[HeapObject]) -> Set[int]:
        reachable = set()
        stack = list(roots)
        while stack:
            obj = stack.pop()
            if obj.id in reachable:
                continue
            if obj in target_set:
                reachable.add(obj.id)
            for ref in obj.refs:
                if ref.id not in reachable:
                    stack.append(ref)
        return reachable

    def minor_collect(self):
        """Collect nursery only. Promote survivors."""
        self.minor_collections += 1
        # Roots for nursery: global roots + remembered set
        extra_roots = [o for o in self.tenured if o.id in self.remembered_set]
        all_roots = self.roots + extra_roots
        reachable = self._mark_reachable(all_roots, self.nursery)

        survivors = []
        for obj in self.nursery:
            if obj.id in reachable:
                self.survive_count[obj.id] = self.survive_count.get(obj.id, 0) + 1
                if self.survive_count[obj.id] >= self.promotion_threshold:
                    self.tenured.append(obj)  # promote
                else:
                    survivors.append(obj)
        self.nursery = survivors
        self.remembered_set.clear()

    def major_collect(self):
        """Full GC: collect both nursery and tenured."""
        self.major_collections += 1
        all_objs = self.nursery + self.tenured
        reachable = self._mark_reachable(self.roots, all_objs)
        self.nursery = [o for o in self.nursery if o.id in reachable]
        self.tenured = [o for o in self.tenured if o.id in reachable]
        self.remembered_set.clear()

    def status(self) -> str:
        n = [o.name for o in self.nursery]
        t = [o.name for o in self.tenured]
        return (f"Nursery: {n}, Tenured: {t}, "
                f"Minor GCs: {self.minor_collections}, Major GCs: {self.major_collections}")


# --- 6d. Reference Counting with Cycle Detection ---

class RCObject:
    """Reference-counted object (CPython style)."""
    _counter = 0

    def __init__(self, name: str):
        RCObject._counter += 1
        self.id = RCObject._counter
        self.name = name
        self.refcount = 0
        self.refs: List['RCObject'] = []
        self.alive = True

    def __repr__(self):
        return f"RC({self.name}, rc={self.refcount})"


class RefCountGC:
    """Reference counting with cycle detection (CPython approach)."""

    def __init__(self):
        self.objects: List[RCObject] = []
        self.freed: List[str] = []

    def new_object(self, name: str) -> RCObject:
        obj = RCObject(name)
        obj.refcount = 1  # creation ref
        self.objects.append(obj)
        return obj

    def add_ref(self, holder: RCObject, target: RCObject):
        holder.refs.append(target)
        target.refcount += 1

    def del_ref(self, holder: RCObject, target: RCObject):
        if target in holder.refs:
            holder.refs.remove(target)
            target.refcount -= 1
            if target.refcount == 0:
                self._free(target)

    def decref(self, obj: RCObject):
        obj.refcount -= 1
        if obj.refcount == 0:
            self._free(obj)

    def _free(self, obj: RCObject):
        if not obj.alive:
            return
        obj.alive = False
        self.freed.append(obj.name)
        for ref in obj.refs:
            ref.refcount -= 1
            if ref.refcount == 0:
                self._free(ref)
        self.objects = [o for o in self.objects if o.alive]

    def detect_cycles(self) -> List[List[str]]:
        """
        Cycle detection (simplified CPython gc module approach):
        1. For each container object, tentatively decrement refcount of referents
        2. Objects still with refcount > 0 are roots (externally referenced)
        3. Objects reachable from roots are alive; rest are cyclic garbage
        """
        # Save original refcounts
        saved = {obj.id: obj.refcount for obj in self.objects}
        # Tentative decrements
        gc_refcount = {obj.id: obj.refcount for obj in self.objects}
        for obj in self.objects:
            for ref in obj.refs:
                if ref.alive:
                    gc_refcount[ref.id] = gc_refcount.get(ref.id, 0) - 1

        # Find roots (gc_refcount > 0)
        roots = {obj.id for obj in self.objects if gc_refcount.get(obj.id, 0) > 0}

        # BFS from roots
        reachable = set()
        stack = [obj for obj in self.objects if obj.id in roots]
        while stack:
            o = stack.pop()
            if o.id in reachable:
                continue
            reachable.add(o.id)
            for ref in o.refs:
                if ref.alive and ref.id not in reachable:
                    stack.append(ref)

        # Unreachable objects form cycles
        cycles = []
        unreachable = [o for o in self.objects if o.id not in reachable]
        if unreachable:
            cycles.append([o.name for o in unreachable])
            for o in unreachable:
                o.alive = False
                self.freed.append(o.name)
            self.objects = [o for o in self.objects if o.alive]

        return cycles


# --- 6e. Tri-Color Marking (Concurrent GC) ---

class TriColorGC:
    """Tri-color marking for concurrent/incremental GC."""

    WHITE = 0  # Not yet seen (potentially garbage)
    GRAY = 1   # Seen but refs not yet scanned
    BLACK = 2  # Fully scanned (definitely alive)

    def __init__(self):
        self.heap: List[HeapObject] = []
        self.roots: List[HeapObject] = []
        self.colors: Dict[int, int] = {}
        self.steps_log: List[str] = []

    def allocate(self, name: str) -> HeapObject:
        obj = HeapObject(name)
        self.heap.append(obj)
        self.colors[obj.id] = self.WHITE
        return obj

    def collect_incremental(self) -> int:
        """Step-by-step tri-color marking (simulates concurrent GC)."""
        color_names = {0: "WHITE", 1: "GRAY", 2: "BLACK"}
        self.steps_log = []

        # Init: all white
        for obj in self.heap:
            self.colors[obj.id] = self.WHITE

        # Step 1: Mark roots gray
        for root in self.roots:
            self.colors[root.id] = self.GRAY
        self.steps_log.append(self._snapshot("Roots marked GRAY"))

        # Step 2+: Process gray objects until none remain
        step = 2
        while True:
            gray = [o for o in self.heap if self.colors.get(o.id) == self.GRAY]
            if not gray:
                break
            obj = gray[0]
            self.colors[obj.id] = self.BLACK
            for ref in obj.refs:
                if self.colors.get(ref.id) == self.WHITE:
                    self.colors[ref.id] = self.GRAY
            self.steps_log.append(
                self._snapshot(f"Step {step}: scan {obj.name} -> BLACK")
            )
            step += 1

        # Sweep: remove white objects
        before = len(self.heap)
        self.heap = [o for o in self.heap if self.colors.get(o.id) != self.WHITE]
        freed = before - len(self.heap)
        self.steps_log.append(self._snapshot(f"Sweep: freed {freed} objects"))
        return freed

    def _snapshot(self, msg: str) -> str:
        color_names = {0: "W", 1: "G", 2: "B"}
        objs = ", ".join(
            f"{o.name}={color_names[self.colors.get(o.id, 0)]}"
            for o in self.heap
        )
        return f"{msg}: [{objs}]"


def demo_garbage_collection():
    print("=" * 70)
    print("6. GARBAGE COLLECTION")
    print("=" * 70)

    # --- Mark-Sweep ---
    print("\n  --- 6a. Mark-Sweep GC ---")
    print("""
  The simplest tracing GC. Two phases:
    Mark: traverse from roots, mark all reachable objects
    Sweep: free all unmarked objects

  Pros: handles cycles, simple implementation
  Cons: stop-the-world pauses, heap fragmentation
""")
    gc = MarkSweepGC()
    a = gc.allocate("A")
    b = gc.allocate("B")
    c = gc.allocate("C")
    d = gc.allocate("D")
    gc.add_root(a)
    a.add_ref(b)
    b.add_ref(c)
    # D is unreachable

    print(f"    Before GC: {gc.status()}")
    freed = gc.collect()
    print(f"    After GC:  {gc.status()} (freed {freed} object: D)")

    # --- Copying Collector ---
    print("\n  --- 6b. Copying Collector (Cheney's Algorithm) ---")
    print("""
  Divides heap into two semi-spaces (from/to).
    1. Allocate in from-space
    2. When full, copy live objects to to-space (BFS via scan pointer)
    3. Swap spaces; from-space is now clean

  Pros: no fragmentation (compaction built-in), allocation = pointer bump
  Cons: wastes 50% of heap, copies live objects (expensive if many alive)
  Used in: Java young generation, many Lisp/Scheme implementations
""")
    cgc = CopyingGC(space_size=8)
    i0 = cgc.allocate("X")
    i1 = cgc.allocate("Y")
    i2 = cgc.allocate("Z")
    i3 = cgc.allocate("garbage1")
    i4 = cgc.allocate("garbage2")
    cgc.roots = [i0, i1]
    cgc.add_ref(i0, i2)  # X -> Z

    print(f"    Before: {cgc.dump()}")
    freed = cgc.collect()
    print(f"    After:  {cgc.dump()} (freed {freed}: garbage1, garbage2, unreachable)")

    # --- Generational GC ---
    print("\n  --- 6c. Generational GC ---")
    print("""
  Observation: most objects die young (generational hypothesis).
  Strategy: separate heap into generations:
    - Nursery (young gen): small, collected frequently (minor GC)
    - Tenured (old gen): large, collected rarely (major GC)
    - Objects that survive N minor GCs get promoted to tenured

  Write barrier: when old object references new object, record it in
  a "remembered set" so minor GC can find cross-generation references.

  Used by: JVM (G1, ZGC, Shenandoah), .NET, V8, Python (via gc module)
""")
    ggc = GenerationalGC(nursery_size=4)
    obj_a = ggc.allocate("A")
    obj_b = ggc.allocate("B")
    obj_c = ggc.allocate("C")
    obj_d = ggc.allocate("D")
    ggc.roots = [obj_a, obj_b]
    obj_a.add_ref(obj_c)
    print(f"    Initial:     {ggc.status()}")
    # Trigger minor GC by allocating more
    obj_e = ggc.allocate("E")
    print(f"    After alloc: {ggc.status()}")
    ggc.minor_collect()
    print(f"    After minor: {ggc.status()}")
    # Another minor GC to promote survivors
    ggc.minor_collect()
    print(f"    After 2nd:   {ggc.status()}")

    # --- Reference Counting with Cycle Detection ---
    print("\n  --- 6d. Reference Counting (CPython approach) ---")
    print("""
  Each object has a reference count. When it reaches 0, object is freed.

  Pros: immediate reclamation, no pauses, simple
  Cons: overhead per assignment, cannot handle cycles alone

  CPython solution: ref counting + periodic cycle detector
  The cycle detector uses "tentative decrement":
    1. For all container objects, decrement refs' counts by internal refs
    2. Objects with count > 0 have external references (roots)
    3. Unreachable from roots = cyclic garbage
""")
    rcgc = RefCountGC()
    p = rcgc.new_object("P")
    q = rcgc.new_object("Q")
    r = rcgc.new_object("R")
    # Create cycle: P -> Q -> R -> P
    rcgc.add_ref(p, q)
    rcgc.add_ref(q, r)
    rcgc.add_ref(r, p)
    # Drop external references
    rcgc.decref(p)
    rcgc.decref(q)
    rcgc.decref(r)
    print(f"    After dropping external refs: {[o for o in rcgc.objects]}")
    print(f"    All alive (cycle keeps them)! refcounts: "
          f"P={p.refcount}, Q={q.refcount}, R={r.refcount}")
    cycles = rcgc.detect_cycles()
    print(f"    Cycle detector found: {cycles}")
    print(f"    After cycle collection: {[o.name for o in rcgc.objects if o.alive]}")

    # --- Tri-Color Marking ---
    print("\n  --- 6e. Tri-Color Marking (Concurrent GC) ---")
    print("""
  For concurrent GC, we need to allow mutator to run during collection.
  Tri-color abstraction:
    WHITE: not yet visited (garbage candidate)
    GRAY:  discovered but children not scanned yet
    BLACK: fully scanned (alive)

  Invariant: no BLACK object points directly to a WHITE object
  (maintained via write barriers: SATB or incremental update)

  Process: roots->GRAY, then repeatedly pick GRAY, scan its refs, mark BLACK
  When no GRAY left, all WHITE objects are garbage.
""")
    tcgc = TriColorGC()
    ta = tcgc.allocate("A")
    tb = tcgc.allocate("B")
    tc = tcgc.allocate("C")
    td = tcgc.allocate("D")
    te = tcgc.allocate("E")
    tcgc.roots = [ta]
    ta.add_ref(tb)
    tb.add_ref(tc)
    # D, E are unreachable
    freed = tcgc.collect_incremental()
    for log in tcgc.steps_log:
        print(f"    {log}")

    # --- G1/ZGC Concepts ---
    print("\n  --- 6f. Modern GC Concepts (G1, ZGC, Shenandoah) ---")
    print("""
  G1 (Garbage First) - JVM default since Java 9:
    - Divides heap into equal-sized regions (not contiguous generations)
    - Each region can be: Eden, Survivor, Old, Humongous
    - Collects regions with most garbage first (hence "Garbage First")
    - Mixed collections: young + some old regions
    - Target: configurable pause time goal (e.g., 200ms)

  ZGC (Z Garbage Collector) - JVM, ultra-low latency:
    - Colored pointers: metadata stored in pointer bits
      (marked0, marked1, remapped, finalizable)
    - Load barriers: when reading a reference, fix it up if needed
    - Concurrent everything: marking, relocation, reference processing
    - Pause times < 10ms regardless of heap size (tested up to 16TB)
    - Region-based: small (2MB), medium (32MB), large (N*2MB)

  Shenandoah - OpenJDK alternative to ZGC:
    - Brooks forwarding pointers: extra word per object for relocation
    - Concurrent compaction via forwarding pointer indirection
    - Similar pause characteristics to ZGC, different mechanism

  Key concepts comparison:
    Collector    | Concurrent Mark | Concurrent Compact | Barrier Type
    -------------|-----------------|--------------------|--------------
    G1           | Yes             | Partial (evac)     | Write (SATB)
    ZGC          | Yes             | Yes                | Load
    Shenandoah   | Yes             | Yes                | Load + Write
    Serial/CMS   | CMS only        | No                 | Write
""")


# ==========================================================================
# 7. JIT COMPILATION
# ==========================================================================

class MethodProfile:
    """Tracks method execution for JIT decisions."""

    def __init__(self, name: str):
        self.name = name
        self.call_count = 0
        self.compiled_tier = 0  # 0=interpreted, 1=baseline, 2=optimized
        self.type_feedback: Dict[str, List[str]] = {}  # callsite -> observed types
        self.deopt_count = 0

    def __repr__(self):
        tier_names = {0: "interp", 1: "baseline", 2: "optimized"}
        return (f"Method({self.name}, calls={self.call_count}, "
                f"tier={tier_names[self.compiled_tier]})")


class InlineCache:
    """
    Inline cache entry for dynamic dispatch optimization.
    States: uninitialized -> monomorphic -> polymorphic -> megamorphic
    """
    UNINIT = 0
    MONO = 1
    POLY = 2
    MEGA = 3

    def __init__(self, callsite_id: str):
        self.callsite_id = callsite_id
        self.state = self.UNINIT
        self.cached_types: List[Tuple[str, Callable]] = []  # (type_name, target_fn)
        self.poly_limit = 4

    def lookup(self, receiver_type: str, slow_lookup: Callable) -> Callable:
        """
        Fast path: check cache. Slow path: full method lookup.
        Monomorphic: 1 check. Polymorphic: linear scan. Mega: always slow.
        """
        # Check cache
        for cached_type, target in self.cached_types:
            if cached_type == receiver_type:
                return target

        # Cache miss: slow path
        target = slow_lookup(receiver_type)

        if self.state == self.UNINIT:
            self.state = self.MONO
            self.cached_types = [(receiver_type, target)]
        elif self.state == self.MONO:
            self.state = self.POLY
            self.cached_types.append((receiver_type, target))
        elif self.state == self.POLY:
            if len(self.cached_types) >= self.poly_limit:
                self.state = self.MEGA
                self.cached_types.clear()  # give up caching
            else:
                self.cached_types.append((receiver_type, target))
        # MEGA: don't cache

        return target

    def state_name(self) -> str:
        return {0: "uninit", 1: "monomorphic",
                2: "polymorphic", 3: "megamorphic"}[self.state]


class TieredJIT:
    """Simulates tiered JIT compilation (like JVM HotSpot C1/C2)."""

    INTERP_THRESHOLD = 10    # calls before baseline JIT
    OPT_THRESHOLD = 100      # calls before optimizing JIT
    DEOPT_LIMIT = 3          # max deopts before giving up optimization

    def __init__(self):
        self.methods: Dict[str, MethodProfile] = {}
        self.compilation_log: List[str] = []

    def register_method(self, name: str):
        self.methods[name] = MethodProfile(name)

    def invoke(self, name: str, hot_loop_iters: int = 0):
        """Simulate method invocation with tiered compilation."""
        if name not in self.methods:
            self.register_method(name)
        prof = self.methods[name]
        prof.call_count += 1

        # Tier transitions
        if prof.compiled_tier == 0 and prof.call_count >= self.INTERP_THRESHOLD:
            prof.compiled_tier = 1
            self.compilation_log.append(
                f"  [JIT] {name}: interpreted -> baseline (call #{prof.call_count})"
            )

        if prof.compiled_tier == 1 and prof.call_count >= self.OPT_THRESHOLD:
            if prof.deopt_count < self.DEOPT_LIMIT:
                prof.compiled_tier = 2
                self.compilation_log.append(
                    f"  [JIT] {name}: baseline -> optimized (call #{prof.call_count})"
                )

    def deoptimize(self, name: str, reason: str):
        """Fall back to interpreter when assumptions break."""
        if name in self.methods:
            prof = self.methods[name]
            prof.compiled_tier = 0
            prof.deopt_count += 1
            self.compilation_log.append(
                f"  [DEOPT] {name}: optimized -> interp (reason: {reason}, "
                f"deopt #{prof.deopt_count})"
            )

    def osr_opportunity(self, name: str, loop_iteration: int):
        """On-Stack Replacement: compile and switch mid-loop."""
        if name in self.methods:
            prof = self.methods[name]
            if prof.compiled_tier < 2 and loop_iteration > 1000:
                self.compilation_log.append(
                    f"  [OSR] {name}: on-stack replacement at iteration {loop_iteration}"
                )
                prof.compiled_tier = 2


def demo_jit_compilation():
    print("=" * 70)
    print("7. JIT COMPILATION")
    print("=" * 70)
    print("""
JIT (Just-In-Time) compilation converts bytecode/IR to native machine code
at runtime, guided by profiling data.

Key techniques:

  Hot Method Detection:
    Count method invocations. When count > threshold, trigger compilation.
    JVM: invocation counter + backedge counter (loop iterations).

  Tiered Compilation (JVM HotSpot):
    Tier 0: Interpreter (collect profile data)
    Tier 1: C1 baseline compiler (fast compile, modest optimization)
    Tier 2: C2 optimizing compiler (slow compile, aggressive optimization)

  Inline Caching (V8, HotSpot):
    Cache the resolved method for a callsite based on receiver type.
    Monomorphic: 1 type seen -> direct call (fastest)
    Polymorphic: 2-4 types -> linear search
    Megamorphic: too many types -> always do full lookup

  On-Stack Replacement (OSR):
    A long-running loop is still in interpreted code.
    OSR compiles the method and switches to compiled code mid-execution.
    Requires mapping interpreter state to compiled frame layout.

  Deoptimization:
    Optimized code made assumptions (e.g., "x is always int").
    When assumption breaks, bail out to interpreter with correct state.
    Uncommon trap: patched into compiled code at speculation points.
""")
    # Simulate tiered compilation
    print("  --- Tiered Compilation Simulation ---")
    jit = TieredJIT()
    jit.register_method("calculateTotal")
    jit.register_method("parseInput")

    for i in range(120):
        jit.invoke("calculateTotal")
    for i in range(15):
        jit.invoke("parseInput")

    for log in jit.compilation_log:
        print(f"  {log}")

    # Deoptimization
    jit.deoptimize("calculateTotal", "type guard failed: expected Int, got String")
    # Re-warm
    for i in range(120):
        jit.invoke("calculateTotal")
    for log in jit.compilation_log[-3:]:
        print(f"  {log}")

    # Inline caching demo
    print("\n  --- Inline Cache Simulation ---")

    def slow_method_lookup(type_name: str) -> Callable:
        """Simulates vtable/method table lookup."""
        return lambda: f"{type_name}.draw()"

    ic = InlineCache("shape.draw@line42")
    for type_name in ["Circle", "Circle", "Circle", "Square", "Triangle",
                       "Hexagon", "Pentagon", "Star"]:
        fn = ic.lookup(type_name, slow_method_lookup)
        print(f"    Call {type_name}.draw() -> IC state: {ic.state_name()}, "
              f"cached: {len(ic.cached_types)} types")

    # OSR demo
    print("\n  --- On-Stack Replacement ---")
    jit2 = TieredJIT()
    jit2.register_method("longLoop")
    jit2.invoke("longLoop")  # enters loop while still interpreted
    for i in [100, 500, 1000, 1500]:
        jit2.osr_opportunity("longLoop", i)
    for log in jit2.compilation_log:
        print(f"  {log}")
    print()


# ==========================================================================
# 8. RUNTIME MEMORY -- Stack Frames, Calling Conventions, Escape Analysis
# ==========================================================================

def demo_runtime_memory():
    print("=" * 70)
    print("8. RUNTIME MEMORY -- Stack Frames & Object Layout")
    print("=" * 70)
    print("""
  Stack Frame Layout (x86-64, simplified):
  +-----------------------+  High address
  |   Caller's frame      |
  +-----------------------+
  |   Return address      |  <- pushed by CALL instruction
  +-----------------------+
  |   Saved RBP (old FP)  |  <- frame pointer (RBP)
  +-----------------------+
  |   Local var 1         |  [RBP - 8]
  |   Local var 2         |  [RBP - 16]
  |   ...                 |
  +-----------------------+
  |   Spilled registers   |
  +-----------------------+
  |   Outgoing args       |  <- stack pointer (RSP)
  +-----------------------+  Low address

  Calling Conventions (x86-64 System V ABI):
    Args 1-6:  RDI, RSI, RDX, RCX, R8, R9
    Float args: XMM0-XMM7
    Return:    RAX (integer), XMM0 (float)
    Callee-saved: RBX, RBP, R12-R15
    Caller-saved: RAX, RCX, RDX, RSI, RDI, R8-R11

  Windows x64 is different:
    Args: RCX, RDX, R8, R9 (only 4 in registers)
    32-byte "shadow space" always reserved on stack

  Escape Analysis:
    Determines if an object's lifetime is bounded by its creating method.

    No escape:   Object used only within the method
                 -> Allocate on stack (no GC needed!)
                 -> Scalar replacement: break object into local vars

    Arg escape:  Object passed to called method but doesn't outlive caller
                 -> May still stack-allocate if callee is inlined

    Global escape: Object stored in field, returned, or assigned to global
                 -> Must heap-allocate

    Example (Java/Go):
      func newPoint(x, y int) *Point {
          p := &Point{x, y}   // p escapes (returned)
          return p             // -> must heap-allocate
      }
      func distance(a, b Point) float64 {
          dx := a.x - b.x     // dx does NOT escape
          dy := a.y - b.y     // -> stack allocated
          return math.Sqrt(dx*dx + dy*dy)
      }

  Object Header Layout (JVM HotSpot, 64-bit):
  +--------------------+
  | Mark Word (8 bytes)|  hash code, GC age, lock state, GC bits
  +--------------------+
  | Klass Pointer (4B) |  compressed class pointer -> method table (vtable)
  +--------------------+
  | Instance fields     |  laid out by field type, with alignment padding
  +--------------------+
  | Padding (0-7 bytes)|  align to 8-byte boundary
  +--------------------+

  Vtable (Virtual Method Table):
  +--------------------+
  | Klass metadata     |
  +--------------------+
  | vtable[0]          |  -> Object.hashCode native code
  | vtable[1]          |  -> Object.equals native code
  | vtable[2]          |  -> MyClass.myMethod native code
  +--------------------+

  Virtual dispatch: obj->klass->vtable[method_index]()
    - 2 pointer dereferences (cache-friendly if hot)
    - Devirtualization: JIT proves only one implementation -> direct call

  Memory alignment matters:
    struct Bad  { char a; long b; char c; }  // 24 bytes (padding!)
    struct Good { long b; char a; char c; }  // 16 bytes (packed)
""")

    # Simple escape analysis simulation
    print("  --- Escape Analysis Simulation ---")

    class EscapeAnalyzer:
        def analyze(self, allocations: List[Dict]) -> List[Dict]:
            results = []
            for alloc in allocations:
                name = alloc['name']
                returned = alloc.get('returned', False)
                stored_in_field = alloc.get('stored_in_field', False)
                passed_to_fn = alloc.get('passed_to_fn', False)
                fn_inlined = alloc.get('fn_inlined', False)

                if returned or stored_in_field:
                    escape = "global"
                    location = "HEAP"
                elif passed_to_fn and not fn_inlined:
                    escape = "arg"
                    location = "HEAP (maybe stack if inlined)"
                else:
                    escape = "none"
                    location = "STACK (scalar replacement possible)"

                results.append({
                    'name': name, 'escape': escape, 'location': location
                })
            return results

    allocations = [
        {'name': 'point', 'returned': True},
        {'name': 'temp_buffer', 'returned': False, 'stored_in_field': False},
        {'name': 'shared_map', 'stored_in_field': True},
        {'name': 'callback_arg', 'passed_to_fn': True, 'fn_inlined': False},
        {'name': 'helper_obj', 'passed_to_fn': True, 'fn_inlined': True},
    ]

    analyzer = EscapeAnalyzer()
    results = analyzer.analyze(allocations)
    for r in results:
        print(f"    {r['name']:20s} escape={r['escape']:8s} -> {r['location']}")
    print()


# ==========================================================================
# 9. TIER 1-4 PRIORITY GUIDE
# ==========================================================================

def show_priorities():
    print("=" * 70)
    print("9. LEARNING PRIORITY -- Tier 1-4")
    print("=" * 70)
    print("""
  TIER 1 -- Must Know (Interview Essentials)
  -------------------------------------------
  [x] Garbage Collection: mark-sweep, generational, GC roots concept
      -> "Explain how GC works in JVM/Python/Go"
      -> Know: stop-the-world vs concurrent, generational hypothesis
  [x] Stack vs Heap: when objects go where, stack frame basics
      -> "Why is stack allocation faster? What causes stack overflow?"
  [x] Reference counting vs tracing GC trade-offs
      -> CPython uses refcount + cycle detector. JVM uses tracing only.
  [x] Basic compilation pipeline: source -> tokens -> AST -> IR -> machine code
      -> Know the stages even if you can't implement them

  TIER 2 -- Should Know (Senior Engineer Level)
  -----------------------------------------------
  [x] Type systems: static vs dynamic, structural vs nominal
      -> TypeScript: structural. Java: nominal. Python: dynamic (gradual).
  [x] JIT basics: why V8/JVM are fast, tiered compilation concept
      -> Interpreter collects profiles, JIT optimizes hot code
  [x] Inline caching: why polymorphic code is slower
      -> Monomorphic callsites are 10-100x faster than megamorphic
  [x] IR and basic optimizations: constant folding, dead code elimination
      -> LLVM IR is SSA-based; optimizations are composable passes
  [x] Escape analysis: stack allocation optimization
      -> Go does this aggressively; JVM since Java 6

  TIER 3 -- Deep Knowledge (Compiler/Runtime Engineer)
  -----------------------------------------------------
  [x] Pratt parsing / operator precedence parsing
      -> Elegant alternative to recursive descent for expressions
  [x] Register allocation: graph coloring, linear scan
      -> Graph coloring: optimal but NP-hard. Linear scan: JIT-friendly.
  [x] Hindley-Milner type inference: unification algorithm
      -> Foundation of ML/Haskell type systems. Rust uses partial HM.
  [x] Tri-color marking, concurrent GC invariants
      -> SATB (snapshot-at-beginning) vs incremental update barriers
  [x] Copying collector: Cheney's algorithm, semi-space
  [x] On-stack replacement, deoptimization

  TIER 4 -- Expert (Language Implementor)
  -----------------------------------------
  [ ] SSA construction (dominance frontiers, phi nodes)
  [ ] Register allocation with coalescing (Iterated Register Coalescing)
  [ ] Advanced GC: ZGC colored pointers, Shenandoah Brooks pointers
  [ ] Partial evaluation, supercompilation
  [ ] Profile-guided optimization (PGO), auto-vectorization
  [ ] Polymorphic inline caches with guards and side exits
  [ ] Garbage collection for real-time systems (Metronome, RTGC)

  Key Interview Questions:
  ========================
  Q: "How does Python manage memory?"
  A: Reference counting for immediate cleanup + cyclic garbage collector
     (generational, 3 generations) for cycles. gc module lets you control it.

  Q: "Why is Java faster than Python for compute?"
  A: JVM JIT (C2) compiles hot methods to native code with type speculation,
     inlining, loop unrolling, vectorization. CPython is pure interpreter
     (though PyPy has a tracing JIT, and Python 3.13+ adds basic JIT).

  Q: "What happens when you call a virtual method?"
  A: Look up object's class pointer -> find vtable -> index into vtable
     -> call function pointer. JIT can devirtualize if only one impl exists.

  Q: "Explain how V8 executes JavaScript."
  A: Parse -> AST -> Ignition (bytecode interpreter, collects type feedback)
     -> TurboFan (optimizing JIT using Sea of Nodes IR)
     -> Deoptimize if type assumptions fail.
     Inline caches at every property access / method call.

  Q: "What is escape analysis and why does it matter?"
  A: Compiler proves object doesn't escape method scope -> allocates on stack
     instead of heap -> no GC pressure, better cache locality. Go and JVM
     both do this. Key for high-allocation-rate code (e.g., iterators).
""")


# ==========================================================================
# MAIN
# ==========================================================================

def main():
    print()
    print("*" * 70)
    print("*  COMPILER & RUNTIME INTERNALS                                    *")
    print("*  From source code to execution: the complete pipeline             *")
    print("*" * 70)
    print()

    demo_lexer()
    demo_parser()
    demo_type_inference()
    demo_ir_optimization()
    demo_register_allocation()
    demo_garbage_collection()
    demo_jit_compilation()
    demo_runtime_memory()
    show_priorities()

    print("=" * 70)
    print("END -- All compiler & runtime topics covered.")
    print("=" * 70)


if __name__ == "__main__":
    main()
