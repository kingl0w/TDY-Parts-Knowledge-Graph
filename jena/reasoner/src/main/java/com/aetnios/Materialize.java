package com.aetnios;

import org.semanticweb.HermiT.ReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.formats.TurtleDocumentFormat;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.OWLReasoner;

import java.io.File;

public class Materialize {
    static final String NS = "https://tdytrading.example/parts#";

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: Materialize <merged.ttl> <out-inferred.ttl>");
            System.exit(1);
        }

        OWLOntologyManager mgr = OWLManager.createOWLOntologyManager();
        OWLDataFactory df = mgr.getOWLDataFactory();

        // schema + data parsed together so properties are typed correctly
        OWLOntology onto = mgr.loadOntologyFromOntologyDocument(new File(args[0]));

        long opa = onto.getAxioms(AxiomType.OBJECT_PROPERTY_ASSERTION).size();
        System.out.println("object property assertions in input: " + opa);

        OWLReasoner reasoner = new ReasonerFactory().createReasoner(onto);
        System.out.println("consistent: " + reasoner.isConsistent());

        OWLOntology inferred = mgr.createOntology();

        // class memberships: ask the reasoner who is in each named class
        for (OWLClass c : onto.getClassesInSignature()) {
            if (c.isOWLThing() || c.isOWLNothing()) continue;
            for (OWLNamedIndividual i : reasoner.getInstances(c, false).getFlattened()) {
                mgr.addAxiom(inferred, df.getOWLClassAssertionAxiom(c, i));
            }
        }

        // object property links: ask the reasoner for all values of each property
        for (OWLNamedIndividual i : onto.getIndividualsInSignature()) {
            for (OWLObjectProperty op : onto.getObjectPropertiesInSignature()) {
                for (OWLNamedIndividual v : reasoner.getObjectPropertyValues(i, op).getFlattened()) {
                    mgr.addAxiom(inferred, df.getOWLObjectPropertyAssertionAxiom(op, i, v));
                }
            }
        }

        mgr.saveOntology(inferred, new TurtleDocumentFormat(),
                IRI.create(new File(args[1]).toURI()));

        OWLClass mbc = df.getOWLClass(IRI.create(NS + "MotherboardCompatible"));
        System.out.println("MotherboardCompatible instances: "
                + reasoner.getInstances(mbc, false).getFlattened());

        OWLObjectProperty offers = df.getOWLObjectProperty(IRI.create(NS + "offersCompatible"));
        for (OWLNamedIndividual i : onto.getIndividualsInSignature()) {
            var vals = reasoner.getObjectPropertyValues(i, offers).getFlattened();
            if (!vals.isEmpty()) System.out.println(i.getIRI() + " offersCompatible " + vals);
        }

        System.out.println("inferred axioms written: " + inferred.getAxiomCount());
        reasoner.dispose();
    }
}
