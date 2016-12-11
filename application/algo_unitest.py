import unittest
from Algorithm import UseThread


class WidgetTestCase(unittest.TestCase):
    def setUp(self):
        self.instance = UseThread(0)

    def tearDown(self):
        self.instance.exit()
        self.instance = None

    def test_default_size(self):
        self.assertEqual(self.instance.cal_current_time('2016-12-10 08:12:49.510760'), 29569.510760,
                         'incorrect Time calculation')

    def test_default_size(self):
        cal_interval_time(cur_time, quantity, order_size)


if __name__ == '__main__':
    unittest.main()
