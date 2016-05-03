# -*- coding: utf-8 -*-
"""
Common package shared between the programs to allow code reusing.
"""
import datetime

def time_in_millis(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    return int( (dt - epoch).total_seconds() * 1000.0 )