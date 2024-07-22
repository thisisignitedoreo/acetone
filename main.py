
from dataclasses import dataclass
import pyclip
import base64
import zlib
import sys
import os

clamp = lambda a, b, x: max(a, min(x, b))

def strtofont(string):
    res = {}
    lines = string.split("\n")
    sx, sy = map(float, lines[0].split())
    lines = lines[1:]
    c = None
    for i in lines:
        if i.startswith("#"): continue
        if len(i) == 1:
            res[i] = []
            c = i
        elif len(i) == 2:
            res[c].append(None)
        elif len(i) == 0:
            pass
        else:
            a, b = map(float, i.split())
            res[c].append((a, b))
    return sx, sy, res

sx, sy, font = strtofont(open("font.txt").read())

## LEX

TOKEN_NUMBER = "TOKEN_NUMBER"
TOKEN_WORD = "TOKEN_WORD"
TOKEN_OCURLY = "TOKEN_OCURLY"
TOKEN_CCURLY = "TOKEN_CCURLY"
TOKEN_REFNUMBER = "TOKEN_REFNUMBER"
TOKEN_SEMICOLON = "TOKEN_SEMICOLON"
TOKEN_EQUALS = "TOKEN_EQUALS"

literal_tokens = {
    "=": TOKEN_EQUALS,
    ";": TOKEN_SEMICOLON,
    "{": TOKEN_OCURLY,
    "}": TOKEN_CCURLY,
}
inv_lit_tokens = {i: k for k, i in literal_tokens.items()}

@dataclass
class Location:
    filename: str
    line: int
    char: int

    def __str__(self): return f"{self.filename}:{self.line}:{self.char}"

@dataclass
class Token:
    loc: Location
    value: str
    type: str
    pair: int | None = None

    def __str__(self): return f"{self.loc}: Token {self.type}: {self.value}"

@dataclass
class RefNumber:
    val: int
    def __str__(self): return f'[{self.val}]'

ALPHABET = "qwertyuyiopasdfghjklzxcvbnm"
NUMBERS = "1234567890"

def error_loc(loc, string):
    print(loc, ": error: ", string, sep="")
    file = open(loc.filename).readlines()
    nums = []
    if loc.line != 1: nums.append(loc.line-1)
    nums.append(loc.line)
    if loc.line != len(file)-1:nums.append(loc.line+1)
    ls = list(map(lambda x: len(str(x)), nums))
    l = max(ls)

    if loc.line != 1:
        print(f'{" "*(l-ls[0])}{loc.line-1} | {file[loc.line-2].rstrip("\n")}')
    print(f'{" "*(l-ls[1])}{loc.line} | {file[loc.line-1].rstrip("\n")}')
    print(f'{" "*(l-ls[1])}{" "*len(str(loc.line))} | {" "*(loc.char-1)}^')
    if loc.line != len(file)-1:
        print(f'{" "*(l-ls[2])}{loc.line+1} | {file[loc.line].rstrip("\n")}')
    sys.exit(1)

def error(string):
    print("error: ", string, sep="")
    sys.exit(1)

def lex(src, filename):
    tokens = []
    n = 0
    line, char = 1, 1
    while n < len(src):
        if src[n] in " \r\t\n":
            char += 1
            if src[n] == '\n':
                line += 1
                char = 1
            n += 1
            continue

        if n < len(src) - 1 and src[n] == "/" and src[n+1] == "/":
            n += 2
            char += 2
            while src[n] != "\n":
                char += 2
                n += 1
        
        if src[n] in ALPHABET + ALPHABET.upper() + "_+-:/!?":
            char_start = char
            buffer = ""
            while src[n] in ALPHABET + ALPHABET.upper() + NUMBERS + "_+-:/!?":
                buffer += src[n]
                n += 1
                char += 1
            tokens.append(
                Token(
                    Location(filename, line, char_start),
                    buffer,
                    TOKEN_WORD
                )
            )
        elif src[n] in NUMBERS:
            char_start = char
            buffer = ""
            while src[n] in NUMBERS:
                buffer += src[n]
                n += 1
                char += 1
            tokens.append(
                Token(
                    Location(filename, line, char_start),
                    int(buffer),
                    TOKEN_NUMBER
                )
            )
        elif src[n] in literal_tokens.keys():
            tokens.append(
                Token(
                    Location(filename, line, char),
                    src[n],
                    literal_tokens[src[n]]
                )
            )
            n += 1
            char += 1
        elif src[n] == "[":
            buf = ""
            n += 1
            char += 1
            while src[n] != ']':
                if src[n] not in NUMBERS:
                    error_loc(Location(filename, line, char), "expected only numbers")
                buf += src[n]
                char += 1
                n += 1
            n += 1
            char += 1
            buf = int(buf.strip())
            
            tokens.append(
                Token(
                    Location(filename, line, char),
                    RefNumber(buf),
                    TOKEN_REFNUMBER
                )
            )
    return tokens

def crossreference(lexed):
    stack = []
    result = []
    for k, i in enumerate(lexed):
        if i.type == TOKEN_OCURLY:
            stack.append(k)
            result.append(i)
        elif i.type == TOKEN_CCURLY:
            if not stack:
                error_loc(i.loc, "no opening curly for this closing curly")
            ocurly = stack.pop()
            result[ocurly].pair = k
            result.append(i)
            result[-1].pair = ocurly
        else:
            result.append(i)
    
    if stack: error_loc(lexed[stack[-1]].loc, "unclosed curly")

    return result

## COMMENTS

def draw_comment(string, font_size=60000, pad=(2000, 3000), kerning=3000):
    cur = [pad[0] + 1, pad[1] + 1]
    w, h = font_size/sx, font_size/sy
    result = []
    for i in string:
        i = i.lower()
        if i not in font.keys(): continue
        for j in font[i]:
            if j is None: result.append((0, 0))
            else: result.append((clamp(0, 65535, cur[0] + j[0] * w), clamp(0, 65535, cur[1] + j[1] * h)))
        cur[0] += w + kerning
        result.append((0, 0))
    is_zero = False
    res = []
    for i in result:
        if is_zero:
            if i != (0, 0):
                res.append(i)
                is_zero = False
        else:
            res.append(i)
            if i == (0, 0): is_zero = True
    return res

lerp = lambda a, b, t: (b - a) * t + a
lerp2d = lambda a, b, t: (lerp(a[0], b[0], t), lerp(a[1], b[1], t))

def draw_bezier_curve(p1, p2, pC, ps=100):
    res = []
    for i in range(ps):
        t = i/ps
        a = lerp2d(p1, pC, t)
        b = lerp2d(pC, p2, t)
        res.append(lerp2d(a, b, t))
    return res

def encode_drawing(res):
    blob = b""
    blob += int.to_bytes(len(res), 4, "little")
    for x, y in res:
        blob += int.to_bytes(int(x), 2, "little")
        blob += int.to_bytes(int(y), 2, "little")
    blob += b"\x00" * (1028 - len(blob))
    return base64.b64encode(zlib.compress(blob)).rstrip(b"=").decode()

## PARSING

OP_LABEL = "LABEL"
OP_INBOX = "INBOX"
OP_OUTBOX = "OUTBOX"
OP_COPYTO = "COPYTO"
OP_COPYFROM = "COPYFROM"
OP_ADD = "ADD"
OP_SUB = "SUB"
OP_BUMPA = "BUMPUP"
OP_BUMPS = "BUMPDN"
OP_JUMP = "JUMP"
OP_JUMPZ = "JUMPZ"
OP_JUMPN = "JUMPN"
OP_COMMENT = "COMMENT"

@dataclass
class Op:
    op: str
    operand: any
    loc: Location

    def op_str(self): return f'{self.op:<10}'
    def __str__(self): return f'{self.loc}: {self.op} {self.operand}'

def token_type_word(token, istype=False):
    if istype: token_type = token
    else: token_type = token.type
    if token_type == TOKEN_WORD: return "word"
    if token_type == TOKEN_NUMBER: return "number"
    if token_type == TOKEN_SEMICOLON: return "semicolon"
    if token_type == TOKEN_OCURLY: return "opening curly brace"
    if token_type == TOKEN_CCURLY: return "closing curly brace"
    if token_type == TOKEN_EQUALS: return "equal sign"
    if token_type == TOKEN_REFNUMBER: return "pointer"
    return "unknown"

def parse_condition(condition, ifloc, loop=False):
    if len(condition) == 0 and not loop:
        error_loc(ifloc, "expected condition")
    elif len(condition) == 0 and loop:
        return ""
    fcondition = condition[0].value.lower()
    if fcondition == "zero":
        return "z"
    elif fcondition == "negative":
        return "n"
    elif fcondition == "not":
        if len(condition) == 1:
            error_loc(condition[0].loc, "expected `not zero`")
        fcondition = condition[1].value.lower()
        if fcondition == "zero":
            return "!z"
        else:
            error_loc(condition[0].loc, "expected `not zero`")
    else:
        error_loc(condition[0].loc, "expected either `zero`, `positive` or `negative`")

def parse_types(types):
    exp_types = list(map(lambda x: token_type_word("TOKEN_" + x, True), lstrip(types, "TOKEN_").split("TOKEN_")))
    if len(exp_types) == 1:
        exp_str = token_type_word(exp_types[0], True)
    else:
        exp_str = ", ".join(exp_types[:-1])
        exp_str += f" or {exp_types[-1]}"
    return exp_str

def check_params(op, oploc, params, signature, var=False):
    if len(signature) != len(params) and not var:
        error_loc(oploc, f"{op} takes {len(signature)} params, but got {len(params)}")

    for k, i in enumerate(params):
        if i.type not in signature[k%len(signature)]:
            error_loc(i.loc, f"parameter {k+1} should be {parse_types(signature[k%len(signature)])}, not {token_type_word(i)}")

lstrip = lambda x, s: x[len(s):] if x.startswith(s) else x

def expect(token, expected_type):
    if token.type not in expected_type:
        error_loc(token.loc, f"expected {parse_types(expected_type)}, got {token_type_word(token)}")

macros = {}
sections = set()

def parse(lexed, r=0, last_loop=-1):
    global macros, sections
    prg = []
    n = 0

    while n < len(lexed):
        current_token = lexed[n]
        expect(current_token, TOKEN_WORD)
        
        operation = lexed[n].value.lower()
        oploc = lexed[n].loc
        oppos = n

        if operation == "if":
            condition = []
            n += 1
            while lexed[n].type != TOKEN_OCURLY:
                condition.append(lexed[n])
                n += 1
            ifbranch = parse(lexed[n+1:lexed[n].pair-r], r+n+1, last_loop)
            n = lexed[n].pair + 1 - r
            print(lexed[n-1])
            if n < len(lexed) and lexed[n].value == "else":
                n += 1
                elsebranch = parse(lexed[n+1:lexed[n].pair-r], r+n+1, last_loop)
                n = lexed[n].pair + 1 - r
            else:
                elsebranch = []
            condition = parse_condition(condition, oploc)
            if condition == "z":
                prg.append(Op(OP_JUMPZ, f"styreneif{oppos + r}start", oploc))
                prg.append(Op(OP_JUMP, f"styreneif{oppos + r}else", oploc))
            if condition == "n":
                prg.append(Op(OP_JUMPN, f"styreneif{oppos + r}start", oploc))
                prg.append(Op(OP_JUMP, f"styreneif{oppos + r}else", oploc))
            if condition == "!z":
                prg.append(Op(OP_JUMPZ, f"styreneif{oppos + r}else", oploc))
            if condition == "!n":
                prg.append(Op(OP_JUMPN, f"styreneif{oppos + r}else", oploc))
            prg.append(Op(OP_LABEL, f"styreneif{oppos + r}start", oploc))
            prg += ifbranch
            prg.append(Op(OP_JUMP, f"styreneif{oppos + r}end", oploc))
            prg.append(Op(OP_LABEL, f"styreneif{oppos + r}else", oploc))
            prg += elsebranch
            prg.append(Op(OP_LABEL, f"styreneif{oppos + r}end", oploc))
        elif operation == "while":
            # start:
            #  BODY
            # if !z: goto start
            # skip:
            n += 1
            condition = []
            while lexed[n].type != TOKEN_OCURLY:
                condition.append(lexed[n])
                n += 1
            condition = parse_condition(condition, oploc, loop=True)
            body = parse(lexed[n+1:lexed[n].pair-r], r+n+1, oppos + r)
            if condition == "z":
                prg.append(Op(OP_JUMPZ, f"styreneloop{oppos + r}", oploc))
                prg.append(Op(OP_JUMP, f"styreneloop{oppos + r}skip", oploc))
            if condition == "!z":
                prg.append(Op(OP_JUMPZ, f"styreneloop{oppos + r}skip", oploc))
                prg.append(Op(OP_JUMP, f"styreneloop{oppos + r}", oploc))
            if condition == "n":
                prg.append(Op(OP_JUMPN, f"styreneloop{oppos + r}", oploc))
                prg.append(Op(OP_JUMP, f"styreneloop{oppos + r}skip", oploc))
            if condition == "!n":
                prg.append(Op(OP_JUMPN, f"styreneloop{oppos + r}skip", oploc))
                prg.append(Op(OP_JUMP, f"styreneloop{oppos + r}", oploc))
            prg.append(Op(OP_LABEL, f"styreneloop{oppos + r}", oploc))
            prg += body
            prg.append(Op(OP_LABEL, f"styreneloop{oppos + r}check", oploc))
            if condition == "": prg.append(Op(OP_JUMP, f"styreneloop{oppos + r}", oploc))
            if condition == "z": prg.append(Op(OP_JUMPZ, f"styreneloop{oppos + r}", oploc))
            if condition == "!z":
                prg.append(Op(OP_JUMPZ, f"styreneloop{oppos + r}skip", oploc))
                prg.append(Op(OP_JUMP, f"styreneloop{oppos + r}", oploc))
            if condition == "n": prg.append(Op(OP_JUMPN, f"styreneloop{oppos + r}", oploc))
            if condition == "!n":
                prg.append(Op(OP_JUMPN, f"styreneloop{oppos + r}skip", oploc))
                prg.append(Op(OP_JUMP, f"styreneloop{oppos + r}", oploc))
            prg.append(Op(OP_LABEL, f"styreneloop{oppos + r}skip", oploc))
            n = lexed[n].pair + 1 - r
        elif operation == "macro":
            n += 1
            expect(lexed[n], TOKEN_WORD)
            name = lexed[n].value
            n += 1
            expect(lexed[n], TOKEN_OCURLY)
            body = parse(lexed[n+1:lexed[n].pair-r], r+n+1, last_loop)
            n = lexed[n].pair - r + 1
            if name in macros.keys():
                error_loc(oploc, "macro with such name already exists")
            if name in sections:
                error_loc(oploc, "section with such name already exists")
            macros[name] = body
        elif operation == "section":
            n += 1
            expect(lexed[n], TOKEN_WORD)
            name = lexed[n].value
            n += 1
            expect(lexed[n], TOKEN_OCURLY)
            body = parse(lexed[n+1:lexed[n].pair-r], r+n+1, last_loop)
            n = lexed[n].pair - r + 1
            if name in macros.keys():
                error_loc(oploc, "macro with such name already exists")
            if name in sections:
                error_loc(oploc, "section with such name already exists")
            prg.append(Op(OP_JUMP, f"styrenesection{name}end", oploc))
            prg.append(Op(OP_LABEL, f"styrenesection{name}start", oploc))
            prg += body
            prg.append(Op(OP_LABEL, f"styrenesection{name}end", oploc))
            sections.add(name)
        else:
            params = []
            n += 1
            while lexed[n].type != TOKEN_SEMICOLON:
                params.append(lexed[n])
                expect(lexed[n], TOKEN_WORD + TOKEN_NUMBER + TOKEN_REFNUMBER)
                n += 1
                if n >= len(lexed):
                    error_loc(oploc, "expected semicolon, got EOF. missing semicolon?")
            n += 1

            if operation.lower() == "call":
                # call either macro (inline it) or section (go to it)
                check_params(operation.lower(), oploc, params, [TOKEN_WORD])
                if params[0].value in macros.keys():
                    prg += macros[params[0].value]
                elif params[0].value in sections:
                    prg.append(Op(OP_JUMP, f"styrenesection{params[0].value}start", oploc))
                else:
                    error_loc(params[0].loc, "no such macro or section")

            elif operation.lower() == "break":
                check_params(operation.lower(), oploc, params, [])
                if last_loop == -1:
                    error_loc(oploc, "break outside loop")
                prg.append(Op(OP_JUMP, f"styreneloop{last_loop}end", oploc))

            elif operation.lower() == "continue":
                check_params(operation.lower(), oploc, params, [])
                if last_loop == -1:
                    error_loc(oploc, "continue outside loop")
                prg.append(Op(OP_JUMP, f"styreneloop{last_loop}", oploc))

            elif operation.lower() == "copy":
                check_params(operation.lower(), oploc, params, [TOKEN_WORD + TOKEN_NUMBER + TOKEN_REFNUMBER, TOKEN_WORD + TOKEN_NUMBER + TOKEN_REFNUMBER])
                f, t = map(lambda x: x, params)
                if f.type == TOKEN_WORD:
                    if f.value != "inbox":
                        error_loc(f.loc, "expected `inbox`")
                    prg.append(Op(OP_INBOX, None, oploc))
                else:
                    prg.append(Op(OP_COPYFROM, f, oploc))
                if t.type == TOKEN_WORD:
                    if t.value != "outbox":
                        error_loc(t.loc, "expected `outbox`")
                    prg.append(Op(OP_OUTBOX, None, oploc))
                else:
                    prg.append(Op(OP_COPYTO, t, oploc))

            # base game low-level instructions
            elif operation.lower() == "inbox":
                check_params(operation.lower(), oploc, params, [])
                prg.append(Op(OP_INBOX, None, oploc))
            elif operation.lower() == "outbox":
                check_params(operation.lower(), oploc, params, [])
                prg.append(Op(OP_OUTBOX, None, oploc))

            elif operation.lower() == "add":
                check_params(operation.lower(), oploc, params, [TOKEN_NUMBER + TOKEN_REFNUMBER])
                prg.append(Op(OP_ADD, params[0].value, oploc))
            elif operation.lower() == "sub":
                check_params(operation.lower(), oploc, params, [TOKEN_NUMBER + TOKEN_REFNUMBER])
                prg.append(Op(OP_SUB, params[0].value, oploc))

            elif operation.lower() == "bump+":
                check_params(operation.lower(), oploc, params, [TOKEN_NUMBER + TOKEN_REFNUMBER])
                prg.append(Op(OP_BUMPA, params[0].value, oploc))
            elif operation.lower() == "bump-":
                check_params(operation.lower(), oploc, params, [TOKEN_NUMBER + TOKEN_REFNUMBER])
                prg.append(Op(OP_BUMPS, params[0].value, oploc))

            elif operation.lower() == "copyfrom":
                check_params(operation.lower(), oploc, params, [TOKEN_NUMBER + TOKEN_REFNUMBER])
                prg.append(Op(OP_COPYFROM, params[0].value, oploc))
            elif operation.lower() == "copyto":
                check_params(operation.lower(), oploc, params, [TOKEN_NUMBER + TOKEN_REFNUMBER])
                prg.append(Op(OP_COPYTO, params[0].value, oploc))

            elif operation.lower() == "label":
                check_params(operation.lower(), oploc, params, [TOKEN_WORD], True)
                for i in params:
                    if i.value.startswith("styrene"):
                        error_loc(i.loc, "for internal reasons label name can not start from styrene")
                    prg.append(Op(OP_LABEL, i.value, oploc))

            elif operation.lower() == "jump":
                check_params(operation.lower(), oploc, params, [TOKEN_WORD])
                if params[0].value.startswith("styrene"):
                    error_loc(i.loc, "for internal reasons you cant jump to labels starting with styrene")
                prg.append(Op(OP_JUMP, params[0].value, oploc))
            elif operation.lower() == "jumpz":
                check_params(operation.lower(), oploc, params, [TOKEN_WORD])
                prg.append(Op(OP_JUMPZ, params[0].value, oploc))
            elif operation.lower() == "jumpn":
                check_params(operation.lower(), oploc, params, [TOKEN_WORD])
                prg.append(Op(OP_JUMPN, params[0].value, oploc))

            else:
                error_loc(oploc, f"unknown operation {operation.lower()}")

    return prg

def fix_label_name(label_name):
    res = ""
    a = {
        "_": "u",
        "+": "p",
        "-": "m",
        ":": "c",
        "/": "s",
        "!": "x",
        "?": "q",
    }
    for i in label_name:
        if i in a.keys(): res += a[i]
        else: res += i
    return res

def compute_size(msg):
    pad = 2000, 3000
    kerning = 3000
    size_func = lambda x: 200000/x if x else 0
    size = size_func(len(msg))

    return pad, kerning, size

def break_comment(comment):
    words = comment.split()
    max_len = 5
    res = []
    for i in words:
        if not res: res.append("")
        if len(res[-1]) < max_len:
            res[-1] += i + " "
        else:
            res.append(i)
    resres = []
    for i in res:
        if len(i) // max_len > 1:
            for j in range(int(len(i) // max_len)):
                resres.append(j)
            resres.append(i[int(len(i)//max_len):])
        else:
            resres.append(i)
    return resres

def construct_program(prg, filename, comments, c):
    output = f"-- HUMAN RESOURCE MACHINE PROGRAM --\n" + (f"-- acetone program: {filename}; {len(prg)} instructions compiled\n" if comments else "") + "\n"
    if c: output += "    COMMENT 0\n"
    for i in prg:
        if comments: output += f"    -- {i.op}{' ' + str(i.operand) if i.operand else ''}: {i.loc}\n"
        if i.op == OP_LABEL:
            label_name = fix_label_name(i.operand)
            output += label_name + ":\n"
        else: output += "    " + i.op_str() + (str(i.operand) if i.operand is not None else "") + "\n"
    
    output += "\n"
    if c:
        output += f"DEFINE COMMENT 0\n"
        comment = draw_comment("acetone", 25000)
        comment += draw_bezier_curve((2000, 40000), (65535-2000, 40000), (lerp(2000, 65535-2000, 0.5), 60000))
        output += f"{encode_drawing(comment)};\n"
        output += "\n"

    return output

def print_usage(prg):
    print(f"usage: {prg} <filename.chco>")

def argparse(args):
    program = args.pop(0)
    if not args:
        print_usage(program)
        error("not enough args")
    filename = None
    do_args = True
    comments = False
    static = True
    comment = True
    copy = True
    n = 0
    for i in args:
        if do_args and i == "--":
            do_args = False
        elif do_args and i == "--debug":
            comments = True
        elif do_args and i == "--dont-copy":
            copy = False
        elif do_args and i == "--no-static":
            static = False
        elif do_args and i == "--no-comment":
            comment = False
        else:
            if n == 0: filename = i
            else:
                error("too many positional args")
    return filename, comments, copy, static, comment

def print_braces(lexed):
    print("".join(map(lambda x: f'{x.value}{lexed[x.pair].value} ', filter(lambda x: x.value == "{", lexed))))
    for i in lexed:
        if i.type in TOKEN_OCURLY:
            print(i)
            print("pair:", lexed[i.pair])

def dups(labels):
    seen = []
    for i in labels:
        if i in seen: return i
        seen.append(i)

def dupi(labels):
    seen = []
    for k, i in enumerate(labels):
        if i in seen: return k
        seen.append(i)

def static_check(prg):
    labels = list(map(lambda x: x.operand, filter(lambda x: x.op == OP_LABEL, prg)))
    labellocs = list(map(lambda x: x.loc, filter(lambda x: x.op == OP_LABEL, prg)))

    if dups(labels) is not None:
        error_loc(labellocs[dupi(labels)], f"duplicate label `{dups(labels)}`")

    for i in prg:
        if i.op in OP_JUMP + OP_JUMPN + OP_JUMPZ and i.operand not in labels:
            error_loc(i.loc, f"no such label as `{i.operand}`")

if __name__ == "__main__":
    print("styrene (acetone compiler) v1.0")
    filename, comments, copy, static, comment = argparse(sys.argv)

    src = open(filename).read()
    lexed = lex(src, filename)
    lexed = crossreference(lexed)
    prg = parse(lexed)
    if static: static_check(prg)
    prg = construct_program(prg, filename, comments, comment)
    print(prg)
    if copy: pyclip.copy(prg)
