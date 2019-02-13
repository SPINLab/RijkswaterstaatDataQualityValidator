#! /usr/bin/env python

from rdflib import BNode, Graph, Literal, RDF, RDFS

from pgkgc.cache import Cache
from pgkgc.structures import IdentityAssertion, DataTypeVariable, ObjectTypeVariable, TypeVariable


def validate(g, generation_forest, max_depth):
    cache = Cache(g)
    h = Graph()

    violations = set()
    for t in generation_forest.types():
        tree = generation_forest.get_tree(t)

        for clause in tree.get(depth=0):
            domain = g.subjects(RDF.type, t)
            violations |= validate_recursion(clause,
                                             domain,
                                             cache,
                                             max_depth)

    for s, p, o in violations:
        flag_triple(h, s, p, o)

    return h

def validate_recursion(clause, parent_domain, cache, depth):
    if depth < 0:
        return set()

    # reduce search space by constraining parent domain
    domain = generate_domain(cache.predicate_map,
                             cache.object_type_map,
                             cache.data_type_map,
                             clause.body,
                             clause.body.identity,
                             parent_domain)

    violations = check_violations(cache.predicate_map,
                                  cache.object_type_map,
                                  cache.data_type_map,
                                  clause.head,
                                  domain)

    for child in clause.children:
        violations |= validate_recursion(child,
                                         domain,
                                         cache,
                                         depth-1)

    return violations

def check_violations(predicate_map,
                     object_type_map,
                     data_type_map,
                     assertion,
                     assertion_domain):
    """ Check whether a clause assertion holds within a domain of entities

        Returns a set of violations
    """
    violations = set()
    if not isinstance(assertion.rhs, TypeVariable):
        # either an entity or literal
        for entity in assertion_domain:
            if assertion.rhs not in predicate_map[assertion.predicate]['forwards'][entity]:
                # P(e, u) does not hold
                violations.add(entity)
    
    elif isinstance(assertion.rhs, ObjectTypeVariable):
        for entity in assertion_domain:
            for resource in predicate_map[assertion.predicate]['forwards'][entity]:
                if object_type_map['object-to-type'][resource] != assertion.rhs.type:
                    # P(e, ?) with object type(?, t) does not hold
                    violations.add(entity)

    elif isinstance(assertion.rhs, DataTypeVariable):
        for entity in assertion_domain:
            for resource in predicate_map[assertion.predicate]['forwards'][entity]:
                if data_type_map['object-to-type'][resource] != assertion.rhs.type:
                    # P(e, ?) with data type(?, t) does not hold
                    violations.add(entity)

    return violations


def generate_domain(predicate_map,
                    object_type_map,
                    data_type_map,
                    context,
                    assertion,
                    assertion_domain):
    """ Generate the domain given a graph context

    Returns a set of entities
    """
    # no need to continue if we are a pendant incident (optimization)
    if len(context.connections[assertion]) <= 0:
        if isinstance(assertion, IdentityAssertion):
            return assertion_domain

        assertion_domain_updated = set()
        if not isinstance(assertion.rhs, TypeVariable):
            # either an entity or literal
            for entity in assertion_domain:
                if assertion.rhs in predicate_map[assertion.predicate]['forwards'][entity]:
                    # P(e, u) holds
                    assertion_domain_updated.add(entity)
        elif isinstance(assertion.rhs, ObjectTypeVariable):
            for entity in assertion_domain:
                for resource in predicate_map[assertion.predicate]['forwards'][entity]:
                    if object_type_map['object-to-type'][resource] == assertion.rhs.type:
                        # P(e, ?) with object type(?, t) holds
                        assertion_domain_updated.add(entity)
        elif isinstance(assertion.rhs, DataTypeVariable):
            for entity in assertion_domain:
                for resource in predicate_map[assertion.predicate]['forwards'][entity]:
                    if data_type_map['object-to-type'][resource] == assertion.rhs.type:
                        # P(e, ?) with data type(?, t) holds
                        assertion_domain_updated.add(entity)

        return assertion_domain_updated

    # retrieve range based on assertion's domain
    if isinstance(assertion, IdentityAssertion):
        assertion_range = assertion_domain
    else:  # type is Clause.Assertion with ObjectTypeVariable as rhs
        assertion_range = set()
        for entity in assertion_domain:
            for resource in predicate_map[assertion.predicate]['forwards'][entity]:
                if object_type_map['object-to-type'][resource] is assertion.rhs.type:
                    assertion_range.add(resource)

    # update range based on connected assertions' domains (optimization)
    for connection in context.connections[assertion]:
        assertion_range &= frozenset(predicate_map[connection.predicate]['forwards'].keys())

    # update range based on connected assertions' returned updated domains
    # search space is reduced after each returned update
    connection_domain = assertion_range  # only for readability
    for connection in context.connections[assertion]:
        range_update = generate_domain(predicate_map,
                                       object_type_map,
                                       data_type_map,
                                       context,
                                       connection,
                                       connection_domain)

        assertion_range &= range_update

    # update domain based on updated range
    if isinstance(assertion, IdentityAssertion):
        return assertion_range

    assertion_domain_updated = set()
    for resource in assertion_range:
        domain_update = predicate_map[assertion.predicate]['backwards'][resource]
        assertion_domain_updated |= domain_update

    return assertion_domain_updated

def flag_triple(h, s, p, o):
    bnode = BNode()

    h.add((bnode, RDF.type, RDF.Statement))

    h.add((bnode, RDF.subject, s))
    h.add((bnode, RDF.predicate, p))
    h.add((bnode, RDF.object, o))

    comment = Literal("Constraint Violation", lang="en")
    h.add((bnode, RDFS.comment, comment))
