"""Pydantic return types for clamol MCP tools.

FastMCP auto-generates JSON Schema for these so the model receives structured
data instead of stringified blobs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ObjectInfo(BaseModel):
    name: str
    n_atoms: int
    chains: list[str]


class SelectionInfo(BaseModel):
    name: str
    n_atoms: int


class AlignResult(BaseModel):
    """Result of cmd.align / cmd.super / cmd.cealign.

    PyMOL returns a 7-tuple [rmsd_refined, n_atoms, n_cycles, rmsd_init, n_init,
    raw_rmsd, n_raw]. cealign returns a dict in newer PyMOLs; we normalize.
    """

    rmsd: float = Field(description="Refined RMSD in Angstroms after outlier rejection cycles")
    n_atoms: int = Field(description="Number of atoms in the refined alignment")
    n_cycles: int = Field(default=0, description="Number of outlier-rejection cycles")
    rmsd_initial: float = Field(default=0.0, description="RMSD before refinement")
    n_atoms_initial: int = Field(default=0, description="Atoms in the initial alignment")


class AtomCoord(BaseModel):
    chain: str
    resi: str
    resn: str
    name: str
    element: str
    x: float
    y: float
    z: float
