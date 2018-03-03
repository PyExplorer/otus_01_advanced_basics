#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import gzip
import json
import logging
import re
import sys
import time
from argparse import ArgumentParser
from os import listdir
from os import path
from os import utime

CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
}

SAMPLE = 'nginx-access-ui.log-'
RE_TIME = '[-](\d{8})[.]'
BASE_REPORT_NAME = 'report.html'
BASE_REPORT_REPL = '$table_json'
PREC = 7  # precision for round stat values
PROC_ERRORS_LIMIT = 50  # percentage to stop parsing
START_CHECK_ERRORS = 3  # number of attempts for start checking on errors


def get_config_from_parser():
    parser = ArgumentParser(description="Parser")
    parser.add_argument("-c", "--config", action='store', default="config.json",
                        help="Set the path for config.json")
    args = parser.parse_args()
    return args.config


def set_logging(log_filename):
    logging.basicConfig(
        filename=log_filename,
        level=logging.DEBUG,
        format='[%(asctime)s] '
               '%(levelname).1s '
               '%(message)s ',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def merge_two_config(a, b):
    """
    :param a: first dict
    :param b: second dict
    :return: merged dict
    """
    c = a.copy()
    c.update(b)
    return c


def get_last_log_name(log_path):
    """
    :param log_path: path for log's directory
    :return: str with name for the last log
    """
    log_files = [f for f in listdir(log_path) if f.startswith(SAMPLE) and re.findall(RE_TIME, f)]
    if not log_files:
        logging.info('No appropriate logs in the directory')
        return
    return sorted(log_files, key=lambda x: re.findall(RE_TIME, x))[-1]


def get_log_path(log_dir, log_name):
    return path.join(log_dir, log_name)


def get_report_name(log_file):
    """
    :param log_file: name for log with date and time
    :return: name for report with date and time from log name
    """
    base_name = re.findall(RE_TIME, log_file)
    if not base_name:
        logging.error('No date and time for report, can\'t create report\'s name')
        return
    base_name = base_name[0]
    return "report-{}.{}.{}.html".format(base_name[:4], base_name[4:6], base_name[6:])


def get_report_path(report_dir, report_name):
    return path.join(report_dir, report_name)


def is_report_exist(report_path):
    if path.exists(report_path):
        logging.info('Report {} is exist, exit'.format(report_path))
        return 1


def get_median(source_list):
    """
    :param source_list: list with float to count median
    :return: value of median
    """
    if len(source_list) % 2 == 0:
        med = int(len(source_list) / 2 - 1)
        return (source_list[med] + source_list[med + 1]) / 2.0
    else:
        med = int(len(source_list) / 2)
        return source_list[med]


def get_stat(counter, number_urls, overall_request_time):
    """
    :param counter: dict with urls and lists their request_time
    :param number_urls: total numbers af urls
    :param overall_request_time: total request time
    :return: list of dictionary with stat
    """
    stat = []
    for key, val in counter.iteritems():
        stat.append({
            'url': key,
            'count': len(val),
            'count_perc': round(1.0 * len(val) / number_urls * 100, PREC),
            'time_sum': sum(val),
            'time_perc': round(1.0 * sum(val) / overall_request_time, PREC),
            'time_avg': round(1.0 * sum(val) / len(val), PREC),
            'time_max': max(val),
            'time_med': round(get_median(val), PREC)

        })
    stat.sort(key=lambda d: d['time_sum'], reverse=True)
    return stat


def get_by_line(log_path):
    """
    Generator for big log - read by line
    :param log_path: path to log
    :return: next line of the log
    """
    if log_path.endswith('.gz'):
        log = gzip.open(log_path, 'r')
    else:
        log = open(log_path)
    for line in log:
        yield line
    log.close()


def get_url_from_line(line, line_number):
    """
    :param line: str with line of report
    :param line_number: current line number
    :return: str with url
    """
    url = re.findall('\d+\.\d+\.\d+\.\d+\s.*\s.*\[.*?]\s".*?\s\/(.*?)\s.*"\s\d+\s\d+', line)
    if not url:
        logging.error('Can\'t parse url from line {} of report'.format(line_number))
        return
    return url[0]


def get_request_time_from_line(line, line_number):
    """
    :param line: str with line of report
    :param line_number: current line number
    :return: float request_time
    """
    request_time = re.findall('\d+.\d+$', line)
    if not request_time:
        logging.error('Can\'t parse request_time from line {} of report'.format(line_number))
        return
    return float(request_time[0])


def parse_log(log_path):
    """
    :param log_path: path for log
    :return: list with stat
    """
    number_urls = overall_request_time = number_errors = 0
    data = {}

    for i, line in enumerate(get_by_line(log_path), 1):
        url = get_url_from_line(line, i)
        request_time = get_request_time_from_line(line, i)
        if not (url and request_time):
            number_errors += 1
            # as we don't know how many lines in log - check on errors after START_CHECK_ERRORS lines
            if i < START_CHECK_ERRORS:
                continue
            percentage_errors = 1.0 * number_errors / i * 100.0
            if percentage_errors > PROC_ERRORS_LIMIT:
                logging.error(
                    'Percentage of errors {} more than limit {}, stop parsing'.format(
                        percentage_errors, PROC_ERRORS_LIMIT
                    )
                )
                return []
            continue
        value = data.get(url, [])
        value.append(request_time)
        data[url] = value
        number_urls += 1
        overall_request_time += request_time

    if number_errors > 0:
        logging.info('Number of errors due to parsing {}'.format(number_errors))

    return get_stat(data, number_urls, overall_request_time)


def save_to_file(html, report_path):
    try:
        with open(report_path, "w") as f:
            f.write(html)
        return 1
    except TypeError as e:
        logging.exception('Error with saving report {}'.format(e.message))
        return


def get_html_report(stat, base_report_path):
    try:
        with open(base_report_path) as f:
            html = f.read()
        html = html.replace(BASE_REPORT_REPL, json.dumps(stat))
        return html
    except TypeError as e:
        logging.exception('Error with opening a template for the report {}'.format(e.message))
        return


def update_ts(ts_path):
    try:
        with open(ts_path, "a") as f:
            finish_time = time.time()
            f.write(str(finish_time) + '\n')
        utime(ts_path, (finish_time, finish_time))
        return 1
    except TypeError as e:
        logging.exception('Error with working with ts file {}'.format(e.message))
        return


def main(settings):
    # wrap to catch all errors
    try:
        # prepare path's for log and report
        log_name = get_last_log_name(settings['LOG_DIR'])
        if not log_name:
            # if we don't have any logs - just stop analyzing without errors
            return 1
        log_path = get_log_path(settings['LOG_DIR'], log_name)
        report_name = get_report_name(log_name)
        if not report_name:
            return 0
        report_path = get_report_path(settings['REPORT_DIR'], report_name)
        base_report_path = get_report_path(settings['REPORT_DIR'], BASE_REPORT_NAME)

        # exit if report exists
        if is_report_exist(report_path):
            return 1

        # fetch statistic
        stat = parse_log(log_path)
        if not stat:
            logging.error('Report was not created - stat was empty, exit'.format(report_name))
            return 0

        # create report from stat
        html_report = get_html_report(stat[:settings['REPORT_SIZE']], base_report_path)
        if not html_report:
            logging.error('Report was not created, exit'.format(report_name))
            return 0

        # save report with statistic to file
        if not save_to_file(html_report, report_path):
            logging.error('Report was not saving, exit'.format(report_name))
            return 0

        if not update_ts(settings.get('TS_FILE', None)):
            logging.error('ts file was not created - but report was created'.format(report_name))
            return 0

        return 1
    except:  # it is not good but for learning goals we want to catch all exceptions
        logging.exception('Something went wrong')
        return 0


if __name__ == "__main__":
    config_file = get_config_from_parser()

    if not path.isfile(config_file):
        print "File " + config_file + " not exists"
        sys.exit(-1)

    try:
        with open(config_file) as json_data_file:
            config_from_file = json.load(json_data_file)
    except ValueError:
        print "File " + config_file + " is corrupted and can't be parsed"
        sys.exit(-1)

    merged_config = merge_two_config(CONFIG, config_from_file)

    set_logging(merged_config.get('LOG_FILE', None))
    logging.info('** Start analyzing... **')
    status = main(merged_config)
    if status:
        logging.info('**** Stop analyzing. Work done. ****')
    else:
        logging.info('!!!! Stop analyzing with an error !!!!')
