#! /usr/bin/env python

from math import ceil
from multiprocessing import Pool

from rdflib import Graph, RDF

from pgkgc.cache import Cache
from sequential import flag_triple, validate_recursion


def validate_mp(nproc, g, generation_forest, max_depth):
    cache = Cache(g)
    h = Graph()

    with Pool(nproc) as pool:
        types = generation_forest.types()

        chunksize = ceil(len(types)/nproc)
        for depth in range(max_depth):
            for s, p, o in pool.imap_unordered(validate_tree,
                                               ((t, g, generation_forest, depth, cache) for t in types),
                                               chunksize=chunksize if chunksize > 1 else 2):
                flag_triple(h, s, p, o)

    return h

def validate_tree(inputs):
    t, g, generation_forest, depth, cache = inputs

    # root clauses have all members of type t as domain 
    domain = set(g.subjects(RDF.type, t)) if depth <= 0 else set()

    tree = generation_forest.get_tree(t)
    for clause in tree.get(depth=depth):
        if depth <= 0 and clause.parent._satisfy_body is None:
            # set starting point if previously cleared
            clause.parent._satisfy_body = domain

        for violation in validate_recursion(clause, cache):
            yield violation
