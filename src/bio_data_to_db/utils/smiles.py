from functools import cache

import polars as pl
from rdkit import Chem
from tqdm import tqdm

from .polars import w_pbar


@cache
def canonical_smiles_wo_salt(smiles: str) -> str | None:
    """
    Get the canonical SMILES without salt from the input SMILES.

    Salt is a short part separated by "." in the SMILES.
    Shared function with dti-pytorch
    """
    m = Chem.MolFromSmiles(smiles)
    if m is not None:
        canonical_smiles = Chem.MolToSmiles(m, isomericSmiles=True, canonical=True)
        split_smi = canonical_smiles.split(".")
        if len(split_smi) > 1:
            smiles_wo_salt = max(split_smi, key=len)
            if Chem.MolFromSmiles(smiles_wo_salt) is None:
                smiles_wo_salt = None
        else:
            smiles_wo_salt = split_smi[0]
    else:
        smiles_wo_salt = None
    return smiles_wo_salt


def polars_canonical_smiles_wo_salt(
    df: pl.DataFrame,
    *,
    smiles_col: str = "smiles",
    out_col: str = "canonical_smiles_wo_salt",
) -> pl.DataFrame:
    """
    Apply canonical_smiles_wo_salt on the DataFrame with tqdm.
    """
    with tqdm(
        total=df.shape[0], desc="Converting smiles to canonical smiles without salt"
    ) as pbar:
        df = df.with_columns(
            pl.col(smiles_col)
            .map_elements(w_pbar(pbar, canonical_smiles_wo_salt), return_dtype=pl.Utf8)
            .alias(out_col),
        )

    return df
