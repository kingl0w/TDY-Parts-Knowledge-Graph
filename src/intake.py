import csv
import sys
from validate_csv import validate_all
from pathlib import Path
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, XSD

ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = ROOT / "data" / "csv"
OUT = ROOT / "data" / "catalog.ttl"
TDY = Namespace("https://tdytrading.example/parts#")


def add_psus(g, rows):
    for row in rows:
        part = TDY[row["id"]]
        g.add((part, RDF.type, TDY.PSU))
        g.add((part, TDY.wattage, Literal(int(row["wattage"]), datatype=XSD.integer)))


def add_cpus(g, rows):
    for row in rows:
        part = TDY[row["id"]]
        g.add((part, RDF.type, TDY.CPU))
        g.add((part, TDY.socket, Literal(row["socket"])))
        g.add((part, TDY.ramGen, Literal(row["ramGen"])))
        g.add((part, TDY.draw, Literal(int(row["draw"]), datatype=XSD.integer)))


def add_motherboards(g, rows):
    for row in rows:
        part = TDY[row["id"]]
        g.add((part, RDF.type, TDY.Motherboard))
        g.add((part, TDY.socket, Literal(row["socket"])))
        g.add((part, TDY.ramGen, Literal(row["ramGen"])))
        g.add((part, TDY.formFactor, Literal(row["formFactor"])))
        g.add((part, TDY.interface, Literal(row["interface"])))


def add_gpus(g, rows):
    for row in rows:
        part = TDY[row["id"]]
        g.add((part, RDF.type, TDY.GPU))
        g.add((part, TDY.lengthMm, Literal(int(row["lengthMm"]), datatype=XSD.integer)))
        g.add((part, TDY.draw, Literal(int(row["draw"]), datatype=XSD.integer)))
        g.add((part, TDY.recommendedPsu, Literal(int(row["recommendedPsu"]), datatype=XSD.integer)))


def add_ram(g, rows):
    for row in rows:
        part = TDY[row["id"]]
        g.add((part, RDF.type, TDY.RAM))
        g.add((part, TDY.ramGen, Literal(row["ramGen"])))


def add_storage(g, rows):
    for row in rows:
        part = TDY[row["id"]]
        g.add((part, RDF.type, TDY.Storage))
        g.add((part, TDY.interface, Literal(row["interface"])))


def add_cases(g, rows):
    for row in rows:
        part = TDY[row["id"]]
        g.add((part, RDF.type, TDY.Case))
        for ff in row["acceptsFormFactor"].split(";"):
            ff = ff.strip()
            if ff:
                g.add((part, TDY.acceptsFormFactor, Literal(ff)))
        g.add((part, TDY.maxGpuMm, Literal(int(row["maxGpuMm"]), datatype=XSD.integer)))


def add_builds(g, rows):
    for row in rows:
        build = TDY[row["id"]]
        g.add((build, RDF.type, TDY.Build))
        for pid in row["parts"].split(";"):
            pid = pid.strip()
            if pid:
                g.add((build, TDY.hasPart, TDY[pid]))


def read_csv(name):
    with open(CSV_DIR / name, newline="") as f:
        return list(csv.DictReader(f))


def build():
    g = Graph()
    g.bind("tdy", TDY)
    add_psus(g, read_csv("psus.csv"))
    add_cpus(g, read_csv("cpus.csv"))
    add_motherboards(g, read_csv("motherboards.csv"))
    add_gpus(g, read_csv("gpus.csv"))
    add_ram(g, read_csv("ram.csv"))
    add_storage(g, read_csv("storage.csv"))
    add_cases(g, read_csv("cases.csv"))
    add_builds(g, read_csv("builds.csv"))
    return g


if __name__ == "__main__":
    errs = validate_all()
    if errs:
        print(f"{len(errs)} validation error(s), aborting:")
        for e in errs:
            print(f"  {e}")
        sys.exit(1)
    g = build()
    g.serialize(destination=OUT, format="turtle")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(g)} triples")