# tdy-parts-graph

A small knowledge graph for a used computer parts inventory, built twice over the same ontology: once in Python for modeling and validation, once on the JVM (Apache Jena + Fuseki) as a served, persistent, reasoning endpoint that stands up in one `docker compose up`.

The point of the project is the thing a normal database can't do: it answers questions about facts nobody typed in. You assert that a motherboard fits a CPU; the graph derives that the CPU fits the motherboard, and that a listing selling that CPU offers something compatible with a motherboard. Those facts are computed by an OWL reasoner, not stored by hand.

## What this demonstrates

- OWL/RDFS domain modeling, including a defined class and an OWL 2 property chain
- The full reasoning stack on the JVM: RDFS and OWL-rule inference live in Fuseki, full OWL DL (HermiT) materialized offline
- The engineering judgment of *which* inference runs live vs precomputed, and why
- SHACL data-quality validation, run through two engines (pySHACL and Jena) off one shapes file
- A deployable artifact: served SPARQL endpoint, persistent triplestore, containerized, one command to run

## Two implementations, one ontology

The ontology (`ontology/parts.ttl`) and data (`data/inventory.ttl`) are the single source of truth. Both stacks read the same files.

**Python** (`src/`): rdflib + owlready2 + pySHACL. Modeling, RDFS reasoning, SHACL validation, a pytest CI gate. Fast to iterate, good for getting the model right.

**Jena / Fuseki** (`jena/`): the same ontology served as infrastructure. Persistent TDB2 store, a real SPARQL endpoint over HTTP, three inference configs, an offline HermiT materializer, and a Docker build. This is the "deploy it" half.

## The derived-not-stored demo

The headline. You assert exactly one direction of compatibility:

```turtle
tdy:mobo_x1 tdy:compatibleWith tdy:cpu_x1 .
tdy:mobo_x1 tdy:compatibleWith tdy:ram_x1 .
```

Query the served endpoint for what listings offer something motherboard-compatible:

```sparql
SELECT ?listing ?x WHERE { ?listing tdy:offersCompatible ?x }
```

```
listing_1  mobo_x1
listing_2  mobo_x1
```

Nobody wrote those triples. Deriving them takes two inferences composed: `compatibleWith` is symmetric (so the CPU is compatible with the mobo, in reverse of what was asserted), and `offersCompatible` is a property chain `sells ∘ compatibleWith` (so a listing selling that CPU offers something compatible with the mobo). HermiT computes this once; the result is served as plain data with no reasoner running at query time.

The defined class `MotherboardCompatible` works the same way: `cpu_x1` and `ram_x1` are classified into it without ever being asserted as members.

## Layout

```
ontology/parts.ttl              OWL/RDFS ontology (shared)
data/inventory.ttl              served dataset (shared)
data/valid.ttl                  fixture: conforming records
data/invalid.ttl                fixture: six broken records
shapes/listing-shapes.ttl       SHACL shapes (shared by both validators)
src/validate.py                 Python: load, reason, validate, query
tests/test_shapes.py            Python: pytest CI gate

jena/reasoner/                  Maven project: OWL API + HermiT offline materializer
jena/reasoner/inferred.ttl      HermiT output, committed so the graph rebuilds without a reasoner run
jena/fuseki/tdyparts-rdfs.ttl   Fuseki config: live RDFS reasoner
jena/fuseki/tdyparts-owl.ttl    Fuseki config: live OWL-rule reasoner
jena/fuseki/tdyparts-served.ttl Fuseki config: plain, serves the materialized graph
jena/fuseki/tdyparts-docker.ttl same, with container paths
jena/Dockerfile                 multi-stage: load TDB2, then serve
docker-compose.yml              one-command standup
```

## Run it

### Jena (served endpoint, one command)

```
docker compose up -d
# wait a few seconds for Fuseki to start, then:
curl -s http://localhost:3030/tdyparts/sparql -H 'Accept: text/csv' \
  --data-urlencode 'query=PREFIX tdy: <https://tdytrading.example/parts#>
SELECT ?listing ?x WHERE { ?listing tdy:offersCompatible ?x }'
docker compose down
```

Needs only Docker. The image builds the TDB2 store from the three TTLs and serves it. No Java or Jena install required.

### Python (validate + reason locally)

```
pip install -r requirements.txt
python src/validate.py
pytest -q
```

`validate.py` runs the demo dataset and reports violations. `pytest -q` is the CI gate against the split fixtures.

### Jena, manually (no Docker)

Requires Java 21 and a local Apache Jena/Fuseki 6.1.0. The configs in `jena/fuseki/` swap the inference layer by pointing `fuseki-server --config` at the RDFS, OWL, or served file. The reasoner (`jena/reasoner/`) builds with `mvn package` and runs on Java 17, since OWL API 5.x predates Java 21. It is a build-time tool, decoupled from the Java 21 serving stack on purpose.

## The model

Components (CPU, GPU, RAM, storage, motherboard) are subclasses of `Component`, so an RDFS reasoner infers any CPU is also a component. A `Listing` sells one component, has one condition from a controlled vocabulary (new, used, refurb, forparts), and is listed by one seller. A `GradedListing` adds a 1..10 grade and is never sold for parts.

On top of that, three OWL constructs that need real reasoning:

- `compatibleWith`: a symmetric object property between components.
- `MotherboardCompatible`: a defined class, `Component and (compatibleWith some Motherboard)`. The reasoner classifies instances into it; nothing is asserted.
- `offersCompatible`: a property chain `sells ∘ compatibleWith`.

## Inference: what runs where

Three layers, placed deliberately.

- **RDFS, live in Fuseki.** Subclass and range entailment. Cheap, runs on every query. (`tdyparts-rdfs.ttl`)
- **OWL-rule, live in Fuseki.** Adds property characteristics: symmetry, inverse, transitivity. Still cheap. (`tdyparts-owl.ttl`)
- **OWL DL, materialized offline.** Jena's built-in OWL reasoner is rule-based and predates OWL 2: it does not do property chains, and its live handling of existential restrictions skolemizes invented blank-node witnesses into query results. So the heavy reasoning (HermiT, full OWL DL) runs once as a build step, writes `inferred.ttl`, and that gets loaded and served as plain triples. The served endpoint runs no reasoner. (`jena/reasoner/`, `tdyparts-served.ttl`)

This split is the design point: do the cheap, safe deductions live; precompute the expensive ones and serve the answers. It is also how this scales, since live DL reasoning inside a query endpoint does not.

## Validation (SHACL)

`shapes/listing-shapes.ttl` is validated by both pySHACL (Python) and Jena's `shacl` command (JVM), same file, same verdicts. It passes `data/valid.ttl` and flags all six broken records in `data/invalid.ttl`: negative price, condition outside the allowed set, missing seller, grade out of range, a graded listing sold for parts, and a component with no mpn.

One subtlety worth stating: SHACL validates the graph exactly as given and does no reasoning of its own. A shape requiring a listing to sell a `Component` only passes if the class hierarchy is present, so validation includes `ontology/parts.ttl` alongside the data. SHACL checks shape, the reasoner derives truth, they are separate layers.

## Notes on tooling

- Versions verified current as of the build: Apache Jena + Fuseki 6.1.0 (Java 21), HermiT via OWL API 5.1.x (Java 17).
- Openllet, the usual "OWL DL in a Jena stack" answer, was rejected: last release 2019, pinned to an old Jena, will not load in Fuseki 6. HermiT run offline through the OWL API is the maintained path.
- The Dockerfile pulls Jena from `archive.apache.org` rather than the live mirror, so the build stays reproducible after a release rolls over and the live mirror drops the old tarball.
