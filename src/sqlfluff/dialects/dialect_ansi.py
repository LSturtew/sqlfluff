"""The core ANSI dialect.

This is the core SQL grammar. We'll probably extend this or make it pluggable
for other dialects. Here we encode the structure of the language.

There shouldn't be any underlying "machinery" here, that should all
be defined elsewhere.

A lot of the inspiration for this sql grammar is taken from the cockroach
labs full sql grammar. In particular their way for dividing up the expression
grammar. Check out their docs, they're awesome.
https://www.cockroachlabs.com/docs/stable/sql-grammar.html#select_stmt
"""

from ..parser import (BaseSegment, KeywordSegment, ReSegment, NamedSegment,
                      Sequence, GreedyUntil, StartsWith, ContainsOnly,
                      OneOf, Delimited, Bracketed, AnyNumberOf, Ref,
                      Anything, LambdaSegment)
from .base import Dialect


ansi_dialect = Dialect('ansi')


ansi_dialect.add(
    # NB The NonCode Segment is not really for matching, mostly just for use as a terminator
    _NonCodeSegment=LambdaSegment.make(lambda x: not x.is_code, is_code=False, name='non_code'),
    # Real segments
    SemicolonSegment=KeywordSegment.make(';', name="semicolon"),
    StartBracketSegment=KeywordSegment.make('(', name='start_bracket', type='start_bracket'),
    EndBracketSegment=KeywordSegment.make(')', name='end_bracket', type='end_bracket'),
    CommaSegment=KeywordSegment.make(',', name='comma'),
    DotSegment=KeywordSegment.make('.', name='dot', type='dot'),
    StarSegment=KeywordSegment.make('*', name='star'),
    TildeSegment=KeywordSegment.make('~', name='tilde'),
    PlusSegment=KeywordSegment.make('+', name='plus', type='binary_operator'),
    MinusSegment=KeywordSegment.make('-', name='minus', type='binary_operator'),
    DivideSegment=KeywordSegment.make('/', name='divide', type='binary_operator'),
    MultiplySegment=KeywordSegment.make('*', name='multiply', type='binary_operator'),
    EqualsSegment=KeywordSegment.make('=', name='equals', type='comparison_operator'),
    GreaterThanSegment=KeywordSegment.make('>', name='greater_than', type='comparison_operator'),
    LessThanSegment=KeywordSegment.make('<', name='less_than', type='comparison_operator'),
    GreaterThanOrEqualToSegment=KeywordSegment.make('>=', name='greater_than_equal_to', type='comparison_operator'),
    LessThanOrEqualToSegment=KeywordSegment.make('<=', name='less_than_equal_to', type='comparison_operator'),
    # The strange regex here it to make sure we don't accidentally match numeric literals
    NakedIdentifierSegment=ReSegment.make(r"[A-Z0-9_]*[A-Z][A-Z0-9_]*", name='identifier', type='naked_identifier'),
    FunctionNameSegment=ReSegment.make(r"[A-Z][A-Z0-9_]*", name='function_name', type='function_name'),
    QuotedIdentifierSegment=NamedSegment.make('double_quote', name='identifier', type='quoted_identifier'),
    QuotedLiteralSegment=NamedSegment.make('single_quote', name='literal', type='quoted_literal'),
    NumericLiteralSegment=NamedSegment.make('numeric_literal', name='literal', type='numeric_literal'),
    TrueSegment=KeywordSegment.make('true', name='true', type='boolean_literal'),
    FalseSegment=KeywordSegment.make('false', name='false', type='boolean_literal'),
    # We use a GRAMMAR here not a Segment. Otherwise we get an unecessary layer
    SingleIdentifierGrammar=OneOf(Ref('NakedIdentifierSegment'), Ref('QuotedIdentifierSegment')),
    BooleanLiteralGrammar=OneOf(Ref('TrueSegment'), Ref('FalseSegment')),
    # We specifically define a group of arithmetic operators to make it easier to override this
    # if some dialects have different available operators
    ArithmeticBinaryOperatorGrammar=OneOf(
        Ref('PlusSegment'), Ref('MinusSegment'), Ref('DivideSegment'), Ref('MultiplySegment')),
    BooleanBinaryOperatorGrammar=OneOf(
        Ref('AndKeywordSegment'), Ref('OrKeywordSegment')),
    ComparisonOperatorGrammar=OneOf(
        Ref('EqualsSegment'), Ref('GreaterThanSegment'), Ref('LessThanSegment'),
        Ref('GreaterThanOrEqualToSegment'), Ref('LessThanOrEqualToSegment')),
    AliasExpressionGrammar=Sequence(Ref('AsKeywordSegment'), Ref('SingleIdentifierGrammar')),
    # Keywords
    AsKeywordSegment=KeywordSegment.make('as'),
    FromKeywordSegment=KeywordSegment.make('from'),
    DistinctKeywordSegment=KeywordSegment.make('distinct'),
    AllKeywordSegment=KeywordSegment.make('all'),
    LimitKeywordSegment=KeywordSegment.make('limit'),
    OnKeywordSegment=KeywordSegment.make('on'),
    JoinKeywordSegment=KeywordSegment.make('join'),
    InnerKeywordSegment=KeywordSegment.make('inner'),
    LeftKeywordSegment=KeywordSegment.make('left'),
    CrossKeywordSegment=KeywordSegment.make('cross'),
    UsingKeywordSegment=KeywordSegment.make('using'),
    WhereKeywordSegment=KeywordSegment.make('where'),
    GroupKeywordSegment=KeywordSegment.make('group'),
    OrderKeywordSegment=KeywordSegment.make('order'),
    HavingKeywordSegment=KeywordSegment.make('having'),
    OverwriteKeywordSegment=KeywordSegment.make('overwrite'),
    ByKeywordSegment=KeywordSegment.make('by'),
    InKeywordSegment=KeywordSegment.make('in'),
    AndKeywordSegment=KeywordSegment.make('and', type='binary_operator'),
    OrKeywordSegment=KeywordSegment.make('or', type='binary_operator'),
    NotKeywordSegment=KeywordSegment.make('not'),
    AscKeywordSegment=KeywordSegment.make('asc'),
    DescKeywordSegment=KeywordSegment.make('desc'),
    ValueKeywordSegment=KeywordSegment.make('value'),
    ValuesKeywordSegment=KeywordSegment.make('values'),
    SelectKeywordSegment=KeywordSegment.make('select'),
    WithKeywordSegment=KeywordSegment.make('with'),
    InsertKeywordSegment=KeywordSegment.make('insert'),
    IntoKeywordSegment=KeywordSegment.make('into'),
    # Some more grammars:
    LiteralGrammar=OneOf(
        Ref('QuotedLiteralSegment'), Ref('NumericLiteralSegment'),
        Ref('BooleanLiteralGrammar'), Ref('QualifiedNumericLiteralSegment')
    ),
)


@ansi_dialect.segment()
class ColumnExpressionSegment(BaseSegment):
    """A reference to a column."""
    type = 'column_expression'
    match_grammar = OneOf(Ref('SingleIdentifierGrammar'), code_only=False)  # QuotedIdentifierSegment


@ansi_dialect.segment()
class ObjectReferenceSegment(BaseSegment):
    """A reference to an object."""
    type = 'object_reference'
    # match grammar (don't allow whitespace)
    match_grammar = Delimited(
        Ref('SingleIdentifierGrammar'),
        delimiter=Ref('DotSegment'),
        terminator=OneOf(Ref('_NonCodeSegment'), Ref('CommaSegment')),
        code_only=False)


@ansi_dialect.segment()
class AliasedObjectReferenceSegment(BaseSegment):
    """A reference to an object with an `AS` clause."""
    type = 'object_reference'
    match_grammar = Sequence(Ref('ObjectReferenceSegment'), Ref('AliasExpressionGrammar'))


@ansi_dialect.segment()
class QualifiedNumericLiteralSegment(BaseSegment):
    """A numeric literal with a + or - sign preceeding.

    The qualified numeric literal is a compound of a raw
    literal and a plus/minus sign. We do it this way rather
    than at the lexing step because the lexer doesn't deal
    well with ambiguity.
    """

    type = 'numeric_literal'
    match_grammar = Sequence(
        OneOf(Ref('PlusSegment'), Ref('MinusSegment')),
        Ref('NumericLiteralSegment'),
        code_only=False)


@ansi_dialect.segment()
class FunctionSegment(BaseSegment):
    """A scalar or aggregate function.

    Maybe in the future we should distinguish between
    aggregate functions and other functions. For now
    we treat them the same because they look the same
    for our purposes.
    """
    type = 'function'
    match_grammar = Sequence(
        Ref('FunctionNameSegment'),
        Bracketed(
            Anything()
        ),
        code_only=False
    )
    parse_grammar = Sequence(
        Ref('FunctionNameSegment'),
        Bracketed(
            OneOf(
                # Most functions will be using the delimited route
                # but for COUNT(*) or similar we allow the star segment
                # here.
                Ref('StarSegment'),
                Delimited(
                    Ref('ExpressionSegment'),
                    delimiter=Ref('CommaSegment')
                )
            )
        ),
        code_only=False
    )


@ansi_dialect.segment()
class TableExpressionSegment(BaseSegment):
    """A table expression."""
    type = 'table_expression'
    match_grammar = Sequence(
        OneOf(
            Ref('ObjectReferenceSegment'),
            # Values clause?
        ),
        Ref('AliasExpressionGrammar', optional=True)
    )


@ansi_dialect.segment()
class SelectTargetElementSegment(BaseSegment):
    """An element in the targets of a select statement."""
    type = 'select_target_element'
    # Important to split elements before parsing, otherwise debugging is really hard.
    match_grammar = GreedyUntil(Ref('CommaSegment'))
    parse_grammar = OneOf(
        # *
        Ref('StarSegment'),
        # blah.*
        Sequence(Ref('SingleIdentifierGrammar'), Ref('DotSegment'), Ref('StarSegment'), code_only=False),
        Sequence(
            OneOf(
                Ref('ObjectReferenceSegment'),
                Ref('LiteralGrammar'),
                Ref('FunctionSegment')
            ),
            Ref('AliasExpressionGrammar', optional=True)
        ),
        Sequence(
            OneOf(
                Ref('ExpressionSegment'),
            ),
            Ref('AliasExpressionGrammar', optional=True)
        ),
    )


@ansi_dialect.segment()
class SelectTargetGroupStatementSegment(BaseSegment):
    """A group of elements in a select target statement."""
    type = 'select_target_group'
    match_grammar = GreedyUntil(Ref('FromKeywordSegment'))
    # We should edit the parse grammar to deal with DISTINCT, ALL or similar
    parse_grammar = Sequence(
        OneOf(
            Ref('DistinctKeywordSegment'),
            Ref('AllKeywordSegment'),
            optional=True
        ),
        Delimited(
            Ref('SelectTargetElementSegment'),
            delimiter=Ref('CommaSegment')
        )
    )


@ansi_dialect.segment()
class JoinClauseSegment(BaseSegment):
    """Any number of join clauses, including the `JOIN` keyword."""
    type = 'join_clause'
    match_grammar = OneOf(
        # Types of join clause

        # Old School Comma style clause
        Sequence(
            Ref('CommaSegment'),
            Ref('TableExpressionSegment')
        ),

        # New style Join clauses
        Sequence(
            # NB These qualifiers are optional
            AnyNumberOf(
                Ref('InnerKeywordSegment'),
                Ref('LeftKeywordSegment'),
                Ref('CrossKeywordSegment'),
                max_times=1,
                optional=True
            ),
            Ref('JoinKeywordSegment'),
            Ref('TableExpressionSegment'),
            # NB: this is optional
            AnyNumberOf(
                # ON clause
                Sequence(
                    Ref('OnKeywordSegment'),
                    Bracketed(
                        # this is the lazy option for now. Perhaps we should even
                        # allow ON conditions without brackets?
                        # TODO: Do that.
                        Anything()
                    )
                ),
                # USING clause
                Sequence(
                    Ref('UsingKeywordSegment'),
                    Bracketed(
                        Delimited(
                            Ref('SingleIdentifierGrammar'),
                            delimiter=Ref('CommaSegment')
                        )
                    )
                ),
                max_times=1
            )
        )
    )


@ansi_dialect.segment()
class FromClauseSegment(BaseSegment):
    """A `FROM` clause like in `SELECT`."""
    type = 'from_clause'
    match_grammar = StartsWith(
        Ref('FromKeywordSegment'),
        terminator=OneOf(
            Ref('WhereKeywordSegment'),
            Ref('LimitKeywordSegment'),
            Ref('GroupKeywordSegment'),
            Ref('OrderKeywordSegment'),
            Ref('HavingKeywordSegment')
        )
    )
    parse_grammar = Sequence(
        Ref('FromKeywordSegment'),
        Ref('TableExpressionSegment'),
        AnyNumberOf(
            Ref('JoinClauseSegment'),
            optional=True
        )
    )


ansi_dialect.add(
    Expression_A_Grammar=Sequence(
        OneOf(
            Ref('Expression_C_Grammar'),
            Sequence(
                OneOf(
                    Ref('PlusSegment'),
                    Ref('MinusSegment'),
                    Ref('TildeSegment'),
                    Ref('NotKeywordSegment')
                ),
                Ref('Expression_A_Grammar')
            )
        ),
        AnyNumberOf(
            OneOf(
                Sequence(
                    OneOf(
                        Ref('ArithmeticBinaryOperatorGrammar'),
                        Ref('ComparisonOperatorGrammar'),
                        Ref('BooleanBinaryOperatorGrammar')
                        # We need to add a lot more here...
                    ),
                    Ref('Expression_A_Grammar')
                ),
                Sequence(
                    Ref('InKeywordSegment'),
                    Bracketed(
                        OneOf(
                            Delimited(
                                Ref('LiteralGrammar'),
                                delimiter=Ref('CommaSegment')
                            ),
                            Ref('SelectStatementSegment')
                        )
                    )
                )
            )
        )
    ),
    Expression_B_Grammar=None,  # TODO
    Expression_C_Grammar=Ref('Expression_D_Grammar'),
    Expression_D_Grammar=OneOf(
        Ref('LiteralGrammar'),
        Ref('ObjectReferenceSegment'),
        Ref('FunctionSegment'),
        Bracketed(
            Ref('Expression_A_Grammar')
        )
    ),
)


@ansi_dialect.segment()
class ExpressionSegment(BaseSegment):
    """A expression, either arithmetic or boolean.

    NB: This is potentially VERY recursive and
    mostly uses the grammars above.
    """
    type = 'expression'
    match_grammar = GreedyUntil(
        Ref('CommaSegment'),
        Ref('AsKeywordSegment')
    )
    parse_grammar = Ref('Expression_A_Grammar')


@ansi_dialect.segment()
class WhereClauseSegment(BaseSegment):
    """A `WHERE` clause like in `SELECT` or `INSERT`."""
    type = 'where_clause'
    match_grammar = StartsWith(
        Ref('WhereKeywordSegment'),
        terminator=OneOf(
            Ref('LimitKeywordSegment'),
            Ref('GroupKeywordSegment'),
            Ref('OrderKeywordSegment'),
            Ref('HavingKeywordSegment')
        )
    )
    parse_grammar = Sequence(
        Ref('WhereKeywordSegment'),
        Ref('ExpressionSegment')
    )


@ansi_dialect.segment()
class OrderByClauseSegment(BaseSegment):
    """A `ORDER BY` clause like in `SELECT`."""
    type = 'orderby_clause'
    match_grammar = StartsWith(
        Ref('OrderKeywordSegment'),
        terminator=OneOf(
            Ref('LimitKeywordSegment'),
            Ref('HavingKeywordSegment')
        )
    )
    parse_grammar = Sequence(
        Ref('OrderKeywordSegment'),
        Ref('ByKeywordSegment'),
        Delimited(
            Sequence(
                Ref('ObjectReferenceSegment'),
                OneOf(
                    Ref('AscKeywordSegment'),
                    Ref('DescKeywordSegment'),
                    optional=True
                ),
            ),
            delimiter=Ref('CommaSegment'),
            terminator=Ref('LimitKeywordSegment')
        )
    )


@ansi_dialect.segment()
class ValuesClauseSegment(BaseSegment):
    """A `VALUES` clause like in `INSERT`."""
    type = 'values_clause'
    match_grammar = Sequence(
        OneOf(
            Ref('ValueKeywordSegment'),
            Ref('ValuesKeywordSegment')
        ),
        Delimited(
            Bracketed(
                Delimited(
                    Ref('LiteralGrammar'),
                    delimiter=Ref('CommaSegment')
                )
            ),
            delimiter=Ref('CommaSegment')
        )
    )


@ansi_dialect.segment()
class SelectStatementSegment(BaseSegment):
    """A `SELECT` statement."""
    type = 'select_statement'
    # match grammar. This one makes sense in the context of knowing that it's
    # definitely a statement, we just don't know what type yet.
    match_grammar = StartsWith(Ref('SelectKeywordSegment'))
    parse_grammar = Sequence(
        Ref('SelectKeywordSegment'),
        Ref('SelectTargetGroupStatementSegment'),
        Ref('FromClauseSegment', optional=True),
        Ref('WhereClauseSegment', optional=True),
        Ref('OrderByClauseSegment', optional=True),
        # GreedyUntil(KeywordSegment.make('limit'), optional=True)
    )


@ansi_dialect.segment()
class WithCompoundStatementSegment(BaseSegment):
    """A `SELECT` statement preceeded by a selection of `WITH` clauses."""
    type = 'with_compound_statement'
    # match grammar
    match_grammar = StartsWith(Ref('WithKeywordSegment'))
    parse_grammar = Sequence(
        Ref('WithKeywordSegment'),
        Delimited(
            Sequence(
                Ref('ObjectReferenceSegment'),
                Ref('AsKeywordSegment'),
                Bracketed(Ref('SelectStatementSegment'))
            ),
            delimiter=Ref('CommaSegment'),
            terminator=Ref('SelectKeywordSegment')
        ),
        Ref('SelectStatementSegment')
    )


@ansi_dialect.segment()
class InsertStatementSegment(BaseSegment):
    """A `INSERT` statement."""
    type = 'insert_statement'
    match_grammar = StartsWith(Ref('InsertKeywordSegment'))
    parse_grammar = Sequence(
        Ref('InsertKeywordSegment'),
        Ref('OverwriteKeywordSegment', optional=True),  # Maybe this is just snowflake?
        Ref('IntoKeywordSegment', optional=True),
        Ref('ObjectReferenceSegment'),
        Bracketed(Delimited(Ref('ObjectReferenceSegment'), delimiter=Ref('CommaSegment')), optional=True),
        OneOf(
            Ref('SelectStatementSegment'),
            Ref('ValuesClauseSegment'),
            Ref('WithCompoundStatementSegment')
        )
    )


@ansi_dialect.segment()
class EmptyStatementSegment(BaseSegment):
    """A placeholder for a statement containing nothing but whitespace and comments."""
    type = 'empty_statement'
    grammar = ContainsOnly('comment', 'newline')
    # TODO: At some point - we should lint that these are only
    # allowed at the END - otherwise it's probably a parsing error


@ansi_dialect.segment()
class StatementSegment(BaseSegment):
    """A generic segment, to any of it's child subsegments.

    NOTE: Should this actually be a grammar?
    """
    type = 'statement'
    parse_grammar = OneOf(
        Ref('SelectStatementSegment'), Ref('InsertStatementSegment'),
        Ref('EmptyStatementSegment'), Ref('WithCompoundStatementSegment'))
    match_grammar = GreedyUntil(Ref('SemicolonSegment'))
