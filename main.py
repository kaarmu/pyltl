"""

Core LTL formulas
- true
- prop
- and
- not
- next
- union


x = prop()
y = prop()

n = NOT()
u = UNION()

:: FORM -> FORM -> FORM
subform = NOT(UNION(FORM, NOT(FORM)))



formula = n(u(x, not(y)))

NU(P1)(NP2)

{2|!1}

"""

from inspect import isclass
from typing import Type
from abc import ABC, abstractmethod

class Formula(ABC):

    @abstractmethod
    def __init__(self, *_):
        pass

    @abstractmethod
    def __call__(self, word: str) -> bool:
        pass

    @property
    @abstractmethod
    def symbol(self):
        pass

    @property
    @abstractmethod
    def optype(self):
        pass

class Composition(Formula):

    @property
    @abstractmethod
    def comp(self):
        pass

    def __call__(self, word: str):
        return self.comp(word)

class Unary(Formula):
    optype = 'unary'

    def __init__(self, x: Formula):
        self.hooks = (x,)

class Binary(Formula):
    optype = 'binary'

    def __init__(self, x: Formula, y: Formula):
        self.hooks = (x, y)

class Consumer(Formula):
    optype = 'consumer'

    def __init__(self, x: str):
        self.x = x

class Terminal(Formula):
    optype = 'terminal'

    def __init__(self):
        pass

# CORE STUFF
# true
# prop
# and
# not
# next
# until

class PROP(Consumer):
    symbol = 'P'

    def __call__(self, word: str):
        return word[0] == self.x

class TRUE(Terminal):
    symbol = 'T'

    def __call__(self, word: str):
        return True

class AND(Binary):
    symbol = 'A'

    def __call__(self, word: str):
        return self.hooks[0](word) and self.hooks[1](word)

class NOT(Unary):
    symbol = 'N'

    def __call__(self, word: str):
        return not self.hooks[0](word)

class NEXT(Unary):
    symbol = 'X'

    def __call__(self, word: str):
        return self.hooks[0](word[1:])

class UNTIL(Binary):
    symbol = 'U'

    def __call__(self, word: str):
        i, l = 0, len(word)
        while not self.hooks[1](word[i:]):
            if not self.hooks[0](word[i:]):
                return False
            if (i := i+1) == l:
                return False
        return True


# COMPOSITIONS

class OR(Binary, Composition):
    # Composition: NUN*N*
    symbol = 'O'

    def comp(self):
        return NOT(AND(NOT(self.hooks[0]), NOT(self.hooks[1])))

class IMPLIES(Binary, Composition):
    # Composition: ON**
    symbol = 'I'

    def comp(self):
        return OR(NOT(self.hooks[0]), self.hooks[1])

class EVENTUALLY(Unary, Composition):
    # Composition: UT*
    symbol = 'F'

    def comp(self):
        return UNTIL(TRUE(), self.hooks[0])

class ALWAYS(Unary, Composition):
    # Composition: NFN*
    symbol = 'G'

    def comp(self):
        return NOT(EVENTUALLY(NOT(self.hooks[0])))

#
# Parsing
#

ALLOPS = { f.symbol: f for f in [
        # CORE FORMULAS
        PROP, TRUE, AND, NOT, NEXT, UNTIL,
        # COMPOSITIONS
        OR, IMPLIES, EVENTUALLY, ALWAYS,
    ] }

def findMatchingPair(pair: str, tokens: str, start: int = 0):
    assert tokens[start] == pair[0]

    level = 0
    for i, token in enumerate(tokens[start:]):
        if token == pair[0]:
            level += 1
        elif token == pair[1]:
            level -= 1
        if level == 0:
            break
    else:
        raise Exception("Could not find a matching brace to the following"
                        f" string.\n{''.join(tokens)}")
    return i

def parseBraces(pair: str, tokens: str) -> tuple[str, str]:
    i = findMatchingPair(pair, tokens)
    return tokens[1:i], tokens[i+1:]

def parse(tokens: str, ops: dict[str, Type[Formula]] = ALLOPS
         ) -> tuple[Formula, str]:

    print(tokens[0])

    # 1. Remove whitespace
    while tokens[0] == ' ':
        tokens = tokens[1:]

    # 2. Evalute braces
    if tokens[0] == '(':
        content, tokens = parseBraces('()', tokens)
        tmp = parse(content, ops)

        assert not tmp[1]
        return tmp[0], tokens

    # 3. Extract operator
    try:
        op = ops[tokens[0]]
        optype = op.optype
    except KeyError as e:
        raise Exception(f"Operator '{e.args[0]}' is not known")

    # 4. Consumer operator
    if optype == 'consumer':
        return op(tokens[1]), tokens[2:]

    # 5. Unary operator
    if optype == 'unary':
        formula, tokens = parse(tokens[1:], ops)
        return op(formula), tokens

    # . Binary operator
    if optype == 'binary':
        lhs, tokens = parse(tokens[1:], ops)
        rhs, tokens = parse(tokens)
        return op(lhs, rhs), tokens

    if optype == 'terminal':
        return op(), tokens[1:]


    raise Exception("Could not parse")
