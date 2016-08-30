#! /usr/bin/env python

import csv
import sys
from collections import defaultdict
import math
import numpy as np
from matplotlib.pyplot import *
from IPython import embed
import sys, traceback

names = ['time', 'q_u', 'q_u_ref', 'f_a', 'tau', 'tau_c', 'robotname']

traceback_template = '''Traceback (most recent call last):
  File "%(filename)s", line %(lineno)s, in %(name)s
%(type)s: %(message)s\n''' # Skipping the "actual line" item

def parse_log(f):
    reader = csv.reader(f, quoting = csv.QUOTE_NONE)
    headers = reader.next()
    headers = [n.strip() for n in headers]
    indices = {}
    vals = {}
    for n in names:
        try:
            indices[n] = headers.index(n)
            vals[n] = [row[indices[n]] for row in reader]
            for i, val in enumerate(vals[n]):
                if val.strip('[]') != val:
                    vals[n][i] = np.fromstring(val.strip('[]'), sep =' ')
                elif n != 'robotname':
                    vals[n][i] = float(val)
            f.seek(0)
            reader.next()
        except ValueError:
            indices[n] = 0

    return vals

fn = sys.argv[1]
f = open(fn, 'r')

try:
    vals = parse_log(f)
    if vals['robotname'][0] == 'soft_hand':
        index_finger_u = [1,3]
        legend_1 = ('prox q', 'dist q', 'prox eq', 'dist eq')
        legend_2 = (
        'f', r'$\tau$ prox',  r'$\tau$ dist', r'$\tau_c$ prox',
        r'$\tau_c$ dist')
        #legend_1 = ('proximal q', 'middle q', 'distal q', 'proximal eq', 'middle eq', 'distal eq')
        #legend_2 = ('f', r'$\tau$ proximal', r'$\tau$ middle', r'$\tau$ distal', r'$\tau_c$ proximal', r'$\tau_c$ middle', r'$\tau_c$ distal')
    else:
        index_finger_u = [1,2]
        legend_1 = ('proximal q', 'distal q', 'proximal eq', 'distal eq')
        legend_2 = (r'$f_0$', r'$\tau$ distal', r'$\tau$ proximal', r'$\tau_c$ distal', r'$\tau_c$ proximal')

    for name in ['q_u', 'q_u_ref', 'tau', 'tau_c']:
        for i, val in enumerate(vals[name]):
            vals[name][i] = val[index_finger_u]
    for i, val in enumerate(vals['f_a']):
        vals['f_a'][i] = val[0]

    fig_q_vs_q_ref = figure(figsize=(8.5, 5))
    p = plot(vals['time'], vals['q_u'], vals['time'], vals['q_u_ref'])
    title('Configuration evolution vs expected Equilibrium Configuration')
    legend(p, legend_1)
    xlabel('t [s]')
    ylabel('joint config [rad]')
    tight_layout()
    fig_q_vs_q_ref.savefig('fig_q_vs_q_ref.eps', format='eps', transparent='true')

    fig_tau_vs_tau_c = figure(figsize=(8.5, 5))
    p = plot(vals['time'], vals['f_a'], vals['time'], vals['tau'], vals['time'], vals['tau_c'])
    title('Tendon tension, actuated torques and contact torques ')
    legend(p, legend_2)
    xlabel('t [s]')
    ylabel('joint torques [Nm]')
    tight_layout()
    fig_tau_vs_tau_c.savefig('fig_tau_vs_tau_c.eps', format='eps', transparent='true')

    fig_exp_all = figure(figsize=(7.5, 9))
    subplot(211)
    p = plot(vals['time'], vals['q_u'], vals['time'], vals['q_u_ref'])
    title('Configuration evolution vs expected Equilibrium Configuration')
    legend(p, legend_1)
    xlabel('t [s]')
    ylabel('joint config [rad]')

    subplot(212)
    p = plot(vals['time'], vals['f_a'], vals['time'], vals['tau'], vals['time'], vals['tau_c'])
    title('Tendon tension, actuated torques and contact torques ')
    legend(p, legend_2)
    xlabel('t [s]')
    ylabel('joint torques [Nm]')
    tight_layout()
    fig_exp_all.savefig('fig_exp_all.eps', format='eps', transparent='true')

    show()
except:
    print traceback.format_exc()
    embed()

