"""Pydantic models for Apache Jena (Fuseki) operations."""

from pydantic import BaseModel, Field


class SparqlRequest(BaseModel):
    """A SPARQL query or update against a Fuseki dataset."""

    dataset: str = Field(description="Fuseki dataset name, e.g. 'ds'.")
    sparql: str = Field(description="SPARQL query or update string.")
    accept: str = Field(
        default="application/sparql-results+json",
        description="Accept header for query results.",
    )


class DatasetSpec(BaseModel):
    """A Fuseki dataset to create or address."""

    name: str = Field(description="Dataset name.")
    db_type: str = Field(
        default="tdb2", description="Storage type: tdb2, tdb, or mem."
    )
