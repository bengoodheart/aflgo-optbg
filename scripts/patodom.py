#!/usr/bin/env python3

import argparse
import collections
import functools
import networkx as nx
from collections import defaultdict


class memoize:
    # From https://github.com/S2E/s2e-env/blob/master/s2e_env/utils/memoize.py

    def __init__(self, func):
        self._func = func
        self._cache = {}

    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            return self._func(args)

        if args in self._cache:
            return self._cache[args]

        value = self._func(*args)
        self._cache[args] = value
        return value

    def __repr__(self):
        # Return the function's docstring
        return self._func.__doc__

    def __get__(self, obj, objtype):
        # Support instance methods
        return functools.partial(self.__call__, obj)


#################################
# Get graph node name
#################################
def node_name(name):
    if is_cg:
        return "\"{%s}\"" % name
    else:
        return "\"{%s:" % name


#################################
# Find the graph node for a name
#################################
@memoize
def find_nodes(name):
    n_name = node_name(name)
    return [n for n, d in G.nodes(data=True) if n_name in d.get('label', '')]


##################################
# Find labels for graph nodes
##################################
def get_data(G, nodes):
    res = []
    for n, d in G.nodes(data=True):
        if n in nodes:
            line = d.get('label', '')
            res.append(line)
    return res


##################################
# Main function
##################################
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d',
                        '--dot',
                        type=str,
                        required=True,
                        help="Path to dot-file representing the graph.")
    parser.add_argument('-t',
                        '--targets',
                        type=str,
                        required=True,
                        help="Path to file specifying Target nodes.")
    parser.add_argument(
        '-b',
        '--bbs',
        type=str,
        required=True,
        help="Path to file specifying first BBs of each function.")
    parser.add_argument(
        '-o',
        '--out',
        type=str,
        required=True,
        help="Path to output file containing distance for each node.")

    args = parser.parse_args()

    print("\nParsing %s .." % args.dot)
    G = nx.DiGraph(nx.drawing.nx_pydot.read_dot(args.dot))
    print(nx.info(G))

    is_cg = "Name: Call graph" in nx.info(G)
    print("\nWorking in %s mode.." % ("CG" if is_cg else "CFG"))

    # Process as ControlFlowGraph
    caller = ""
    cg_distance = {}
    bb_distance = {}
    if not is_cg:
        # pato: handled by llvm pass
        pass
        # print("Adding target BBs (if any)..")
        # targets = []
        # with open(args.targets, "r") as f:
        #     for l in f.readlines():
        #         s = l.strip().split("/")
        #         line = s[len(s) - 1]
        #         for node in find_nodes(line):
        #             targets.append(node)
        #             print("Added target BB %s!" % line)

        # entry_nodes = []
        # for n, d in G.nodes(data=True):
        #     if G.in_degree(n) == 0:
        #         line = d.get('label', '')[2:-3]
        #         entry_nodes.append(n)
        # if len(entry_nodes) > 1:
        #     print("More than one entry")
        #     print("********************* " + str(entry_nodes))
        #     exit(-1)

        # print("Creating dominators..")
        # dominance = nx.immediate_dominators(G, entry_nodes[0])
        # res = set()

        # print("Calculating doms..")
        # while len(targets) > 0:
        #     target = targets.pop()
        #     print("tgt: %s" % str(target))
        #     dom = dominance[target]
        #     if dom not in res:
        #         res.add(dom)
        #         targets.append(dom)
        # print(get_data(G, res))

    # Process as CallGraph
    else:
        print("Loading targets..")
        with open(args.targets, "r") as f:
            targets = []
            for line in f.readlines():
                line = line.strip()
                for target in find_nodes(line):
                    targets.append(target)

        if (not targets and is_cg):
            print("No targets available")
            exit(0)

        print("Creating dominators..")
        entry_nodes = find_nodes('main')
        if len(entry_nodes) > 1:
            print("More than one entry")
            exit(-1)
        dominance = nx.immediate_dominators(G, entry_nodes[0])
        res = set()

        print("Calculating doms..")
        while len(targets) > 0:
            target = targets.pop()
            # print("tgt: " + target)
            dom = dominance[target]
            if dom not in res:
                res.add(dom)
                targets.append(dom)
        res = get_data(G, res)
        funcs = [r[2:-2] for r in res]

        print("Loading first BBs..")
        with open(args.bbs, "r") as f:
            f2bb = defaultdict(set)
            for line in f.readlines():
                line = line.strip()
                parts = line.split(",")
                if len(parts) < 2:
                    continue
                f2bb[parts[0]].add(parts[1])

        res = [f2bb[func] for func in funcs if len(f2bb[func]) == 1]
        print(funcs, res)

        print("Writing new targets..")
        with open(args.out, "w") as out:
            for r in res:
                out.write("%s\n" % r)