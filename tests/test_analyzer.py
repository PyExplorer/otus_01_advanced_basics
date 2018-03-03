# -*- coding: utf-8 -*-
import unittest

import src.log_analyzer as la

TEST_LINE_CORRECT = """
1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1"
 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-"
"1498697422-2190034393-4708-9752759" "dc7161be3" 0.390
"""
TEST_LINE_INCORRECT_1 = """
1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET/api/v2/banner/25019354 HTTP/1.1"
 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-"
"1498697422-2190034393-4708-9752759" "dc7161be3"
"""
TEST_LINE_INCORRECT_2 = """
196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1"
 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-"
"1498697422-2190034393-4708-9752759" "dc7161be3" 0.390
"""
TEST_LINE_INCORRECT_3 = """
1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] 200 927 "-"
"Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-"
"1498697422-2190034393-4708-9752759" "dc7161be3" 0.390
"""


class AnalyzerTest(unittest.TestCase):
    def test_merge_two_config(self):
        self.assertEqual(
            la.merge_two_config({'a': 1, 'b': 2}, {'a': 2, 'c': 4}), {'a': 2, 'b': 2, 'c': 4})

    def test_get_log_name(self):
        # empty path
        with self.assertRaises(OSError):
            la.get_last_log_name('')

        # no such files in the directory
        self.assertEqual(la.get_last_log_name('.'), None)

        # files are in the directory
        self.assertEqual(la.get_last_log_name('tests/log'), 'nginx-access-ui.log-20170627.txt')

    def test_get_report_name(self):
        # empty log name
        self.assertEqual(
            la.get_report_name(''), None)

        # wrong log name
        self.assertEqual(
            la.get_report_name('nginx-access-ui.log-2017067.txt'), None)

        # name with int
        with self.assertRaises(TypeError):
            la.get_report_name(187)

        # good log name
        self.assertEqual(
            la.get_report_name('nginx-access-ui.log-20170627.txt'), 'report-2017.06.27.html')

    def test_get_median(self):
        # good source
        self.assertEqual(la.get_median([1, 2, 3]), 2)
        self.assertEqual(la.get_median([1, 2, 3, 4]), 2.5)
        # bad source
        with self.assertRaises(IndexError):
            la.get_median([])
        with self.assertRaises(TypeError):
            la.get_median(['as', 'bu', 3, 4])

    def test_get_url_from_line(self):
        self.assertEqual(la.get_url_from_line(TEST_LINE_CORRECT.replace('\n', ''), 1), 'api/v2/banner/25019354')
        self.assertEqual(la.get_url_from_line(TEST_LINE_INCORRECT_1.replace('\n', ''), 1), None)
        self.assertEqual(la.get_url_from_line(TEST_LINE_INCORRECT_2.replace('\n', ''), 1), None)
        self.assertEqual(la.get_url_from_line(TEST_LINE_INCORRECT_3.replace('\n', ''), 1), None)

    def test_get_request_time_from_line(self):
        self.assertEqual(la.get_request_time_from_line(TEST_LINE_CORRECT, 1), 0.390)
        self.assertEqual(la.get_request_time_from_line(TEST_LINE_INCORRECT_1, 1), None)


class ParseAnalyzerTest(unittest.TestCase):
    def test_parse_log(self):
        # bad log from start
        self.assertEqual(la.parse_log('tests/log/nginx-access-ui.log-20170627.txt'), [])
        # bad log in the middle
        self.assertEqual(la.parse_log('tests/log/nginx-access-ui.log-20170625.txt'), [])


class StatAnalyzerTest(unittest.TestCase):
    def test_get_stat(self):
        test_data = [
            {
                'url': 'url2',
                'count': 4,
                'count_perc': round(1.0 * 4 / 8 * 100, la.PREC),
                'time_sum': 18.0,
                'time_perc': round(1.0 * 18 / 25, la.PREC),
                'time_avg': round(1.0 * 18 / 4, la.PREC),
                'time_max': 6.0,
                'time_med': 4.5
            },
            {
                'url': 'url1',
                'count': 3,
                'count_perc': round(1.0 * 3 / 8 * 100, la.PREC),
                'time_sum': 6.0,
                'time_perc': round(1.0 * 6 / 25, la.PREC),
                'time_avg': round(1.0 * 6 / 3, la.PREC),
                'time_max': 3.0,
                'time_med': 2.0
            },
            {
                'url': 'url3',
                'count': 1,
                'count_perc': round(1.0 * 1 / 8 * 100, la.PREC),
                'time_sum': 1.0,
                'time_perc': round(1.0 * 1 / 25, la.PREC),
                'time_avg': round(1.0 * 1 / 1, la.PREC),
                'time_max': 1.0,
                'time_med': 1.0
            },

        ]
        test_data.sort(key=lambda d: d['time_sum'], reverse=True)

        self.assertEqual(la.get_median([1, 2, 3]), 2)
        self.assertEqual(
            la.get_stat(
                # counter
                {
                    'url1': [1.0, 2.0, 3.0],
                    'url2': [3.0, 4.0, 5.0, 6.0],
                    'url3': [1.0]
                },
                # number_urls
                8,
                # overall_request_time
                25
            ),
            test_data
        )


if __name__ == '__main__':
    unittest.main()
