#!/usr/bin/env 

import argparse
import pickle
from time import time

from rdflib import Graph
from rdflib.util import guess_format

from sequential import validate


if __name__ == "__main__":
    timestamp = int(time())

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--constraints", help="Constraints to validate against (.pkl)",
            required=True)
    parser.add_argument("-d", "--max_depth", help="Maximum depth to validate",
            default=0)
    parser.add_argument("-i", "--input", help="One or more RDF-encoded graphs",
            required=True, nargs='+')
    args = parser.parse_args()

    # load graph(s)
    print("importing graphs... ")
    g = Graph()
    for gf in args.input:
        g.parse(gf, format=guess_format(gf))

    # load constraints
    generation_forest = None
    print("importing constraints... ")
    with open(args.constraints, 'rb') as cf:
        generation_forest = pickle.load(cf)

    # validate
    print("validating data... ")
    h = validate(g, generation_forest, args.max_depth)

    # store results
    print("storing results... ")
    h.serialize("./constraint_violations.nt", format="nt")
