import polars as pl


def polars_standardize_fasta(
    df: pl.DataFrame, fasta_col: str = "fasta", out_col: str = "fasta"
) -> pl.DataFrame:
    """
    Remove spaces and make it uppercase of a Polars column.
    """
    df = df.with_columns(
        pl.col(fasta_col)
        .str.to_uppercase()
        .str.replace_all("\n", "")
        .str.replace_all(" ", "")
        .alias(out_col)
    )

    return df
