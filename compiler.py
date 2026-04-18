#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Name: Marinos Aristeidou
AM: 5397
Username: cs215397
"""

from dataclasses import dataclass
from fileinput import filename
import sys
from tkinter.font import names


@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    col: int


class LexError(Exception):
    pass


class Lexer:
    KEYWORDS = {
        "program": "PROGRAM",
        "declare": "DECLARE",
        "function": "FUNCTION",
        "if": "IF",
        "else": "ELSE",
        "while": "WHILE",
        "switchcase": "SWITCHCASE",
        "whilecase": "WHILECASE",
        "incase": "INCASE",
        "forcase": "FORCASE",
        "untilcase": "UNTILCASE",
        "when": "WHEN",
        "default": "DEFAULT",
        "until": "UNTIL",
        "return": "RETURN",
        "print": "PRINT",
        "input": "INPUT",
        "in": "IN",
        "inout": "INOUT",
        "not": "NOT",
        "and": "AND",
        "or": "OR",
    }

    SINGLE = {
        "{": "LBRACE",
        "}": "RBRACE",
        "(": "LPAREN",
        ")": "RPAREN",
        "[": "LBRACKET",
        "]": "RBRACKET",
        ",": "COMMA",
        ":": "COLON",
        "+": "PLUS",
        "-": "MINUS",
        "*": "MUL",
    }

    TWO_OPS = {
        ":=": "ASSIGN",
        "<=": "LE",
        ">=": "GE",
        "<>": "NE",
    }

    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.line = 1
        self.col = 1

    def _peek(self, k=0) -> str:
        j = self.i + k
        if j >= len(self.text):
            return ""
        return self.text[j]

    def _advance(self) -> str:
        ch = self._peek(0)
        if ch == "":
            return ""
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _error(self, msg: str, line: int = None, col: int = None):
        if line is None:
            line = self.line
        if col is None:
            col = self.col
        raise LexError(f"Lexical error at line {line}, col {col}: {msg}")

    def _skip_ws_and_comments(self):
        while True:
            while self._peek() in (" ", "\t", "\r", "\n"):
                self._advance()

            if self._peek() == "/" and self._peek(1) == "/":
                self._advance()
                self._advance()
                while self._peek() not in ("", "\n"):
                    self._advance()
                continue

            if self._peek() == "/" and self._peek(1) == "*":
                start_line, start_col = self.line, self.col
                self._advance()
                self._advance()
                while True:
                    c = self._peek()
                    if c == "":
                        self._error("Unterminated block comment", start_line, start_col)
                    if c == "/" and self._peek(1) == "*":
                        self._error(
                            "Nested or double-open block comments are not allowed",
                            self.line,
                            self.col,
                        )
                    if c == "*" and self._peek(1) == "/":
                        self._advance()
                        self._advance()
                        break
                    self._advance()
                continue

            break

    def next_token(self) -> Token:
        self._skip_ws_and_comments()

        start_line, start_col = self.line, self.col
        ch = self._peek()

        if ch == "":
            return Token("EOF", "", start_line, start_col)

        if ch == ";" or ch == ";":
            self._advance()
            return Token("SEMI", ch, start_line, start_col)

        two = ch + self._peek(1)
        if two in self.TWO_OPS:
            self._advance()
            self._advance()
            return Token(self.TWO_OPS[two], two, start_line, start_col)

        if ch == "/":
            self._advance()
            return Token("DIV", "/", start_line, start_col)

        if ch == "<":
            self._advance()
            return Token("LT", "<", start_line, start_col)
        if ch == ">":
            self._advance()
            return Token("GT", ">", start_line, start_col)
        if ch == "=":
            self._advance()
            return Token("EQ", "=", start_line, start_col)

        if ch in self.SINGLE:
            self._advance()
            return Token(self.SINGLE[ch], ch, start_line, start_col)

        if ch.isalpha():
            buf = []
            while True:
                c = self._peek()
                if c.isalpha() or c.isdigit() or c == "_":
                    buf.append(self._advance())
                else:
                    break
            lex = "".join(buf)
            tok_type = self.KEYWORDS.get(lex, "ID")
            if tok_type == "ID" and len(lex) > 30:
                lex = lex[:30]
            return Token(tok_type, lex, start_line, start_col)

        if ch.isdigit() or (ch in "+-" and self._peek(1).isdigit()):
            sign = ""
            if ch in "+-":
                sign = self._advance()
            digits = []
            while self._peek().isdigit():
                digits.append(self._advance())
            lex = sign + "".join(digits)

            try:
                val = int(lex)
            except ValueError:
                self._error(f"Invalid integer literal '{lex}'", start_line, start_col)

            if val < -32767 or val > 32767:
                self._error(
                    f"Integer out of range: {val} (must be between -32767 and 32767)",
                    start_line,
                    start_col,
                )
            return Token("INTEGER", lex, start_line, start_col)

        self._error(f"Illegal character '{ch}'", start_line, start_col)


class SynError(Exception):
    pass

@dataclass
class Quad:
    label: int
    op: str
    x: str
    y: str
    z: str


class IntermediateCode:
    def __init__(self):
        self.quads = []
        self.temp_counter = 0

    def nextquad(self):
        return len(self.quads) + 1

    def genquad(self, op, x="_", y="_", z="_"):
        q = Quad(self.nextquad(), op, str(x), str(y), str(z))
        self.quads.append(q)
        return q.label

    def newtemp(self):
        self.temp_counter += 1
        return f"T_{self.temp_counter}"

    def emptylist(self):
        return []

    def makelist(self, x):
        return [x]

    def mergelist(self, l1, l2):
        return l1 + l2

    def backpatch(self, lst, z):
        for label in lst:
            for q in self.quads:
                if q.label == label:
                    q.z = str(z)
                    break

    def write_int_file(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            for q in self.quads:
                f.write(f"{q.label}: {q.op}, {q.x}, {q.y}, {q.z}\n")
                
@dataclass
class Entity:
    name: str
    kind: str
    mode: str = ""
    scope_level: int = 0


class Scope:
    def __init__(self, level):
        self.level = level
        self.entities = []

    def add_entity(self, entity: Entity):
        for e in self.entities:
            if e.name == entity.name:
                raise SynError(
                    f"Duplicate declaration of '{entity.name}' in scope level {self.level}"
                )
        self.entities.append(entity)


class SymbolTable:
    def __init__(self):
        self.scopes = []
        self.completed_scopes = []
        self.function_params = {}

    def enter_scope(self):
        level = len(self.scopes)
        self.scopes.append(Scope(level))

    def exit_scope(self):
        if not self.scopes:
            raise SynError("Attempt to exit scope while no scope exists")
        scope = self.scopes.pop()
        self.completed_scopes.append(scope)

    def current_scope(self):
        if not self.scopes:
            raise SynError("No active scope")
        return self.scopes[-1]

    def add_variable(self, name):
        scope = self.current_scope()
        scope.add_entity(Entity(name=name, kind="variable", scope_level=scope.level))

    def add_parameter(self, name, mode):
        scope = self.current_scope()
        scope.add_entity(
            Entity(name=name, kind="parameter", mode=mode, scope_level=scope.level)
        )

    def add_function(self, name):
        scope = self.current_scope()
        scope.add_entity(Entity(name=name, kind="function", scope_level=scope.level))

    def add_temp(self, name):
        scope = self.current_scope()
        # για να μην πετάει duplicate αν ξαναγίνει κατά λάθος
        for e in scope.entities:
            if e.name == name:
                return
        scope.add_entity(Entity(name=name, kind="temp", scope_level=scope.level))

    def lookup(self, name):
        for scope in reversed(self.scopes):
            for entity in scope.entities:
                if entity.name == name:
                    return entity
        return None

    def format_scope(self, scope: Scope):
        lines = [f"Scope level {scope.level}:"]
        if not scope.entities:
            lines.append("  (empty)")
            return "\n".join(lines)

        for e in scope.entities:
            if e.kind == "parameter":
                lines.append(f"  {e.name} | {e.kind} | {e.mode}")
            else:
                lines.append(f"  {e.name} | {e.kind}")
        return "\n".join(lines)

    def write_symb_file(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            for scope in self.completed_scopes:
                f.write(self.format_scope(scope))
                f.write("\n\n")
                
class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.lookahead = self.lexer.next_token()
        self.ic = IntermediateCode()
        self.symtab = SymbolTable()

        self._statement_handlers = {
            "IF": self.if_stat,
            "WHILE": self.while_stat,
            "SWITCHCASE": self.switchcase_stat,
            "WHILECASE": self.whilecase_stat,
            "INCASE": self.incase_stat,
            "FORCASE": self.forcase_stat,
            "UNTILCASE": self.untilcase_stat,
            "INPUT": self.input_stat,
            "PRINT": self.print_stat,
            "RETURN": self.return_stat,
            "LBRACE": self.statements,
        }
        self._statement_starters = set(self._statement_handlers.keys()) | {"ID"}

    def _error(self, msg: str):
        t = self.lookahead
        raise SynError(
            f"Syntax error at line {t.line}, col {t.col}: {msg} (found {t.type} '{t.lexeme}')"
        )

    def _eat(self, token_type: str):
        if self.lookahead.type == token_type:
            self.lookahead = self.lexer.next_token()
        else:
            self._error(f"Expected {token_type}")

    def _starts_statement(self, t: str) -> bool:
        return t in self._statement_starters

    def parse(self):
        self.program()
        if self.lookahead.type != "EOF":
            self._error("Expected EOF")

    def program(self):
        self._eat("PROGRAM")
        if self.lookahead.type != "ID":
            self._error("Expected program name")
        prog_name = self.lookahead.lexeme
        self._eat("ID")
        self.programblock(prog_name, is_main=True)

    def programblock(self, name=None, is_main=False):
        self.symtab.enter_scope()

        if hasattr(self, "formalpars_buffer") and self.formalpars_buffer:
            for pname, pmode in self.formalpars_buffer:
                self.symtab.add_parameter(pname, pmode)
            self.formalpars_buffer = []

        self._eat("LBRACE")
        self.declarations()
        self.functions()

        if name is not None:
            self.ic.genquad("begin_block", name, "_", "_")

        self.statements_sequence()

        if is_main:
            self.ic.genquad("halt", "_", "_", "_")

        if name is not None:
            self.ic.genquad("end_block", name, "_", "_")

        self._eat("RBRACE")

        self.symtab.exit_scope()

    def statements_sequence(self):
        if self._starts_statement(self.lookahead.type):
            self.statement()
            while self.lookahead.type == "SEMI":
                self._eat("SEMI")
                if self._starts_statement(self.lookahead.type):
                    self.statement()
                else:
                    break

    def declarations(self):
        while self.lookahead.type == "DECLARE":
            self._eat("DECLARE")
            self.varlist()
            self._eat("SEMI")

    def varlist(self):
        if self.lookahead.type == "ID":
            name = self.lookahead.lexeme
            self.symtab.add_variable(name)
            self._eat("ID")

            while self.lookahead.type == "COMMA":
                self._eat("COMMA")
                if self.lookahead.type != "ID":
                    self._error("Expected ID in declaration")
                name = self.lookahead.lexeme
                self.symtab.add_variable(name)
                self._eat("ID")

    def functions(self):
        while self.lookahead.type == "FUNCTION":
            self.function()

    def function(self):
        self._eat("FUNCTION")
        if self.lookahead.type != "ID":
            self._error("Expected function name")
        fname = self.lookahead.lexeme

        self.symtab.add_function(fname)

        self._eat("ID")
        self.formalpars_buffer = []
        self.formalpars()
        self.symtab.function_params[fname] = list(self.formalpars_buffer)
        self.programblock(fname, is_main=False)

    def formalpars(self):
        self._eat("LPAREN")
        self.formalparlist()
        self._eat("RPAREN")

    def formalparlist(self):
        if self.lookahead.type in ("IN", "INOUT"):
            self.formalparitem()
            while self.lookahead.type == "COMMA":
                self._eat("COMMA")
                self.formalparitem()

    def formalparitem(self):
        if self.lookahead.type == "IN":
            self._eat("IN")
            if self.lookahead.type != "ID":
                self._error("Expected ID after 'in'")
            pname = self.lookahead.lexeme
            self._eat("ID")
            self.formalpars_buffer.append((pname, "CV"))

        elif self.lookahead.type == "INOUT":
            self._eat("INOUT")
            if self.lookahead.type != "ID":
                self._error("Expected ID after 'inout'")
            pname = self.lookahead.lexeme
            self._eat("ID")
            self.formalpars_buffer.append((pname, "REF"))

        else:
            self._error("Expected 'in' or 'inout' in formal parameters")

    def statements(self):
        if self.lookahead.type == "LBRACE":
            self._eat("LBRACE")
            self.statements_sequence()
            self._eat("RBRACE")
        else:
            self.statement()

    def statement(self):
        if self.lookahead.type == "ID":
            self.id_started_statement()
            return
        fn = self._statement_handlers.get(self.lookahead.type)
        if not fn:
            self._error("Invalid statement start")
        fn()

    def id_started_statement(self):
        name = self.lookahead.lexeme
        self._eat("ID")

        if self.lookahead.type == "ASSIGN":
            self._eat("ASSIGN")
            e_place = self.expression()
            self.ic.genquad(":=", e_place, "_", name)

        elif self.lookahead.type == "LPAREN":
            self.actualpars(name)

        else:
            self._error("Expected ':=' or '(' after identifier")

    def if_stat(self):
        self._eat("IF")
        true_list, false_list = self.condition()

        self.ic.backpatch(true_list, self.ic.nextquad())
        self.statements()

        if self.lookahead.type == "ELSE":
            jump_list = self.ic.makelist(self.ic.genquad("jump", "_", "_", "_"))
            self.ic.backpatch(false_list, self.ic.nextquad())

            self._eat("ELSE")
            self.statements()

            self.ic.backpatch(jump_list, self.ic.nextquad())
        else:
            self.ic.backpatch(false_list, self.ic.nextquad())

    def while_stat(self):
        self._eat("WHILE")
        cond_quad = self.ic.nextquad()
        true_list, false_list = self.condition()

        self.ic.backpatch(true_list, self.ic.nextquad())
        self.statements()
        self.ic.genquad("jump", "_", "_", cond_quad)
        self.ic.backpatch(false_list, self.ic.nextquad())

    def switchcase_stat(self):
        self._eat("SWITCHCASE")

        exit_list = self.ic.emptylist()

        while self.lookahead.type == "WHEN":
            self._eat("WHEN")

            true_list, false_list = self.condition()
            self._eat("COLON")

            self.ic.backpatch(true_list, self.ic.nextquad())
            self.statements()

            t = self.ic.makelist(self.ic.genquad("jump", "_", "_", "_"))
            self.symtab.add_temp(t)
            exit_list = self.ic.mergelist(exit_list, t)

            self.ic.backpatch(false_list, self.ic.nextquad())

        self._eat("DEFAULT")
        self._eat("COLON")
        self.statements()

        self.ic.backpatch(exit_list, self.ic.nextquad())
        
    def whilecase_stat(self):
        self._eat("WHILECASE")

        first_quad = self.ic.nextquad()

        while self.lookahead.type == "WHEN":
            self._eat("WHEN")

            true_list, false_list = self.condition()
            self._eat("COLON")

            self.ic.backpatch(true_list, self.ic.nextquad())
            self.statements()
            self.ic.genquad("jump", "_", "_", first_quad)

            self.ic.backpatch(false_list, self.ic.nextquad())

        self._eat("DEFAULT")
        self._eat("COLON")
        self.statements()

    def incase_stat(self):
        self._eat("INCASE")

        t = self.ic.newtemp()
        first_quad = self.ic.nextquad()
        self.ic.genquad(":=", "0", "_", t)

        while self.lookahead.type == "WHEN":
            self._eat("WHEN")

            true_list, false_list = self.condition()
            self._eat("COLON")

            self.ic.backpatch(true_list, self.ic.nextquad())
            self.statements()
            self.ic.genquad(":=", "1", "_", t)

            self.ic.backpatch(false_list, self.ic.nextquad())

        self.ic.genquad("=", t, "1", first_quad)

    def forcase_stat(self):
        self._eat("FORCASE")

        if self.lookahead.type != "ID":
            self._error("Expected ID after forcase")
        counter_name = self.lookahead.lexeme
        self._eat("ID")

        self._eat("EQ")

        if self.lookahead.type != "INTEGER":
            self._error("Expected INTEGER in forcase")
        limit_value = self.lookahead.lexeme
        self._eat("INTEGER")

        self.ic.genquad(":=", "1", "_", counter_name)

        check_quad = self.ic.nextquad()
        true_list = self.ic.makelist(self.ic.genquad("<=", counter_name, limit_value, "_"))
        false_list = self.ic.makelist(self.ic.genquad("jump", "_", "_", "_"))

        self.ic.backpatch(true_list, self.ic.nextquad())

        while self.lookahead.type == "WHEN":
            self._eat("WHEN")

            cond_true, cond_false = self.condition()
            self._eat("COLON")

            self.ic.backpatch(cond_true, self.ic.nextquad())
            self.statements()
            self.ic.backpatch(cond_false, self.ic.nextquad())

        temp = self.ic.newtemp()
        self.symtab.add_temp(temp)
        self.ic.genquad("+", counter_name, "1", temp)
        self.ic.genquad(":=", temp, "_", counter_name)
        self.ic.genquad("jump", "_", "_", check_quad)

        self.ic.backpatch(false_list, self.ic.nextquad())

    def untilcase_stat(self):
        self._eat("UNTILCASE")

        first_quad = self.ic.nextquad()

        while self.lookahead.type == "WHEN":
            self._eat("WHEN")

            true_list, false_list = self.condition()
            self._eat("COLON")

            self.ic.backpatch(true_list, self.ic.nextquad())
            self.statements()

            self.ic.backpatch(false_list, self.ic.nextquad())

        self._eat("UNTIL")
        true_list, false_list = self.condition()

        self.ic.backpatch(true_list, self.ic.nextquad())
        self.ic.backpatch(false_list, first_quad)
        
    def print_stat(self):
        self._eat("PRINT")
        e_place = self.expression()
        self.ic.genquad("out", e_place, "_", "_")

    def input_stat(self):
        self._eat("INPUT")
        if self.lookahead.type != "ID":
            self._error("Expected ID after input")
        name = self.lookahead.lexeme
        self._eat("ID")
        self.ic.genquad("inp", name, "_", "_")

    def return_stat(self):
        self._eat("RETURN")
        e_place = self.expression()
        self.ic.genquad("retv", e_place, "_", "_")

    def actualpars(self, func_name):
        self._eat("LPAREN")
        params = []

        if self.lookahead.type in ("IN", "INOUT"):
            params.append(self.actualparitem())
            while self.lookahead.type == "COMMA":
                self._eat("COMMA")
                params.append(self.actualparitem())

        self._eat("RPAREN")

        for mode, value in params:
            if mode == "CV":
                self.ic.genquad("par", value, "CV", "_")
            else:
                self.ic.genquad("par", value, "REF", "_")

        ret_temp = self.ic.newtemp()
        self.symtab.add_temp(ret_temp)
        self.ic.genquad("par", ret_temp, "RET", "_")
        self.ic.genquad("call", func_name, "_", "_")
        return ret_temp

    def actualparlist(self):
        if self.lookahead.type in ("IN", "INOUT"):
            self.actualparitem()
            while self.lookahead.type == "COMMA":
                self._eat("COMMA")
                self.actualparitem()

    def actualparitem(self):
        if self.lookahead.type == "IN":
            self._eat("IN")
            e_place = self.expression()
            return ("CV", e_place)

        elif self.lookahead.type == "INOUT":
            self._eat("INOUT")
            if self.lookahead.type != "ID":
                self._error("Expected ID after inout")
            name = self.lookahead.lexeme
            self._eat("ID")
            return ("REF", name)

        else:
            self._error("Expected actual parameter item")

    def condition(self):
        true_list, false_list = self.boolterm()

        while self.lookahead.type == "OR":
            self._eat("OR")
            self.ic.backpatch(false_list, self.ic.nextquad())
            t2, f2 = self.boolterm()
            true_list = self.ic.mergelist(true_list, t2)
            false_list = f2

        return true_list, false_list

    def boolterm(self):
        true_list, false_list = self.boolfactor()

        while self.lookahead.type == "AND":
            self._eat("AND")
            self.ic.backpatch(true_list, self.ic.nextquad())
            t2, f2 = self.boolfactor()
            false_list = self.ic.mergelist(false_list, f2)
            true_list = t2

        return true_list, false_list

    def boolfactor(self):
        if self.lookahead.type == "NOT":
            self._eat("NOT")
            self._eat("LBRACKET")
            t, f = self.condition()
            self._eat("RBRACKET")
            return f, t

        elif self.lookahead.type == "LBRACKET":
            self._eat("LBRACKET")
            t, f = self.condition()
            self._eat("RBRACKET")
            return t, f

        else:
            e1 = self.expression()
            relop = self.relational_oper()
            e2 = self.expression()

            true_list = self.ic.makelist(self.ic.genquad(relop, e1, e2, "_"))
            false_list = self.ic.makelist(self.ic.genquad("jump", "_", "_", "_"))
            return true_list, false_list

    def relational_oper(self):
        if self.lookahead.type == "EQ":
            self._eat("EQ")
            return "="
        elif self.lookahead.type == "LE":
            self._eat("LE")
            return "<="
        elif self.lookahead.type == "GE":
            self._eat("GE")
            return ">="
        elif self.lookahead.type == "NE":
            self._eat("NE")
            return "<>"
        elif self.lookahead.type == "LT":
            self._eat("LT")
            return "<"
        elif self.lookahead.type == "GT":
            self._eat("GT")
            return ">"
        else:
            self._error("Expected relational operator")

    def expression(self):
        sign = None
        if self.lookahead.type in ("PLUS", "MINUS"):
            sign = self.lookahead.type
            self._eat(self.lookahead.type)

        place = self.term()

        if sign == "MINUS":
            w = self.ic.newtemp()
            self.symtab.add_temp(w)
            self.ic.genquad("-", "0", place, w)
            place = w

        while self.lookahead.type in ("PLUS", "MINUS"):
            op_token = self.lookahead.type
            self._eat(op_token)
            t2 = self.term()
            w = self.ic.newtemp()
            self.symtab.add_temp(w)
            op = "+" if op_token == "PLUS" else "-"
            self.ic.genquad(op, place, t2, w)
            place = w

        return place

    def term(self):
        place = self.factor()
        while self.lookahead.type in ("MUL", "DIV"):
            op_token = self.lookahead.type
            self._eat(op_token)
            f2 = self.factor()
            w = self.ic.newtemp()
            self.symtab.add_temp(w)
            op = "*" if op_token == "MUL" else "/"
            self.ic.genquad(op, place, f2, w)
            place = w
        return place

    def factor(self):
        if self.lookahead.type == "INTEGER":
            value = self.lookahead.lexeme
            self._eat("INTEGER")
            return value

        elif self.lookahead.type == "LPAREN":
            self._eat("LPAREN")
            place = self.expression()
            self._eat("RPAREN")
            return place

        elif self.lookahead.type == "ID":
            name = self.lookahead.lexeme
            self._eat("ID")
            return self.idtail(name)

        else:
            self._error("Expected factor")

    def idtail(self, name):
        if self.lookahead.type == "LPAREN":
            return self.actualpars(name)
        return name


def main(argv):
    if len(argv) < 2:
        print("Usage: py compiler.py <input_file.c++>")
        return 2

    filename = argv[1]

    try:
        with open(filename, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"Cannot open file: {filename}\n{e}")
        return 2

    try:
        lexer = Lexer(text)
        parser = Parser(lexer)
        parser.parse()
        print("PHASE 1 OK (Lexical + Syntax analysis)")
        base = filename.rsplit(".", 1)[0]
        parser.ic.write_int_file(base + ".int")
        parser.symtab.write_symb_file(base + ".symb")
        print("PHASE 2 OK (Intermediate code + Symbol table generated)")
        return 0
    except (LexError, SynError) as e:
        print(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
