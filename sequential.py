#! /usr/bin/env python

from rdflib import BNode, Graph, Literal, RDF, RDFS

from pgkgc.cache import Cache
from pgkgc.metrics import confidence_of as compute_satisfied
from pgkgc.metrics import support_of as compute_domain


def validate(g, generation_forest, max_depth):
    cache = Cache(g)
    h = Graph()

    violations = set()
    for depth in range(max_depth):
        for t in generation_forest.types():
            # root clauses have all members of type t as domain 
            domain = set(g.subjects(RDF.type, t)) if depth <= 0 else set()

            tree = generation_forest.get_tree(t)
            for clause in tree.get(depth=depth):
                if depth <= 0 and clause.parent._satisfy_body is None:
                    # set starting point if previously cleared
                    clause.parent._satisfy_body = domain

                violations |= validate_recursion(clause, cache)

    for s, p, o in violations:
        flag_triple(h, s, p, o)

    return h

def validate_recursion(clause, cache):
    if clause._satisfy_body is None:
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
    violations = clause._satisfy_body - satisfied

    for child in clause.children:
        violations |= validate_recursion(child, cache)

    return violations

def flag_triple(h, s, p, o):
    bnode = BNode()

    h.add((bnode, RDF.type, RDF.Statement))

    h.add((bnode, RDF.subject, s))
    h.add((bnode, RDF.predicate, p))
    h.add((bnode, RDF.object, o))

    comment = Literal("Constraint Violation", lang="en")
    h.add((bnode, RDFS.comment, comment))
