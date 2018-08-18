import unittest

from montague.parsing import (
    AndNode, IteratorWithMemory, OrNode, VarNode, parse_formula, tokenize,
)


class IteratorWithMemoryTest(unittest.TestCase):
    def test_next_and_push(self):
        L = [1, 2, 3]
        it = IteratorWithMemory(iter(L))
        self.assertEqual(1, next(it))
        it.push(7)
        self.assertEqual(7, next(it))
        self.assertEqual(2, next(it))


class TokenizeTest(unittest.TestCase):
    def test_tokenize_symbol(self):
        tz = tokenize('a')
        tkn = next(tz)
        self.assertEqual(tkn.typ, 'SYMBOL')
        self.assertEqual(tkn.value, 'a')
        self.assertEqual(tkn.line, 1)
        self.assertEqual(tkn.column, 0)

        with self.assertRaises(StopIteration):
            next(tz)

    def test_tokenize_multiple_symbols(self):
        tokens = list(tokenize("a' b0 cccc"))
        self.assertEqual(len(tokens), 3)

        self.assertEqual(tokens[0].typ, 'SYMBOL')
        self.assertEqual(tokens[0].value, "a'")
        self.assertEqual(tokens[0].line, 1)
        self.assertEqual(tokens[0].column, 0)

        self.assertEqual(tokens[1].typ, 'SYMBOL')
        self.assertEqual(tokens[1].value, 'b0')
        self.assertEqual(tokens[1].line, 1)
        self.assertEqual(tokens[1].column, 3)

        self.assertEqual(tokens[2].typ, 'SYMBOL')
        self.assertEqual(tokens[2].value, 'cccc')
        self.assertEqual(tokens[2].line, 1)
        self.assertEqual(tokens[2].column, 6)

    def test_tokenize_conjunction(self):
        tokens = list(tokenize('a&b'))
        self.assertEqual(len(tokens), 3)

        self.assertEqual(tokens[0].typ, 'SYMBOL')
        self.assertEqual(tokens[0].value, 'a')
        self.assertEqual(tokens[1].typ, 'AND')
        self.assertEqual(tokens[1].value, '&')
        self.assertEqual(tokens[2].typ, 'SYMBOL')
        self.assertEqual(tokens[2].value, 'b')

    def test_tokenize_disjunction(self):
        tokens = list(tokenize('a|b'))
        self.assertEqual(len(tokens), 3)

        self.assertEqual(tokens[0].typ, 'SYMBOL')
        self.assertEqual(tokens[0].value, 'a')
        self.assertEqual(tokens[1].typ, 'OR')
        self.assertEqual(tokens[1].value, '|')
        self.assertEqual(tokens[2].typ, 'SYMBOL')
        self.assertEqual(tokens[2].value, 'b')


class ParseTest(unittest.TestCase):
    def test_parsing_symbol(self):
        tree = parse_formula('a')
        self.assertIsInstance(tree, VarNode)
        self.assertEqual(tree.value, 'a')

    def test_parsing_another_symbol(self):
        tree = parse_formula("s8DVY_BUvybJH-VDNS'JhjS")
        self.assertIsInstance(tree, VarNode)
        self.assertEqual(tree.value, "s8DVY_BUvybJH-VDNS'JhjS")

    def test_parsing_conjunction(self):
        tree = parse_formula("a & a'")
        self.assertIsInstance(tree, AndNode)
        left = tree.left
        self.assertIsInstance(left, VarNode)
        self.assertEqual(left.value, 'a')
        right = tree.right
        self.assertIsInstance(right, VarNode)
        self.assertEqual(right.value, "a'")

    def test_parsing_disjunction(self):
        tree = parse_formula("b | b0")
        self.assertIsInstance(tree, OrNode)
        left = tree.left
        self.assertIsInstance(left, VarNode)
        self.assertEqual(left.value, 'b')
        right = tree.right
        self.assertIsInstance(right, VarNode)
        self.assertEqual(right.value, "b0")

    def test_parsing_precedence(self):
        tree = parse_formula('x & y | z')
        self.assertIsInstance(tree, OrNode)
        left = tree.left
        self.assertIsInstance(left, AndNode)
        self.assertEqual(left.left.value, 'x')
        self.assertEqual(left.right.value, 'y')
        right = tree.right
        self.assertIsInstance(right, VarNode)
        self.assertEqual(right.value, 'z')