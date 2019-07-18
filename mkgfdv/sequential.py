#! /usr/bin/env python

from time import process_time

from rdflib import BNode, Graph, Literal, RDF, RDFS

from mkgfd.cache import Cache
from mkgfd.metrics import confidence_of as compute_satisfied
from mkgfd.metrics import support_of as compute_domain


def validate(g, generation_forest, max_depth, min_domain_probability):
    cache = Cache(g)
    h = Graph()

    t0 = process_time()
    i = 0
    for depth in range(max_depth+1):
        for t in generation_forest.types():
            # root clauses have all members of type t as domain 
            domain = set(g.subjects(RDF.type, t)) if depth <= 0 else set()

            tree = generation_forest.get_tree(t)
            for clause in tree.get(depth=depth):
                if clause.domain_probability < min_domain_probability:
                    # if this one fails the threshold than his derivatives will too
                    continue

                if depth <= 0 and (clause.parent._satisfy_body is None
                                   or len(clause.parent._satisfy_body) <= 0):
                    # set starting point if previously cleared
                    clause.parent._satisfy_body = domain

                for violated_clause, violations in validate_recursion(clause,
                                                                      min_domain_probability,
                                                                      cache).items():
                    c = violated_clause.head.rhs
                    p = violated_clause.head.predicate
                    prob = violated_clause.domain_probability
                    for e in violations:
                        # simplify by assuming a single object per s,p pair
                        o = list(cache.predicate_map[p]['forwards'][e])[0]
                        flag_triple(h, prob, c, e, p, o)

                        i += 1

    duration = process_time()-t0
    print('found {} violations in {:0.3f}s'.format(i, duration))

    return h

def validate_recursion(clause, min_domain_probability, cache):
    clause_violations = dict()
    if clause.domain_probability < min_domain_probability:
        # if this one fails the threshold than his derivatives will too
        return clause_violations

    if clause._satisfy_body is None or len(clause._satisfy_body) <= 0:
        # compute domain from that of parent to reduce search space
        _, domain = compute_domain(cache.predicate_map,
                                   cache.object_type_map,
                                   cache.data_type_map,
                                   clause.body,
                                   clause.body.identity,
                                   clause.parent._satisfy_body,
                                   min_support=-1)

        clause._satisfy_body = domain


    _, satisfied = compute_satisfied(cache.predicate_map,
                                     cache.object_type_map,
                                     cache.data_type_map,
                                     clause.head,
                                     clause._satisfy_body)

    # domain entities that don't satisfy are violations
    clause_violations[clause] = clause._satisfy_body - satisfied

    for child in clause.children:
        clause_violations.update(validate_recursion(child,
                                                    min_domain_probability,
                                                    cache))

    return clause_violations

def flag_triple(h, prob, c, s, p, o):
    bnode = BNode()

    h.add((bnode, RDF.type, RDF.Statement))

    h.add((bnode, RDF.subject, s))
    h.add((bnode, RDF.predicate, p))
    h.add((bnode, RDF.object, o))

    comment = Literal("Constraint Violation (p = {:0.2f}): {}".format(prob, str(c)), lang="en")
    h.add((bnode, RDFS.comment, comment))
