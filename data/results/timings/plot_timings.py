#! /usr/bin/env python

import csv
import sys, traceback
from collections import defaultdict
import math
import numpy as np
from matplotlib.pyplot import *
from IPython import embed


time_column = 'time'
dt_column = 'dt'
loop_time_column = 'loop_time'

names = [time_column, dt_column, loop_time_column]


def parse_log(f):
    reader = csv.reader(f)
    headers = reader.next()
    headers = [n.strip() for n in headers]
    indices = {}
    vals = {}
    for n in names:
        try:
            indices[n] = headers.index(n)
            if n != 'robotname':
                vals[n] = [float(row[indices[n]]) for row in reader]
            else:
                vals[n] = [row[indices[n]] for row in reader]
            f.seek(0)
            reader.next()
        except ValueError:
            indices[n] = 0

    return vals

fn1 = sys.argv[1]
f1 = open(fn1, 'r')
fn2 = sys.argv[2]
f2 = open(fn2, 'r')
vals1 = parse_log(f1)
vals2 = parse_log(f2)

try:
    t_fig = figure(figsize=(8, 6))
    p = plot(vals1['time'], vals1['loop_time'], vals2['time'], vals2['loop_time'])
    title('Computation times')
    legend(p, ('CUHE', 'regular'), loc = 'best')
    xlabel('t [s]')
    ylabel('t [s]')
    tight_layout()
    autoscale(tight=True)
    t_fig.savefig('timings_comp.eps', format='eps', transparent='true')

    print "rt factor", 0.01/np.mean(vals1['loop_time'])
    show()
except:
    print traceback.format_exc()
    embed()
