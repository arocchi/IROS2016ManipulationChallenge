#! /usr/bin/env python

import csv
import sys
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
            vals[n] = [float(row[indices[n]]) for row in reader]
            f.seek(0)
            reader.next()
        except ValueError:
            indices[n] = 0

    return vals

fn = sys.argv[1]
f = open(fn,'r')
vals = parse_log(f)

t_fig = figure(figsize=(8,6))
p = plot(vals['time'], vals['loop_time'])
title('Computation times')
legend(p,('dt'))
xlabel('t [s]')
ylabel('t [s]')
tight_layout()
t_fig.savefig('timings.eps', format='eps', transparent='true')
show()
embed()