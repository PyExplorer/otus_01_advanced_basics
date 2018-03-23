#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local]
# "$request $status $body_bytes_sent "$http_referer" "$http_user_agent"
# "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER"
# '$request_time';

import gzip
import json
import logging
import re
import sys
import time
from argparse import ArgumentParser
from datetime import datetime
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
PREC = 5  # precision for round stat values
PROC_ERRORS_LIMIT = 0.01


def get_config():
    parser = ArgumentParser(description="Parser")
    parser.add_argument("-c", "--config", action='store',
                        default="config.json",
                        help="Set the path for config.json")
    args = parser.parse_args()

    if not path.isfile(args.config):
        print "File " + args.config + " doesn't exist"
        return

    return args.config


def set_logging(log_filename):
    str_format = '[%(asctime)s] %(levelname).1s %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(
        filename=log_filename,
        level=logging.DEBUG,
        format=str_format,
        datefmt=date_format
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


def get_path_last_log(logs_path):
    """
    :param logs_path: path for log's directory
    :return: path to last log, date and time from log's name
    """
    if not path.exists(logs_path):
        # it's an error
        raise Exception('No such directory {} for logs'.format(logs_path))

    log_files = [f for f in listdir(logs_path) if f.startswith(SAMPLE) and
                 re.findall(RE_TIME, f)]
    if not log_files:
        # it is not an error
        logging.info('No appropriate logs in the directory')
        return
    # logs sorted by date and time
    log_name = sorted(log_files, key=lambda x: re.findall(RE_TIME, x))[-1]
    log_path = path.join(logs_path, log_name)
    base_name = path.splitext(log_name)[0]
    parsed_time = datetime.strptime(
        base_name,
        'nginx-access-ui.log-%Y%m%d').strftime('%Y.%m.%d')

    return log_path, parsed_time


def get_report_name(report_path, parsed_time):
    """
    :param report_path: path to report
    :param parsed_time: date and time for report
    :return: path to report with name
    """
    report_name = "report-{}.html".format(parsed_time)
    return path.join(report_path, report_name)


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


def get_stat(data):
    """
    :param data: dict with urls and lists their request_time, total numbers of
    urls, total request time
    :return: list of dictionary with stat
    """
    stat = []
    for key, val in data.get('counter').iteritems():
        stat.append({
            'url': key,
            'count': len(val),
            'count_perc': round(1.0 * len(val) /
                                data.get('number_urls') * 100, PREC),
            'time_sum': sum(val),
            'time_perc': round(1.0 * sum(val) /
                               data.get('overall_request_time'), PREC),
            'time_avg': round(1.0 * sum(val) / len(val), PREC),
            'time_max': max(val),
            'time_med': round(get_median(val), PREC)

        })
    stat.sort(key=lambda d: d['time_sum'], reverse=True)
    return stat


def get_by_line(log_path):
    """
    Generator for big logs - read by line
    :param log_path: path to log
    :return: next line of the log
    """
    if log_path.endswith('.gz'):
        log = gzip.open(log_path, 'r')
    else:
        log = open(log_path)
    for line in log:
        yield line.encode('utf-8')
    log.close()


def get_url_from_line(line, line_number):
    """
    :param line: str with line of report
    :param line_number: current line number
    :return: str with url
    """
    url = re.findall(
        '\d+\.\d+\.\d+\.\d+\s.*\s.*\[.*?]\s".*?\s(.*?)\s.*"\s\d+\s\d+',
        line
    )
    if not url:
        # disable output to log for lines with error
        # logging.error('Can\'t parse url from line {} of report, line is {}'.
        # format(line_number, line.strip()))
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
        logging.error(
            'Can\'t parse request_time from line {} of report'.format(
                line_number)
        )
        return
    return float(request_time[0])


def parse_log(log_path):
    """
    :param log_path: path for log
    :return: list with stat
    """
    number_urls = 0  # number of urls for report
    overall_request_time = 0  # overall time for all "good" urls
    number_lines = 0  # overall number of lines in the log ("good" and "bad")
    number_errors = 0  # number of urls with error

    data = {}
    # read log line by line (not a whole log at a time)
    for i, line in enumerate(get_by_line(log_path), 1):
        url = get_url_from_line(line, i)
        request_time = get_request_time_from_line(line, i)
        number_lines += 1
        if not (url and request_time):
            number_errors += 1
            continue
        value = data.get(url, [])
        value.append(request_time)
        data[url] = value
        number_urls += 1
        overall_request_time += request_time

    percentage_errors = 1.0 * number_errors / number_lines * 100.0
    if percentage_errors > PROC_ERRORS_LIMIT:
        logging.info(
            'Number of errors due to parsing {}'.format(number_errors)
        )

    return {'counter': data,
            'number_urls': number_urls,
            'overall_request_time': overall_request_time
            }


def get_html_report(stat, base_report_path):
    with open(base_report_path) as f:
        html = f.read()
    html = html.replace(BASE_REPORT_REPL, json.dumps(stat))
    return html


def update_ts(ts_path):
    with open(ts_path, "a") as f:
        finish_time = time.time()
        f.write(str(finish_time) + '\n')
    utime(ts_path, (finish_time, finish_time))


def main(settings):
    # prepare path's for log and report
    log_path, parsed_time = get_path_last_log(settings['LOG_DIR'])
    # if we don't have any logs - just stop analyzing without errors
    if not log_path:
        return
    report_path = get_report_name(settings['REPORT_DIR'], parsed_time)

    # exit if report exists
    if path.exists(report_path):
        logging.info('Report {} is exist, exit'.format(report_path))
        return
    base_report_path = path.join(settings['REPORT_DIR'], BASE_REPORT_NAME)

    # fetch data
    data_from_log = parse_log(log_path)

    # collected statistic
    stat = get_stat(data_from_log)

    # create report from stat
    html_report = get_html_report(
        stat[:settings['REPORT_SIZE']],
        base_report_path
    )

    # save report with statistic to file
    with open(report_path, "w") as f:
        f.write(html_report)

    # update ts file
    update_ts(settings.get('TS_FILE', None))


if __name__ == "__main__":
    config_file = get_config()
    if not config_file:
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

    # wrap to catch all errors
    try:
        main(merged_config)
        logging.info('**** Stop analyzing. Work done. ****')

    except:
        logging.exception('Something went wrong')
        logging.info('!!!! Stop analyzing with an error !!!!')
        sys.exit(-1)
