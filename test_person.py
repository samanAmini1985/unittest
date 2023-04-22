from person import Person
import pytest
import time

'''
import unittest


class PersonTest(unittest.TestCase):
    def setUp(self):
        self.p1 = Person('saman', 'amini')
        self.p2 = Person('artin', 'amini')

    def tearDown(self):
        print('done...')

    def test_fullname(self):
        self.assertEqual(self.p1.full_name(), 'saman amini')
        self.assertEqual(self.p2.full_name(), 'artin amini')

    def test_eamil(self):
        self.assertEqual(self.p1.email(), 'samanamini@email.com')
        self.assertEqual(self.p2.email(), 'artinamini@email.com')


if __name__ == '__main__':
    unittest.main()
'''


class TestPerson:
    @pytest.fixture
    def setup(self):
        self.p1 = Person('saman', 'amini')
        self.p2 = Person('artin', 'amini')
        yield 'setup'
        time.sleep(2)

    def test_fullname(self, setup):
        assert self.p1.full_name() == 'saman amini'
        assert self.p2.full_name() == 'artin amini'

    def test_email(self, setup):
        assert self.p1.email() == 'samanamini@email.com'
        assert self.p2.email() == 'artinamini@email.com'
