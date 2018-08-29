import json
import os
import unittest

from montague.formula import (
    AllNode, AndNode, CallNode, ExistsNode, IfNode, LambdaNode, OrNode,
    TypeNode, VarNode, parse_formula, parse_type, unparse_formula, TYPE_ENTITY,
    TYPE_EVENT, TYPE_TRUTH_VALUE,
)
from montague.translator import (
    LexiconEntry, TranslationError, can_combine, combine, load_lexicon,
    replace_variable, simplify_formula, translate_sentence,
)


TYPE_ET = TypeNode(TYPE_ENTITY, TYPE_TRUTH_VALUE)


test_lexicon = {
  "bad": LexiconEntry(
      LambdaNode('x', CallNode(VarNode('Bad'), VarNode('x'))),
      TYPE_ET
  ),
  "is": LexiconEntry(
      LambdaNode('P', VarNode('P')),
      TypeNode(TYPE_ET, TYPE_ET)
  ),
  "good": LexiconEntry(
      LambdaNode('x', CallNode(VarNode('Good'), VarNode('x'))),
      TYPE_ET
  ),
  "every": LexiconEntry(
      LambdaNode('P',
          LambdaNode('Q',
              AllNode('x',
                  IfNode(
                      CallNode(VarNode('P'), VarNode('x')),
                      CallNode(VarNode('Q'), VarNode('x'))
                  )
              )
          )
      ),
      TypeNode(
          TYPE_ET,
          TypeNode(TYPE_ET, TYPE_TRUTH_VALUE)
      )
  ),
  "child": LexiconEntry(
      LambdaNode('x', CallNode(VarNode('Child'), VarNode('x'))),
      TYPE_ET
  ),
  "John": LexiconEntry(VarNode('j'), TYPE_ENTITY),
}


class TranslatorTest(unittest.TestCase):
    def test_is_good(self):
        tree = translate_sentence('is good', test_lexicon)
        self.assertEqual(
            tree.denotation,
            LambdaNode(
                'x',
                CallNode(VarNode('Good'), VarNode('x'))
            ),
        )
        self.assertEqual(tree.type, TYPE_ET)

    def test_john_is_good(self):
        tree = translate_sentence('John is good', test_lexicon)
        self.assertEqual(
            tree.denotation,
            CallNode(VarNode('Good'), VarNode('j'))
        )
        self.assertEqual(tree.type, TYPE_TRUTH_VALUE)

    def test_john_is_bad(self):
        tree = translate_sentence('John is bad', test_lexicon)
        self.assertEqual(
            tree.denotation,
            CallNode(VarNode('Bad'), VarNode('j'))
        )
        self.assertEqual(tree.type, TYPE_TRUTH_VALUE)

    def test_every_child_is_good(self):
        tree = translate_sentence('every child is good', test_lexicon)
        self.assertTupleEqual(
            tree.denotation,
            AllNode(
                'x',
                IfNode(
                    CallNode(VarNode('Child'), VarNode('x')),
                    CallNode(VarNode('Good'), VarNode('x'))
                )
            )
        )
        self.assertEqual(tree.type, TYPE_TRUTH_VALUE)

    def test_translate_invalid_sentence(self):
        with self.assertRaises(TranslationError):
            translate_sentence('every John is good', test_lexicon)

    def test_translate_unknown_word(self):
        with self.assertRaises(TranslationError) as cm:
            translate_sentence('John is whorlious', test_lexicon)
        self.assertIn('whorlious', cm.exception.args[0])


class CombinerTest(unittest.TestCase):
    pred = LexiconEntry(
        parse_formula('Lx.P(x)'),
        parse_type('<e, t>')
    )
    entity = LexiconEntry(VarNode('me'), TYPE_ENTITY)

    def test_saturate_predicate(self):
        self.assertTrue(can_combine(self.pred, self.entity))
        saturated = combine(self.pred, self.entity)
        self.assertEqual(saturated.type, TYPE_TRUTH_VALUE)
        self.assertEqual(
            saturated.denotation,
            CallNode(self.pred.denotation, self.entity.denotation)
        )

    def test_combine_every_child(self):
        every = test_lexicon['every']
        child = test_lexicon['child']
        every_child = combine(every, child)
        self.assertEqual(every_child.type, TypeNode(TYPE_ET, TYPE_TRUTH_VALUE))
        self.assertEqual(
            every_child.denotation,
            CallNode(every.denotation, child.denotation)
        )

    def test_can_combine_is_good(self):
        self.assertTrue(can_combine(test_lexicon['is'], test_lexicon['good']))

    def test_mismatched_types(self):
        self.assertFalse(can_combine(self.pred, self.pred))
        self.assertFalse(can_combine(self.entity, self.pred))
        self.assertFalse(can_combine(self.entity, self.entity))


class ReplacerTest(unittest.TestCase):
    def test_simple_replace_variable(self):
        replaced = replace_variable(VarNode('x'), 'x', VarNode('y'))
        self.assertEqual(replaced, VarNode('y'))

    def test_replace_variable_in_and_or(self):
        tree = AndNode(OrNode(VarNode('x'), VarNode('y')), VarNode('z'))
        replaced = replace_variable(tree, 'x', VarNode('x\''))
        self.assertEqual(replaced,
            AndNode(
                OrNode(VarNode('x\''), VarNode('y')),
                VarNode('z')
            )
        )

    def test_replace_predicate(self):
        tree = CallNode(VarNode('P'), VarNode('x'))
        replaced = replace_variable(tree, 'P', VarNode('Good'))
        self.assertEqual(replaced, CallNode(VarNode('Good'), VarNode('x')))

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
        replaced = replace_variable(tree, 'b', VarNode('bbb'))
        self.assertEqual(replaced, AllNode('x',
            OrNode(
                AndNode(
                    AllNode('b', VarNode('b')),
                    ExistsNode('b', VarNode('b')),
                ),
                ExistsNode('y', VarNode('bbb'))
            )
        ))


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
        tree = replace_variable(tree, 'x', VarNode('j'))
        self.assertEqual(tree, CallNode(
            CallNode(
                CallNode(
                    VarNode('BFP'),
                    VarNode('j')
                ),
                LambdaNode('x', VarNode('x'))
            ),
            AndNode(VarNode('j'), VarNode('y'))
        ))


class SimplifierTest(unittest.TestCase):
    def test_simplify_call(self):
        tree = simplify_formula(CallNode(
            LambdaNode('x', VarNode('x')),
            VarNode('j')
        ))
        self.assertEqual(tree, VarNode('j'))

    def test_simplify_nested_call(self):
        # (Lx.Ly.x & y)(a)(b) -> a & b
        tree = simplify_formula(
            CallNode(
                CallNode(
                    LambdaNode('x',
                        LambdaNode('y',
                            AndNode(VarNode('x'), VarNode('y'))
                        )
                    ),
                    VarNode('a')
                ),
                VarNode('b')
            )
        )
        self.assertEqual(tree, AndNode(VarNode('a'), VarNode('b')))

    def test_simplify_call_with_lambda_arg(self):
        # (LP.P(x))(Lx.x | a) -> x | a
        tree = simplify_formula(
            CallNode(
                LambdaNode(
                    'P',
                    CallNode(VarNode('P'), VarNode('x'))
                ),
                LambdaNode(
                    'x',
                    OrNode(VarNode('x'), VarNode('a'))
                )
            )
        )
        self.assertEqual(tree, OrNode(VarNode('x'), VarNode('a')))

    def test_simplify_super_nested_call(self):
        # (LP.P(a, b))(Lx.Ly.x & y) -> a & b
        tree = simplify_formula(
            CallNode(
                LambdaNode(
                    'P',
                    CallNode(CallNode(VarNode('P'), VarNode('a')), VarNode('b'))
                ),
                LambdaNode(
                    'x',
                    LambdaNode(
                        'y',
                        AndNode(VarNode('x'), VarNode('y'))
                    )
                )
            )
        )
        self.assertEqual(tree, AndNode(VarNode('a'), VarNode('b')))

    def test_simplify_every_child(self):
        # (LP.LQ.Ax.P(x) -> Q(x))(Lx.Child(x)) -> LQ.Ax.Child(x) -> Q(x)
        tree = simplify_formula(
            CallNode(
                test_lexicon['every'].denotation,
                test_lexicon['child'].denotation
            )
        )
        self.assertTupleEqual(
            tree,
            LambdaNode(
                'Q',
                AllNode(
                    'x',
                    IfNode(
                        CallNode(VarNode('Child'), VarNode('x')),
                        CallNode(VarNode('Q'), VarNode('x'))
                    )
                )
            )
        )


class LexiconLoaderTest(unittest.TestCase):
    def test_load_lexicon(self):
        lexicon = load_lexicon({
            'John': {
                'd': 'j',
                't': 'e',
            },
            'good': {
                'd': 'Lx.Good(x)',
                't': 'et',
            },
        })
        self.assertDictEqual(lexicon, {
            'John': LexiconEntry(parse_formula('j'), parse_type('e')),
            'good': LexiconEntry(parse_formula('Lx.Good(x)'), parse_type('et')),
        })
