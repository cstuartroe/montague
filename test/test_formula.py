import unittest

from montague.formula import (
    AllNode, AndNode, CallNode, ExistsNode, IfNode, LambdaNode, NotNode, OrNode,
    TypeNode, VarNode, parse_formula, parse_type, TYPE_ENTITY, TYPE_EVENT,
    TYPE_TRUTH_VALUE, TYPE_WORLD,
)

from lark.exceptions import LarkError


class FormulaParseTest(unittest.TestCase):
    def test_parsing_symbol(self):
        self.assertTupleEqual(parse_formula('a'), VarNode('a'))

    def test_parsing_long_symbol(self):
        self.assertTupleEqual(
            parse_formula("s8DVY_BUvybJH-VDNS'JhjS"),
            VarNode('s8DVY_BUvybJH-VDNS\'JhjS')
        )

    def test_parsing_conjunction(self):
        self.assertTupleEqual(
            parse_formula("a & a'"),
            AndNode(VarNode('a'), VarNode('a\''))
        )

    def test_parsing_multiple_conjunction(self):
        self.assertTupleEqual(
            parse_formula('a & b & c'),
            AndNode(
                VarNode('a'),
                AndNode(
                    VarNode('b'),
                    VarNode('c')
                )
            )
        )

    def test_parsing_disjunction(self):
        self.assertTupleEqual(
            parse_formula('b | b0'),
            OrNode(VarNode('b'), VarNode('b0'))
        )

    def test_parsing_multi_disjunction(self):
        self.assertTupleEqual(
            parse_formula('a | b | c'),
            OrNode(
                VarNode('a'),
                OrNode(
                    VarNode('b'),
                    VarNode('c')
                )
            )
        )

    def test_parsing_implication(self):
        self.assertTupleEqual(
            parse_formula('a -> b'),
            IfNode(VarNode('a'), VarNode('b'))
        )

    def test_parsing_multi_implication(self):
        self.assertTupleEqual(
            parse_formula('a -> b -> c'),
            IfNode(
                VarNode('a'),
                IfNode(
                    VarNode('b'),
                    VarNode('c')
                )
            )
        )

    def test_parsing_negation(self):
        self.assertEqual(parse_formula('~a'), NotNode(VarNode('a')))

    def test_parsing_negation_precedence(self):
        self.assertEqual(
            parse_formula('~a | b'),
            OrNode(NotNode(VarNode('a')), VarNode('b'))
        )

    def test_parsing_negation_precedence2(self):
        self.assertEqual(
            parse_formula('~[a | b]'),
            NotNode(OrNode(VarNode('a'), VarNode('b')))
        )

    def test_parsing_precedence(self):
        self.assertTupleEqual(
            parse_formula('x & y | z -> m'),
            IfNode(
                OrNode(
                    AndNode(VarNode('x'), VarNode('y')),
                    VarNode('z')
                ),
                VarNode('m')
            )
        )

    def test_parsing_precedence2(self):
        self.assertTupleEqual(
            parse_formula('x | y -> m & z'),
            IfNode(
                OrNode(
                    VarNode('x'),
                    VarNode('y'),
                ),
                AndNode(
                    VarNode('m'),
                    VarNode('z')
                )
            )
        )

    def test_parsing_brackets(self):
        self.assertTupleEqual(
            parse_formula('[x | y] & z'),
            AndNode(
                OrNode(VarNode('x'), VarNode('y')),
                VarNode('z')
            )
        )

    def test_parsing_lambda(self):
        self.assertTupleEqual(
            parse_formula('Lx.Ly.[x & y]'),
            LambdaNode(
                'x',
                LambdaNode(
                    'y',
                    AndNode(VarNode('x'), VarNode('y'))
                )
            )
        )

    def test_parsing_lambda2(self):
        self.assertEqual(
            parse_formula('L x.L y.[x & y]'),
            LambdaNode(
                'x',
                LambdaNode(
                    'y',
                    AndNode(VarNode('x'), VarNode('y'))
                )
            )
        )

    def test_parsing_call(self):
        self.assertTupleEqual(
            parse_formula('Happy(x)'),
            CallNode(VarNode('Happy'), VarNode('x'))
        )

    def test_parsing_call_with_several_args(self):
        self.assertTupleEqual(
            parse_formula('Between(x, y & z, [Capital(france)])'),
            CallNode(
                CallNode(
                    CallNode(
                        VarNode('Between'),
                        VarNode('x')
                    ),
                    AndNode(VarNode('y'), VarNode('z')),
                ),
                CallNode(VarNode('Capital'), VarNode('france')),
            )
        )

    def test_parsing_call_with_lambda(self):
        self.assertTupleEqual(
            parse_formula('(Lx.x)(j)'),
            CallNode(
                LambdaNode('x', VarNode('x')),
                VarNode('j')
            )
        )

    def test_parsing_call_with_multiple_lambdas(self):
        self.assertTupleEqual(
            parse_formula('((Lx.Ly.x & y) (a)) (b)'),
            CallNode(
                CallNode(
                    LambdaNode(
                        'x',
                        LambdaNode('y', AndNode(VarNode('x'), VarNode('y')))
                    ),
                    VarNode('a')
                ),
                VarNode('b')
            )
        )

    def test_parsing_forall(self):
        self.assertTupleEqual(
            parse_formula('Ax.x & y'),
            AllNode('x', AndNode(VarNode('x'), VarNode('y')))
        )

    def test_parsing_forall2(self):
        self.assertTupleEqual(
            parse_formula('A x.x & y'),
            AllNode('x', AndNode(VarNode('x'), VarNode('y')))
        )

    def test_parsing_exists(self):
        self.assertTupleEqual(
            parse_formula('Ex.x | y'),
            ExistsNode('x', OrNode(VarNode('x'), VarNode('y')))
        )

    def test_parsing_exists2(self):
        self.assertTupleEqual(
            parse_formula('E x.x | y'),
            ExistsNode('x', OrNode(VarNode('x'), VarNode('y')))
        )


class FormulaParseErrorTest(unittest.TestCase):
    def test_missing_operand(self):
        with self.assertRaises(LarkError):
            parse_formula('a | ')
        with self.assertRaises(LarkError):
            parse_formula('b & ')
        with self.assertRaises(LarkError):
            parse_formula('| a')
        with self.assertRaises(LarkError):
            parse_formula('& b')

    def test_parsing_hanging_bracket(self):
        with self.assertRaises(LarkError):
            parse_formula('[x | y')

    def test_lambda_missing_body(self):
        with self.assertRaises(LarkError):
            parse_formula('Lx.')

    def test_unknown_token(self):
        with self.assertRaises(LarkError):
            parse_formula('Lx.x?')

    def test_empty_string(self):
        with self.assertRaises(LarkError):
            parse_formula('')


class TypeParseTest(unittest.TestCase):
    def test_parsing_atomic_types(self):
        self.assertEqual(parse_type('e'), TYPE_ENTITY)
        self.assertEqual(parse_type('t'), TYPE_TRUTH_VALUE)
        self.assertEqual(parse_type('v'), TYPE_EVENT)
        self.assertEqual(parse_type('s'), TYPE_WORLD)

    def test_parsing_compound_type(self):
        self.assertTupleEqual(
            parse_type('<e, t>'),
            TypeNode(TYPE_ENTITY, TYPE_TRUTH_VALUE)
        )

    def test_parsing_abbreviated_compound_types(self):
        self.assertTupleEqual(
            parse_type('et'),
            TypeNode(TYPE_ENTITY, TYPE_TRUTH_VALUE)
        )
        self.assertTupleEqual(
            parse_type('vt'),
            TypeNode(TYPE_EVENT, TYPE_TRUTH_VALUE)
        )

    def test_parsing_big_compound_type(self):
        self.assertTupleEqual(
            parse_type('<<e, t>, <e, <s, t>>>'),
            TypeNode(
                TypeNode(TYPE_ENTITY, TYPE_TRUTH_VALUE),
                TypeNode(
                    TYPE_ENTITY,
                    TypeNode(TYPE_WORLD, TYPE_TRUTH_VALUE)
                )
            )
        )

    def test_parsing_big_compound_type_with_abbreviations(self):
        self.assertTupleEqual(
            parse_type('<et, <e, st>>'),
            TypeNode(
                TypeNode(TYPE_ENTITY, TYPE_TRUTH_VALUE),
                TypeNode(
                    TYPE_ENTITY,
                    TypeNode(TYPE_WORLD, TYPE_TRUTH_VALUE)
                )
            )
        )


class TypeParseErrorTest(unittest.TestCase):
    def test_missing_opening_bracket(self):
        with self.assertRaises(LarkError):
            parse_type('e, t>')

    def test_missing_closing_bracket(self):
        with self.assertRaises(LarkError):
            parse_type('<e, t')

    def test_trailing_input(self):
        with self.assertRaises(LarkError):
            parse_type('<e, t> e')

    def test_missing_comma(self):
        with self.assertRaises(LarkError):
            parse_type('<e t>')

    def test_missing_output_type(self):
        with self.assertRaises(LarkError):
            parse_type('<e>')

    def test_invalid_abbreviation(self):
        with self.assertRaises(LarkError):
            parse_type('evt')

    def test_invalid_letter(self):
        with self.assertRaises(LarkError):
            parse_type('b')

    def test_unknown_token(self):
        with self.assertRaises(LarkError):
            parse_type('e?')

    def test_empty_string(self):
        with self.assertRaises(LarkError):
            parse_type('')


class FormulaToStrTest(unittest.TestCase):
    def test_variable_to_str(self):
        self.assertEqual(str(VarNode('a')), 'a')

    def test_and_to_str(self):
        self.assertEqual(str(AndNode(VarNode('a'), VarNode('b'))), 'a & b')

    def test_or_to_str(self):
        self.assertEqual(str(OrNode(VarNode('a'), VarNode('b'))), 'a | b')

    def test_if_to_str(self):
        self.assertEqual(str(IfNode(VarNode('a'), VarNode('b'))), 'a -> b')

    def test_lambda_to_str(self):
        self.assertEqual(
            str(LambdaNode('x', AndNode(VarNode('a'), VarNode('x')))),
            'Lx.a & x'
        )

    def test_call_to_str(self):
        self.assertEqual(
            str(
                CallNode(
                    CallNode(VarNode('P'), AndNode(VarNode('a'), VarNode('b'))),
                    LambdaNode('x', VarNode('x'))
                )
            ),
            'P(a & b, Lx.x)'
        )

    def test_call_with_one_arg_to_str(self):
        self.assertEqual(str(CallNode(VarNode('P'), VarNode('x'))), 'P(x)')

    def test_forall_to_str(self):
        self.assertEqual(
            str(AllNode('x', CallNode(VarNode('P'), VarNode('x')))),
            'Ax.P(x)'
        )

    def test_exists_to_str(self):
        self.assertEqual(
            str(ExistsNode('x', CallNode(VarNode('P'), VarNode('x')))),
            'Ex.P(x)'
        )

    def test_not_to_str(self):
        self.assertEqual(
            str(NotNode(VarNode('x'))),
            '~x'
        )

    def test_not_with_expr_to_str(self):
        self.assertEqual(
            str(NotNode(OrNode(VarNode('x'), VarNode('y')))),
            '~[x | y]'
        )

    def test_nested_and_or_to_str(self):
        self.assertEqual(
            str(AndNode(OrNode(VarNode('a'), VarNode('b')), VarNode('c'))),
            '[a | b] & c'
        )

    def test_nested_and_or_to_str2(self):
        self.assertEqual(
            str(OrNode(AndNode(VarNode('a'), VarNode('b')), VarNode('c'))),
            'a & b | c'
        )

    def test_nested_exists_and_forall_to_str(self):
        self.assertEqual(
            str(
                AndNode(
                    AllNode('x', VarNode('x')),
                    ExistsNode('x', VarNode('x'))
                )
            ),
            '[Ax.x] & [Ex.x]'
        )

    def test_nested_lambdas_to_str(self):
        # This formula is semantically invalid but that doesn't matter.
        self.assertEqual(
            str(
                AndNode(
                    LambdaNode('x', VarNode('x')),
                    LambdaNode('y', VarNode('y'))
                )
            ),
            '[Lx.x] & [Ly.y]'
        )


class TypeToStrTest(unittest.TestCase):
    def test_entity_to_str(self):
        self.assertEqual(str(TYPE_ENTITY), 'e')

    def test_event_to_str(self):
        self.assertEqual(str(TYPE_EVENT), 'v')

    def test_truth_value_to_str(self):
        self.assertEqual(str(TYPE_TRUTH_VALUE), 't')

    def test_world_to_str(self):
        self.assertEqual(str(TYPE_WORLD), 's')

    def test_recursive_type_to_str(self):
        self.assertEqual(str(TypeNode(TYPE_ENTITY, TYPE_TRUTH_VALUE)), '<e, t>')

    def test_deeply_recursive_type_to_str(self):
        self.assertEqual(
            str(
                TypeNode(
                    TYPE_EVENT,
                    TypeNode(
                        TypeNode(TYPE_ENTITY, TYPE_TRUTH_VALUE),
                        TypeNode(TYPE_ENTITY, TYPE_TRUTH_VALUE)
                    )
                )
            ),
            '<v, <<e, t>, <e, t>>>'
        )

    def test_recursive_type_to_concise_str(self):
        typ = TypeNode(TYPE_ENTITY, TYPE_TRUTH_VALUE)
        self.assertEqual(typ.concise_str(), 'et')

    def test_deeply_recursive_type_to_concise_str(self):
        typ = TypeNode(
            TYPE_EVENT,
            TypeNode(
                TypeNode(
                    TYPE_ENTITY,
                    TYPE_TRUTH_VALUE
                ),
                TypeNode(
                    TYPE_ENTITY,
                    TYPE_TRUTH_VALUE
                )
            )
        )
        self.assertEqual(typ.concise_str(), '<v, <et, et>>')


class ReplacerTest(unittest.TestCase):
    def test_simple_replace_variable(self):
        self.assertTupleEqual(
            VarNode('x').replace_variable('x', VarNode('y')),
            VarNode('y')
        )

    def test_replace_variable_in_and_or(self):
        tree = AndNode(OrNode(VarNode('x'), VarNode('y')), VarNode('z'))
        self.assertTupleEqual(
            tree.replace_variable('x', VarNode("x'")),
            AndNode(OrNode(VarNode("x'"), VarNode('y')), VarNode('z'))
        )

    def test_replace_predicate(self):
        tree = CallNode(VarNode('P'), VarNode('x'))
        self.assertTupleEqual(
            tree.replace_variable('P', VarNode('Good')),
            CallNode(VarNode('Good'), VarNode('x'))
        )

    def test_replace_variable_in_quantifiers(self):
        tree = AllNode('x',
            OrNode(
                AndNode(
                    AllNode('b', VarNode('b')),
                    ExistsNode('b', VarNode('b')),
                ),
                ExistsNode('y', VarNode('b'))
            )
        )
        self.assertTupleEqual(
            tree.replace_variable('b', VarNode('bbb')),
            AllNode(
                'x',
                OrNode(
                    AndNode(
                        AllNode('b', VarNode('b')),
                        ExistsNode('b', VarNode('b')),
                    ),
                    ExistsNode('y', VarNode('bbb'))
                )
            )
        )


    def test_recursive_replace_variable(self):
        tree = CallNode(
            CallNode(
                CallNode(
                    VarNode('BFP'),
                    VarNode('x')
                ),
                LambdaNode('x', VarNode('x'))  # This should not be replaced.
            ),
            AndNode(VarNode('x'), VarNode('y'))
        )
        self.assertTupleEqual(
            tree.replace_variable('x', VarNode('j')),
            CallNode(
                CallNode(
                    CallNode(
                        VarNode('BFP'),
                        VarNode('j')
                    ),
                    LambdaNode('x', VarNode('x'))
                ),
                AndNode(VarNode('j'), VarNode('y'))
            )
        )
