# Validator for Multimodal Knowledge Graph Functional Dependencies

Validate any (RDF) Knowledge Graph against a set of Multimodal Knowledge Graph Functional Dependencies (MKGFD). Outputs a set of reification triples which flag candidate violations:

    _:<bnode> a rdf.Statement;
                rdf.subject <subject>;
                rdf.predicate <predicate>;
                rdf.object <object>;
                rdfs.comment "Constraint Violation (p = <probability>) on: <constraint>"@en .

## Usage

    run_mp.py [-h] -c CONSTRAINTS [-d MAX_DEPTH] -i INPUT [INPUT ...]
                     [-n NPROC] [-p MIN_PROB] [--test]

    optional arguments:
      -h, --help            show this help message and exit
      -c CONSTRAINTS, --constraints CONSTRAINTS
                            Constraints to validate against (.pkl)
      -d MAX_DEPTH, --max_depth MAX_DEPTH
                            Maximum depth to validate
      -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                            One or more RDF-encoded graphs
      -n NPROC, --nproc NPROC
                            Number of cores to utilize
      -p MIN_PROB, --min_prob MIN_PROB
                            Minimum probability to consider
      --test                Dry run without saving results

## Generating Knowledge Graph Functional Dependencies

See https://gitlab.com/wxwilcke/mkgfd  
