import unittest
from Algorithm import UseThread


class WidgetTestCase(unittest.TestCase):
    def setUp(self):
        self.instance = UseThread(0)

    def tearDown(self):
        self.instance.exit()
        self.instance = None

    def test_cal_current_time(self):
        self.assertEqual(self.instance.cal_current_time('2016-12-10 08:12:49.510760'), 29569.510760,
                         'incorrect Time calculation')

    def test_cal_interval_time(self):
        self.assertEqual(self.instance.cal_interval_time(29569, 500, 100), 5913.8,
                         'incorrect Time calculation')


if __name__ == '__main__':
    unittest.main()
