#! /usr/bin/env python

from math import ceil
from multiprocessing import Pool
from time import process_time

from rdflib import Graph, RDF

from mkgfd.cache import Cache
from sequential import flag_triple, validate_recursion


def validate_mp(nproc, g, generation_forest, max_depth, min_domain_probability):
    cache = Cache(g)
    h = Graph()

    t0 = process_time()
    i = 0
    with Pool(nproc) as pool:
        types = generation_forest.types()

        chunksize = ceil(len(types)/nproc)
        for depth in range(max_depth+1):
            for clause_violations in pool.imap_unordered(validate_tree,
                                                        ((t,
                                                          g,
                                                          generation_forest.get_tree(t),
                                                          depth,
                                                          min_domain_probability,
                                                          cache)
                                                         for t in types),
                                                        chunksize=chunksize if chunksize > 1 else 2):

                for clause, violations in clause_violations.items():
                    c = clause.head.rhs
                    p = clause.head.predicate
                    prob = clause.domain_probability
                    for e in violations:
                        # simplify by assuming a single object per s,p pair
                        o = list(cache.predicate_map[p]['forwards'][e])[0]

                        flag_triple(h, prob, c, e, p, o)
                        i += 1

    duration = process_time()-t0
    print('found {} violations in {:0.3f}s'.format(i, duration))

    return h

def validate_tree(inputs):
    t, g, tree, depth, min_domain_probability, cache = inputs

    # root clauses have all members of type t as domain 
    domain = set(g.subjects(RDF.type, t)) if depth <= 0 else set()

    violations = dict()
    for clause in tree.get(depth=depth):
        if clause.domain_probability < min_domain_probability:
            # if this one fails the threshold than his derivatives will too
            continue

        if depth <= 0 and (clause.parent._satisfy_body is None
                           or len(clause.parent._satisfy_body) <= 0):
            # set starting point if previously cleared
            clause.parent._satisfy_body = domain

        violations.update(validate_recursion(clause,
                                             min_domain_probability,
                                             cache))

    return violations
