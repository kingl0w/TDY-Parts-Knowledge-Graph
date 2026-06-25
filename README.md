# Tdy-parts-graph

An old personal project I put together to better understand semantic graphs, a tiny knowledge graph for a used computer parts inventory. It shows the full loop:
model the domain in owl, constrain it with shacl, load the data, run rdfs reasoning,
validate, and query.

## Layout

```
ontology/parts.ttl          owl/rdfs ontology
shapes/listing-shapes.ttl   shacl shapes (the data quality rules)
data/inventory.ttl          demo dataset: clean records plus deliberately broken ones
data/valid.ttl              fixture: only conforming records
data/invalid.ttl            fixture: only the six broken records
src/validate.py             loads everything, reasons, validates, queries
tests/test_shapes.py        pytest suite asserting exact validation behavior
```

## Run it

```
pip install -r requirements.txt
python src/validate.py
pytest -q
```

`python src/validate.py` runs the demo dataset (`data/inventory.ttl`), which contains
six deliberately broken records, so it reports `conforms: False`, prints the violations,
and exits 1. that is the point: the same script is the ci gate in
`.github/workflows/validate.yml`. swap in clean data and it exits 0.

`pytest -q` runs against the split fixtures: it asserts `data/valid.ttl` conforms,
`data/invalid.ttl` does not, the exact violation count, and that specific bad records
get flagged. ci runs both.

## The model

Components (cpu, gpu, ram, storage) are subclasses of `Component`, so an rdfs reasoner
infers any cpu is also a component. a `Listing` sells one component, has one condition
from a controlled vocabulary (new, used, refurb, forparts), and is listed by one seller.
a `GradedListing` adds a 1..10 grade and is never sold for parts.
