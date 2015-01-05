#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from pprint import pprint
import numpy as np
import pandas as pd
try:
    from colorama import Fore, Style, init
except ImportError:
    pass
from pyethereum import tester as t

np.set_printoptions(linewidth=500)
                    # precision=5,
                    # suppress=True,
                    # formatter={"float": "{: 0.3f}".format})
pd.set_option("display.max_rows", 25)
pd.set_option("display.width", 1000)
pd.set_option('display.float_format', lambda x: '%.8f' % x)

max_iterations = 4
tolerance = 1e-12
init()

# true=1, false=-1, indeterminate=0.5, no response=0
reports = np.array([[  1,  1, -1,  0],
                    [  1, -1, -1, -1],
                    [  1,  1, -1, -1],
                    [  1,  1,  1, -1],
                    [  0, -1,  1,  1],
                    [ -1, -1,  1,  1]])
reports = np.array([[  1,  1, -1,  1],
                    [  1, -1, -1, -1],
                    [  1,  1, -1, -1],
                    [  1,  1,  1, -1],
                    [  1, -1,  1,  1],
                    [ -1, -1,  1,  1]])
reputation = [2, 10, 4, 2, 7, 1]

# num_voters = 39
# num_events = 39
# reports = np.random.randint(-1, 2, (num_voters, num_events))
# reputation = np.random.randint(1, 100, num_voters)

def BR(string): # bright red
    return "\033[1;31m" + str(string) + "\033[0m"

def BB(string): # bright blue
    return Fore.BLUE + Style.BRIGHT + str(string) + Style.RESET_ALL

def BG(string): # bright green
    return Fore.GREEN + Style.BRIGHT + str(string) + Style.RESET_ALL

def blocky(*strings, **kwds):
    colored = kwds.get("colored", True)
    width = kwds.get("width", 108)
    bound = width*"#"
    fmt = "#{:^%d}#" % (width - 2)
    lines = [bound]
    for string in strings:
        lines.append(fmt.format(string))
    lines.append(bound)
    lines = "\n".join(lines)
    if colored:
        lines = BR(lines)
    return lines

def fix(x):
    return int(x * 0x10000000000000000)

def unfix(x):
    return x / 0x10000000000000000

def test_contract(contract):
    s = t.state()
    filename = contract + ".se"
    print BB("Testing contract:"), BG(filename)
    c = s.contract(filename)
    if contract == "dot":
        num_signals = 10   # columns
        num_samples = 5    # rows
        data = (np.random.rand(num_samples, num_signals) * 10).astype(int)
        for i in range(num_signals):
            for j in range(num_signals):
                expected = np.dot(data[:,i], data[:,j])
                actual = s.send(t.k0, c, 0, funid=0, abi=(list(data[:,i]),))
                try:
                    assert(actual - expected < tolerance)
                except:
                    print(actual)
    elif contract == "mean":
        num_signals = 10      # columns
        num_samples = 5       # rows
        data = (np.random.rand(num_samples, num_signals) * 10).astype(int)
        expected = np.mean(data, 0)
        for i in range(num_signals):
            result = s.send(t.k0, c, 0, funid=0, abi=(list(data[:,i]),))
            actual = unfix(result[0])
            try:
                assert(actual - expected[i] < tolerance)
            except:
                print(actual)
    elif contract == "interpolate":
        result = s.send(t.k0, c, 0, funid=0, abi=[])
        actual = map(unfix, result)
        expected = [0.94736842105263164, 0.30769230769230776, 0.38461538461538469, 0.33333333333333337]
        try:
            assert((np.asarray(actual) - np.asarray(expected) < tolerance).all())
        except:
            print(actual)
    elif contract == "../consensus":
        num_voters = len(reputation)
        num_events = len(reports[0])
        v_size = len(reports.flatten())

        reputation_fixed = map(fix, reputation)
        reports_fixed = map(fix, reports.flatten())

        # tx 1: consensus()
        result = s.send(t.k0, c, 0,
                        funid=0,
                        abi=[reports_fixed, reputation_fixed, max_iterations])

        result = np.array(result)
        weighted_centered_data = result[0:v_size]
        votes_filled = result[v_size:(2*v_size)]
        votes_mask = result[(2*v_size):(3*v_size)]

        # print(pd.DataFrame({
        #     'result': weighted_centered_data,
        #     'base 16': map(hex, weighted_centered_data),
        #     'base 2^64': map(unfix, weighted_centered_data),
        # }))

        # print(pd.DataFrame({
        #     'result': votes_filled,
        #     'base 16': map(hex, votes_filled),
        #     'base 2^64': map(unfix, votes_filled),
        # }))

        # pca()
        s = t.state()
        c = s.contract(filename)
        scores = s.send(t.k0, c, 0,
                        funid=1,
                        abi=[weighted_centered_data.tolist(),
                             reputation_fixed,
                             num_voters,
                             num_events,
                             max_iterations])

        # consensus2()
        s = t.state()
        c = s.contract(filename)
        result = s.send(t.k0, c, 0,
                        funid=2,
                        abi=[reputation_fixed,
                             scores,
                             votes_filled.tolist(),
                             votes_mask.tolist(),
                             num_voters,
                             num_events])

        print(pd.DataFrame({
            'result': result,
            'base 16': map(hex, result),
            'base 2^64': map(unfix, result),
        }))

    elif contract == "../consensus-readable":
        result = s.send(t.k0, c, 0,
                        funid=0,
                        abi=[map(fix, reports.flatten()), map(fix, reputation), max_iterations])

        print(pd.DataFrame({
            'result': result,
            'base 16': map(hex, result),
            'base 2^64': map(unfix, result),
        }))

    else:
        result = s.send(t.k0, c, 0, funid=0, abi=[])
        try:
            assert(result == [1])
        except:
            try:
                assert(map(unfix, result) == [1])
            except:
                print(pd.DataFrame({
                    'result': result,
                    'base 16': map(hex, result),
                    'base 2^64': map(unfix, result),
                }))

def main():
    global s
    print BR("Forming new test genesis block")
    s = t.state()
    contracts = [
        # "sum",
        # "mean",
        # "normalize",
        # "dot",
        # "outer",
        # "multiply",
        # "kron",
        # "hadamard",
        # "transpose",
        # "diag",
        # "isnan",
        # "mask",
        # "any",
        "catch",
        # "get_weight",
        # "interpolate",
        # "fixedpoint",
        "../consensus", 
        "../consensus-readable",
    ]
    for contract in contracts:
        test_contract(contract)

if __name__ == "__main__":
    main()
