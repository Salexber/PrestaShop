#!/usr/bin/env python

import uuid
import glob
import json
from datetime import datetime, timedelta


def gt(dt_str):
    '''
    Convert Javascrpt DateTime with timezone in Python datetime
    '''
    dt, _, us = dt_str.partition('.')
    dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')
    us = int(us.rstrip('Z'), 10)
    return dt + timedelta(microseconds=us)


def traverse_and_modify_timeout(target, deep):
    '''
    Modify tests timeout
    '''
    if target['tests'] and len(target['tests']):
        for test in target['tests']:
            test['timedOut'] = False

    if target['suites']:
        for suite in target['suites']:
            traverse_and_modify_timeout(suite, deep + 1)


def combine(report_dir):
    '''
    Combine stored json in a directory.
    '''
    reports = glob.glob('{}/*.json'.format(report_dir))
    suites = []
    total_suites = 0
    total_tests = 0
    total_passes = 0
    total_failures = 0
    total_pending = 0
    total_skipped = 0
    start_time = None
    end_time = None

    for idx, report in enumerate(reports):
        print('Parsing {}'.format(report))
        f = open(report, 'r')
        raw_data = f.read()
        parsed_data = json.loads(raw_data)
        if start_time is None or gt(parsed_data['stats']['start']) < gt(start_time):
            start_time = parsed_data['stats']['start']

        if end_time is None or gt(parsed_data['stats']['end']) > gt(end_time):
            end_time = parsed_data['stats']['end']

        total_suites += parsed_data['stats']['suites']
        total_skipped += parsed_data['stats']['skipped']
        total_passes += parsed_data['stats']['passes']
        total_failures += parsed_data['stats']['failures']
        total_pending += parsed_data['stats']['pending']
        total_tests += parsed_data['stats']['tests']

        if parsed_data['suites'] and parsed_data['suites']['suites']:
            for suite in parsed_data['suites']['suites']:
                suites.append(suite)

    return {
        'total_suites': total_suites,
        'total_tests': total_tests,
        'total_passes': total_passes,
        'total_failures': total_failures,
        'total_pending': total_pending,
        'start_time': start_time,
        'end_time': end_time,
        'total_skipped': total_skipped,
        'suites': suites,
    }


def get_percent_class(percent):
    '''
    Get percent class
    '''
    if percent <= 50:
        return 'danger'

    if percent < 80:
        return 'warning'

    return 'success'


def write_report(obj):
    '''
    Write report which have already been combined
    '''
    result = {
        'copyrightYear': datetime.now().year,
        'allTests': [],
        'allFailures': [],
        'allPending': [],
        'allPasses': [],
        'stats': {
            'other': 0,
            'hasOther': False,
            'suites': obj['total_suites'],
            'tests': obj['total_tests'],
            'passes': obj['total_passes'],
            'failures': obj['total_failures'],
            'pending': obj['total_pending'],
            'start': obj['start_time'],
            'end': obj['end_time'],
            'duration': int(
              (
                gt(obj['end_time']) - gt(obj['start_time'])
              ).total_seconds()
            ),
            'testsRegistered': obj['total_tests'] - obj['total_pending'],
            'skipped': obj['total_skipped'],
            'hasSkipped': obj['total_skipped'] > 0,
        }
    }

    result['stats']['passPercent'] = round(
      (
        result['stats']['passes'] / (
          result['stats']['testsRegistered'] - result['stats']['pending']
        ) * 1000
      )
    ) / 10

    result['stats']['pendingPercent'] = round(
      (result['stats']['pending'] / result['stats']['testsRegistered']) * 1000
    ) / 10
    result['stats']['passPercentClass'] = get_percent_class(
      result['stats']['passPercent']
    )
    result['stats']['pendingPercentClass'] = get_percent_class(
      result['stats']['pendingPercent']
    )

    for suite in obj['suites']:
        traverse_and_modify_timeout(suite, 0)

    result['suites'] = {
        'title': 'Combined suites',
        'suites': obj['suites'],
        'uuid': str(uuid.uuid4()),
        'tests': [],
        'pending': [],
        'root': True,
        '_timeout': 400000,
        'beforeHooks': [],
        'afterHooks': [],
        'fullFile': '',
        'file': '',
        'passes': [],
        'failures': [],
        'skipped': [],
        'hasBeforeHooks': False,
        'hasAfterHooks': False,
        'hasTests': False,
        'hasSuites': True,
        'totalTests': 0,
        'totalPasses': 0,
        'totalFailures': 0,
        'totalPending': 0,
        'totalSkipped': 0,
        'hasPasses': False,
        'hasFailures': False,
        'hasPending': False,
        'hasSkipped': False,
        'duration': 0,
        'rootEmpty': True
    }

    with open('result.json', 'w') as f:
        f.write(json.dumps(result))


data = combine('../../reports')
write_report(data)
