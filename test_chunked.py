import traceback
from itertools import count, cycle, accumulate
from unittest import TestCase, skipIf
from time import sleep
from operator import add
from sys import version_info

import chunked


class TakeTests(TestCase):
    def test_simple_take(self):
        t = chunked.take(range(10), 5)
        self.assertEqual(t, [0, 1, 2, 3, 4])

    def test_null_take(self):
        t = chunked.take(range(10), 0)
        self.assertEqual(t, [])

    def test_negative_take(self):
        self.assertRaises(ValueError, lambda: chunked.take(-3, range(10)))

    def test_take_too_much(self):
        t = chunked.take(range(5), 10)
        self.assertEqual(t, [0, 1, 2, 3, 4])


class ChunkTests(TestCase):
    def test_even(self):
        self.assertEqual(list(chunked.chunked('ABCDEF', 3)), [['A', 'B', 'C'], ['D', 'E', 'F']])

    def test_odd(self):
        self.assertEqual(list(chunked.chunked('ABCDE', 3)), [['A', 'B', 'C'], ['D', 'E']])

    def test_none(self):
        self.assertEqual(list(chunked.chunked('ABCDE', None)), [['A', 'B', 'C', 'D', 'E']])

    def test_strict_false(self):
        self.assertEqual(list(chunked.chunked('ABCDE', 3, strict=False)), [['A', 'B', 'C'], ['D', 'E']])

    def test_strict_true(self):
        def f():
            return list(chunked.chunked('ABCDE', 3, strict=True))

        self.assertRaisesRegex(ValueError, 'iterator is not divisible by n', f)
        self.assertEqual(list(chunked.chunked('ABCDEF', 3, strict=True)), [['A', 'B', 'C'], ['D', 'E', 'F']])

    def test_strict_true_size_none(self):
        def f():
            return list(chunked.chunked('ABCDE', None, strict=True))

        self.assertRaisesRegex(ValueError, 'n cant be none when strict is True', f)


class FirstTests(TestCase):
    def test_many(self):
        self.assertEqual(chunked.first(x for x in range(4)), 0)

    def test_one(self):
        self.assertEqual(chunked.first([3]), 3)

    def test_default(self):
        self.assertEqual(chunked.first([], 'boo'), 'boo')

    def test_empty_stop_iteration(self):
        try:
            chunked.first([])
        except ValueError:
            formatted_exc = traceback.format_exc()
            self.assertIn('StopIteration', formatted_exc)
            self.assertIn('The above exception was the direct cause ', formatted_exc)
        else:
            self.fail()


class LastTests(TestCase):
    def test_basic(self):
        cases = [
            (range(4), 3),
            (iter(range(4)), 3),
            (range(1), 0),
            (iter(range(1)), 0),
            ({n: str(n) for n in range(5)}, 4)
        ]
        for iterable, expected in cases:
            with self.subTest(iterable=iterable):
                self.assertEqual(chunked.last(iterable), expected)

    def test_default(self):
        for iterable, default, expected in [
            (range(1), None, 0),
            ([], None, None),
            ({}, None, None),
            (iter([]), None, None),
        ]:
            with self.subTest(args=(iterable, default)):
                self.assertEqual(chunked.last(iterable, default=default), expected)

    def test_empty(self):
        for iterable in ([], iter(range(0))):
            with self.subTest(iterable=iterable):
                with self.assertRaises(ValueError):
                    chunked.last(iterable)


class NthOrLastTests(TestCase):
    def test_basic(self):
        self.assertEqual(chunked.nth_or_last(range(3), 1), 1)
        self.assertEqual(chunked.nth_or_last(range(3), 3), 2)

    def test_default_value(self):
        default = 42
        self.assertEqual(chunked.nth_or_last(range(0), 3, default), default)

    def test_iterable_no_default(self):
        self.assertRaises(ValueError, lambda: chunked.nth_or_last(range(0), 0))


class OneTests(TestCase):
    def test_basic(self):
        it = ['item']
        self.assertEqual(chunked.one(it), 'item')

    def test_too_short(self):
        it = []
        for too_short, exc_type in [
            (None, ValueError),
            (IndexError, IndexError)
        ]:
            with self.subTest(too_short=too_short):
                try:
                    chunked.one(it, too_short=too_short)
                except exc_type:
                    formatted_exc = traceback.format_exc()
                    self.assertIn('StopIteration', formatted_exc)
                    self.assertIn('The above exception was the direct cause', formatted_exc)
                else:
                    self.fail()

    def test_too_long(self):
        it = count()
        self.assertRaises(ValueError, lambda: chunked.one(it))
        self.assertEqual(next(it), 2)
        self.assertRaises(OverflowError, lambda: chunked.one(it, too_lang=OverflowError))

    def test_too_lang_default_message(self):
        it = count()
        self.assertRaisesRegex(
            ValueError, 'Expected exactly on item in iterable, but got 0, 1 and perhaps more',
            lambda: chunked.one(it)
        )


class InterleaveTests(TestCase):
    def test_even(self):
        actual = list(chunked.interleave([1, 4, 7], [2, 5, 8], [3, 6, 9]))
        expected = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(actual, expected)

    def test_short(self):
        actual = list(chunked.interleave([1, 4], [2, 5, 7], [3, 6, 8]))
        expected = [1, 2, 3, 4, 5, 6]
        self.assertEqual(actual, expected)

    def test_mixed_types(self):
        it_list = ['a', 'b', 'c', 'd']
        it_str = '123456'
        it_inf = count()
        actual = list(chunked.interleave(it_list, it_str, it_inf))
        expected = ['a', '1', 0, 'b', '2', 1, 'c', '3', 2, 'd', '4', 3]
        self.assertEqual(actual, expected)


class RepeatEachTests(TestCase):
    def test_default(self):
        actual = chunked.repeat_each('ABC')
        expected = ['A', 'A', 'B', 'B', 'C', 'C']
        self.assertEqual(actual, expected)

    def test_basic(self):
        actual = chunked.repeat_each('ABC', 3)
        expected = ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C']
        self.assertEqual(actual, expected)

    def test_empty(self):
        actual = chunked.repeat_each('')
        expected = []
        self.assertEqual(actual, expected)

    def test_no_repeat(self):
        actual = chunked.repeat_each('ABC', 0)
        expected = []
        self.assertEqual(actual, expected)

    def test_negative_repeat(self):
        actual = chunked.repeat_each('ABC', -1)
        expected = []
        self.assertEqual(actual, expected)

    # def test_infinite_repeat(self):
    #     repeater = chunked.repeat_each(cycle('AB'))
    #     actual = chunked.take(repeater, 6)
    #     expected = ['A', 'A', 'B', 'B', 'A', 'A']
    #     self.assertEqual(actual, expected)


class StrictlyNTests(TestCase):
    def test_basic(self):
        iterable = ['A', 'B', 'C', 'D']
        n = 4
        actual = list(chunked.strictly_n(iterable, n))
        expected = iterable
        self.assertEqual(actual, expected)

    def test_too_short_default(self):
        iterable = ['A', 'B', 'C', 'D']
        n = 5
        with self.assertRaises(ValueError) as exc:
            list(chunked.strictly_n(iterable, n))
        self.assertEqual('Too few items in iterable ( got 4 )', exc.exception.args[0])

    def test_too_long_default(self):
        iterable = ['A', 'B', 'C', 'D']
        n = 3
        with self.assertRaises(ValueError) as exc:
            list(chunked.strictly_n(iterable, n))
        self.assertEqual('Too many items in iterable ( at least 4)', exc.exception.args[0])

    def test_too_short_custom(self):
        call_count = 0

        def too_sort(item_count):
            nonlocal call_count
            call_count += 1

        iterable = ['A', 'B', 'C', 'D']
        n = 6
        actual = []
        for item in chunked.strictly_n(iterable, n, too_short=too_sort):
            actual.append(item)
        expected = iterable
        self.assertEqual(actual, expected)
        self.assertEqual(call_count, 1)

    def test_too_long_custom(self):
        import logging
        iterable = ['A', 'B', 'C', 'D']
        n = 2
        too_long = lambda item_count: logging.warning(f'Picked the first {n} items')

        with self.assertLogs(level='WARNING') as exc:
            actual = list(chunked.strictly_n(iterable, n, too_long=too_long))
        self.assertEqual(actual, ['A', 'B'])
        self.assertIn('Picked the first 2 items', exc.output[0])


class OnlyTests(TestCase):
    def test_default(self):
        self.assertEqual(chunked.only([]), None)
        self.assertEqual(chunked.only([1]), 1)
        self.assertRaises(ValueError, lambda: chunked.only([1, 2]))

    def test_custom_value(self):
        self.assertEqual(chunked.only([], default='!'), '!')
        self.assertEqual(chunked.only([1], default='!'), 1)
        self.assertRaises(ValueError, lambda: chunked.only([1, 2], default='!'))

    def test_custom_exception(self):
        self.assertEqual(chunked.only([], too_lang=RuntimeError), None)
        self.assertEqual(chunked.only([1], too_lang=RuntimeError), 1)
        self.assertRaises(RuntimeError, lambda: chunked.only([1, 2], too_lang=RuntimeError))

    def test_default_exception_message(self):
        self.assertRaisesRegex(
            ValueError, 'Expected exactly one item in iterable, but foo, boo and perhaps more.',
            lambda: chunked.only(['foo', 'boo', 'baz'])
        )


class AlwaysReversibleTests(TestCase):
    def test_regular_reversed(self):
        self.assertEqual(
            list(reversed(range(10))), list(chunked.always_reversible(range(10)))
        )
        self.assertEqual(
            list(reversed([1, 2, 3])), list(chunked.always_reversible([1, 2, 3]))
        )
        self.assertEqual(
            reversed([1, 2, 3]).__class__, chunked.always_reversible([1, 2, 3]).__class__
        )

    def test_nonseq_reversed(self):
        self.assertEqual(
            list(reversed(range(10))), list(chunked.always_reversible(x for x in range(10)))
        )
        self.assertEqual(
            list(reversed([1, 2, 3])), list(chunked.always_reversible(x for x in [1, 2, 3]))
        )
        self.assertNotEqual(
            reversed((1, 2)).__class__, chunked.always_reversible(x for x in (1, 2)).__class__
        )


class AlwaysIterableTests(TestCase):
    def test_single(self):
        self.assertEqual(list(chunked.always_iterable(1)), [1])

    def tset_string(self):
        for obj in ['foo', b'bar', 'baz']:
            actual = list(chunked.always_iterable(obj))
            expected = [obj]
            self.assertEqual(actual, expected)

    def test_base_type(self):
        dict_obj = {'a': 1, 'b': 2}
        str_obj = '123'

        default_actual = list(chunked.always_iterable(dict_obj))
        default_expected = list(default_actual)
        self.assertEqual(default_actual, default_expected)

        costume_actual = list(chunked.always_iterable(dict_obj, base_type=dict))
        costume_expected = [dict_obj]
        self.assertEqual(costume_actual, costume_expected)

        str_actual = list(chunked.always_iterable(str_obj, base_type=None))
        str_expected = list(str_obj)
        self.assertEqual(str_actual, str_expected)

        base_type = ((dict,),)
        costume_actual = list(chunked.always_iterable(dict_obj, base_type=base_type))
        costume_expected = [dict_obj]
        self.assertEqual(costume_actual, costume_expected)

    def test_iterable(self):
        self.assertEqual(list(chunked.always_iterable([1, 2])), [1, 2])
        self.assertEqual(list(chunked.always_iterable([1, 2], base_type=list)), [[1, 2]])
        self.assertEqual(list(chunked.always_iterable(iter('foo'))), ['f', 'o', 'o'])
        self.assertEqual(list(chunked.always_iterable([])), [])

    def test_non(self):
        self.assertEqual(list(chunked.always_iterable(None)), [])

    def test_generator(self):
        def _gen():
            yield 0
            yield 1

        self.assertEqual(list(chunked.always_iterable(_gen())), [0, 1])


class SplitAfterTests(TestCase):
    def test_start_with_sep(self):
        actual = list(chunked.split_after('xooxoo', lambda c: c == 'x'))
        expected = [['x'], ['o', 'o', 'x'], ['o', 'o']]
        self.assertEqual(actual, expected)

    def test_ends_with_sep(self):
        actual = list(chunked.split_after('ooxoox', lambda c: c == 'x'))
        expected = [['o', 'o', 'x'], ['o', 'o', 'x']]
        self.assertEqual(actual, expected)

    def test_no_sep(self):
        actual = list(chunked.split_after('ooo', lambda c: c == 'x'))
        expected = [['o', 'o', 'o']]
        self.assertEqual(actual, expected)

    def test_max_split(self):
        for args, expected in [
            (
                    ('a,b,c,d', lambda c: c == ',', -1),
                    [['a', ','], ['b', ','], ['c', ','], ['d']]
            ),
            (
                    ('a,b,c,d', lambda c: c == ',', 0),
                    [['a', ',', 'b', ',', 'c', ',', 'd']]
            ),
            (
                    ('a,b,c,d', lambda c: c == ',', 1),
                    [['a', ','], ['b', ',', 'c', ',', 'd']]
            ),
            (
                    ('a,b,c,d', lambda c: c == ',', 2),
                    [['a', ','], ['b', ','], ['c', ',', 'd']]
            ),
            (
                    ('a,b,c,d', lambda c: c == ',', 10),
                    [['a', ','], ['b', ','], ['c', ','], ['d']]
            ),
            (
                    ('a,b,c,d', lambda c: c == '@', 2),
                    [['a', ',', 'b', ',', 'c', ',', 'd']]
            ),
            (
                    ('a,b,c,d', lambda c: c != ',', 2),
                    [['a'], [',', 'b'], [',', 'c', ',', 'd']]
            ),
        ]:
            actual = list(chunked.split_after(*args))
            self.assertEqual(actual, expected)


class SpiltIntoTests(TestCase):
    def test_iterable_just_right(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [2, 3, 4]
        expected = [[1, 2], [3, 4, 5], [6, 7, 8, 9]]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_iterable_too_small(self):
        iterable = [1, 2, 3, 4, 5, 6, 7]
        sizes = [2, 3, 4]
        expected = [[1, 2], [3, 4, 5], [6, 7]]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_iterable_too_small_extra(self):
        iterable = [1, 2, 3, 4, 5, 6, 7]
        sizes = [2, 3, 4, 5]
        expected = [[1, 2], [3, 4, 5], [6, 7], []]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_iterable_too_large(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [2, 3, 2]
        expected = [[1, 2], [3, 4, 5], [6, 7]]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_using_none_with_leftover(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [2, 3, None]
        expected = [[1, 2], [3, 4, 5], [6, 7, 8, 9]]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_using_non_without_leftover(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [2, 3, 4, None]
        expected = [[1, 2], [3, 4, 5], [6, 7, 8, 9], []]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_using_none_mid_sizes(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [2, 3, None, 4]
        expected = [[1, 2], [3, 4, 5], [6, 7, 8, 9]]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_iterable_empty(self):
        iterable = []
        sizes = [2, 4, 2]
        expected = [[], [], []]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_iterable_empty_using_none(self):
        iterable = []
        sizes = [2, 4, None, 2]
        expected = [[], [], []]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_sizes_empty(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = []
        expected = []
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_both_empty(self):
        iterable = []
        sizes = []
        expected = []
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_bool_in_sizes(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [3, True, 2, False]
        expected = [[1, 2, 3], [4], [5, 6], []]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_invalid_in_sizes(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [1, [], 3]
        with self.assertRaises(ValueError):
            list(chunked.split_into(iterable, sizes))

    def test_invalid_in_sizes_after_none(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = [3, 4, None, []]
        expected = [[1, 2, 3], [4, 5, 6, 7], [8, 9]]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

    def test_generator_iterable_integrity(self):
        iterable = (i for i in range(10))
        sizes = [2, 3]
        expected = [[0, 1], [2, 3, 4]]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

        iterable_expected = [5, 6, 7, 8, 9]
        iterable_actual = list(iterable)
        self.assertEqual(iterable_actual, iterable_expected)

    def test_generator_sizes_integrity(self):
        iterable = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        sizes = (i for i in [1, 2, None, 3, 4])
        expected = [[1], [2, 3], [4, 5, 6, 7, 8, 9]]
        actual = list(chunked.split_into(iterable, sizes))
        self.assertEqual(actual, expected)

        sizes_expected = [3, 4]
        sizes_actual = list(sizes)
        self.assertEqual(sizes_actual, sizes_expected)


class MapIfTests(TestCase):
    def test_without_fun_else(self):
        iterable = list(range(-5, 5))
        actual = list(chunked.map_if(iterable, lambda x: x > 3, lambda x: 'too big'))
        expected = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 'too big']
        self.assertEqual(actual, expected)

    def tset_with_func_else(self):
        iterable = list(range(-5, 5))
        actual = list(chunked.map_if(iterable, lambda x: x >= 0, lambda x: 'notneg', lambda x: 'neg'))
        expected = ['neg'] * 5 + ['notneg'] * 5
        self.assertEqual(actual, expected)

    def test_empty(self):
        actual = list(chunked.map_if([], lambda x: len(x) > 5, lambda x: None))
        expected = []
        self.assertEqual(actual, expected)


class TimeLimitedTests(TestCase):
    def test_basic(self):
        def generator():
            yield 1
            yield 2
            sleep(0.2)
            yield 3

        iterable = chunked.time_limited(0.1, generator())
        actual = list(iterable)
        expected = [1, 2]
        self.assertEqual(actual, expected)
        self.assertTrue(iterable.timed_out)

    def test_complete(self):
        iterable = chunked.time_limited(2, iter(range(10)))
        actual = list(iterable)
        expected = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.assertEqual(actual, expected)
        self.assertFalse(iterable.timed_out)

    def test_zero_limit(self):
        iterable = chunked.time_limited(0, count())
        actual = list(iterable)
        expected = []
        self.assertEqual(actual, expected)
        self.assertTrue(iterable.timed_out)

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            list(chunked.time_limited(-0.1, count()))


class DifferenceTests(TestCase):
    def test_normal(self):
        iterable = [10, 20, 30, 40, 50]
        actual = list(chunked.difference(iterable))
        expected = [10, 10, 10, 10, 10]
        self.assertEqual(actual, expected)

    def test_custom(self):
        iterable = [10, 20, 30, 40, 50]
        actual = list(chunked.difference(iterable, add))
        expected = [10, 30, 50, 70, 90]
        self.assertEqual(actual, expected)

    def test_roundtrip(self):
        original = list(range(100))
        accumulated = accumulate(original)
        actual = list(chunked.difference(accumulated))
        self.assertEqual(original, actual)

    def test_one(self):
        self.assertEqual(list(chunked.difference([0])), [0])

    def test_empty(self):
        self.assertEqual(list(chunked.difference([])), [])

    @skipIf(version_info[:2] < (3, 8), 'accumulate with initial needs +3.8')
    def test_initial(self):
        original = list(range(100))
        accumulated = accumulate(original, initial=100)
        actual = list(chunked.difference(accumulated, initial=100))
        self.assertEqual(original, actual)


class ValuChaintest(TestCase):
    def test_empty(self):
        actual = list(chunked.value_chain())
        expected = []
        self.assertEqual(actual, expected)

    def test_simple(self):
        actual = list(chunked.value_chain(1, 2.17, False, 'foo'))
        expected = [1, 2.17, False, 'foo']
        self.assertEqual(actual, expected)

    def test_more(self):
        actual = list(chunked.value_chain(b'bar', [1, 2, 3], 4, {'key': 1}))
        expected = [b'bar', 1, 2, 3, 4, 'key']
        self.assertEqual(actual, expected)

    def test_empty_list(self):
        actual = list(chunked.value_chain(1, 2, [], 3, 4))
        expected = [1, 2, 3, 4]
        self.assertEqual(actual, expected)

    def test_complex(self):
        obj = object()
        actual = list(
            chunked.value_chain(
                (1, (2, (3,))),
                ['foo', ['bar', ['baz']], 'tic'],
                {'key': {'foo': 1}},
                obj
            )
        )
        expected = [1, (2, (3,)), 'foo', ['bar', ['baz']], 'tic', 'key', obj]
        self.assertEqual(actual, expected)


class SequenceViewTests(TestCase):
    def test_init(self):
        view = chunked.SequenceView((1, 2, 3))
        self.assertEqual(repr(view), 'SequenceView((1, 2, 3))')
        self.assertRaises(TypeError, lambda: chunked.SequenceView({}))

    def test_update(self):
        seq = [1, 2, 3]
        view = chunked.SequenceView(seq)
        self.assertEqual(len(view), 3)
        self.assertEqual(repr(view), 'SequenceView([1, 2, 3])')

        seq.pop()
        self.assertEqual(len(view), 2)
        self.assertEqual(repr(view), 'SequenceView([1, 2])')

    def test_indexing(self):
        seq = ('a', 'b', 'c', 'd', 'e', 'f')
        view = chunked.SequenceView(seq)
        for i in range(-len(seq), len(seq)):
            self.assertEqual(view[i], seq[i])

    def test_abs_methods(self):
        seq = ('a', 'b', 'c', 'd', 'e', 'f', 'f')
        view = chunked.SequenceView(seq)

        self.assertIn('b', view)
        self.assertNotIn('g', view)
        self.assertEqual(list(iter(view)), list(seq))
        self.assertEqual(list(reversed(view)), list(reversed(seq)))
        self.assertEqual(seq.count('f'), 2)

