#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import re
import argparse
from platform import release

"""
From kernel 3.14, there is a value 'MemAvailable' which
estimates the allocatable memory for new workload without
swapping.

This script supports calculating 'MemAvailable' based on:
    - MemTotal
    - MemFree
    - Active(File)
    - Inactive(File)
    - SReclaimable
    - "low" watermarks in /proc/zoneinfo

author: https://github.com/cuongnv23
"""

KV = release().split('-')[0]


def ok(message):
    print "OK - %s" % message
    sys.exit(0)


def warning(message):
    print "WARNING - %s" % message
    sys.exit(1)


def critical(message):
    print "CRITICAL - %s" % message
    sys.exit(2)


def unknown(message):
    print "UNKNOWN - %s" % message
    sys.exit(3)


def mem_info():
    """
    Calculate free memory based on /proc/[meminfo|zoneinfo]
    """
    MEM_TOTAL = 'MemTotal'
    MEM_AVAI = 'MemAvailable'
    MEM_FREE = 'MemFree'
    MEM_ACT = 'Active(file)'
    MEM_IN_ACT = 'Inactive(file)'
    MEM_SRECLAIM = 'SReclaimable'

    # Parse /proc/meminfo to get values
    with open('/proc/meminfo') as f:
        infos = dict()
        for line in f.read().splitlines():
            infos[line.split(':')[0]] = line.split(':')[1].strip()
        mem_total = int(infos[MEM_TOTAL].split()[0])
        mem_free = int(infos[MEM_FREE].split()[0])
        mem_act = int(infos[MEM_ACT].split()[0])
        mem_in_act = int(infos[MEM_IN_ACT].split()[0])
        mem_sreclaim = int(infos[MEM_SRECLAIM].split()[0])
        if KV >= '3.14':
            mem_avai = int(infos[MEM_AVAI].split()[0])
        else:
            mem_avai = 0
    # Parse /proc/zoneinfo to get low watermark values
    with open('/proc/zoneinfo') as f:
        zone = 0
        regex = re.compile('low')
        for line in f.readlines():
            match = regex.findall(line)
            if match:
                k, v = line.split()
                zone += int(v)
        # 3 pages, in amd64 each page mostly is 4kB in size
        mem_zone = zone * 12

    return {'m_total': mem_total,
            'm_avai': mem_avai,
            'm_free': mem_free,
            'm_act': mem_act,
            'm_in_act': mem_in_act,
            'm_sreclaim': mem_sreclaim,
            'm_zone': mem_zone,
            }


def check_mem(warn, crit):
    """
    args:
        - warn: free memory to be a WARNING.
        - crit: free memory to be a CRITICAL.
    Return codes:
        0 : OK
        1 : WARNING
        2 : CRITICAL
        3 : UNKNOWN
    """
    # Calculate free memory based on kernel version
    m = mem_info()
    if KV < '3.14':
        free = m['m_free'] + m['m_sreclaim'] + m['m_act'] + m['m_in_act'] - \
            m['m_zone']
        mf = 100 * free / m['m_total']
    else:
        free = m['m_avai']
        mf = 100 * free / m['m_total']
    if mf <= crit:
        critical("%d%% Free (%dM/%dM)" % (mf, free/1024, m['m_total']/1024))
    elif mf < warn and mf > crit:
        warning("%d%% Free (%dM/%dM)" % (mf, free/1024, m['m_total']/1024))
    elif mf >= warn:
        ok("%d%% Free (%dM/%dM)" % (mf, free/1024, m['m_total']/1024))
    else:
        unknown("Unknown free memory")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--warn", type=int, dest="warn", default=60,
                        help="Warning value")
    parser.add_argument("-c", "--crit", type=int, dest="crit", default=30,
                        help="Critical value")
    args = parser.parse_args()
    try:
        warn = args.warn
        crit = args.crit
    except Exception as e:
        unknown("Unable to parse arguments: %s", e)
    return warn, crit


if __name__ == '__main__':
    warn, crit = parse_args()
    check_mem(warn, crit)
