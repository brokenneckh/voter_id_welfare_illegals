"""Data preparation module for voter ID and welfare analysis."""

import pandas as pd
from pathlib import Path


def load_and_prepare(data_path: str = None) -> pd.DataFrame:
    """
    Load state policy data and prepare for analysis.

    Returns DataFrame with:
    - Original columns (state, abbrev, id_strictness, health_children, health_adults, health_seniors, food, eitc)
    - welfare_score_adults: benefits available to illegal immigrant adults (health_adults + food + eitc, 0-3)
    - welfare_score_any: any illegal immigrant coverage (any health + food + eitc, 0-3)
    - no_effective_id: 1 if id_strictness >= 4 (tiers 4-5), else 0
    - voter_id_policy: human-readable label for grouping
    """
    if data_path is None:
        data_path = Path(__file__).parent.parent / "data" / "state_policies.csv"

    df = pd.read_csv(data_path)

    # Calculate welfare score for illegal immigrant ADULTS specifically (0-3)
    # This is the most defensible metric: health coverage for adults + food + EITC
    df['welfare_score_adults'] = df['health_adults'] + df['food'] + df['eitc']

    # Calculate welfare score for ANY illegal immigrant (0-3)
    # Counts if state has any health coverage (children, adults, or seniors)
    df['has_any_health'] = ((df['health_children'] == 1) |
                            (df['health_adults'] == 1) |
                            (df['health_seniors'] == 1)).astype(int)
    df['welfare_score_any'] = df['has_any_health'] + df['food'] + df['eitc']

    # Legacy welfare_score for backwards compatibility (uses adults score)
    df['welfare_score'] = df['welfare_score_adults']

    # 2-tier classification based on functional outcome (primary analysis)
    # Tiers 4-5: No effective ID requirement (affidavit or no document)
    # Tiers 1-3: ID verification required
    df['no_effective_id'] = (df['id_strictness'] >= 4).astype(int)

    # Human-readable group labels (using 2-tier functional classification)
    df['voter_id_policy'] = df['no_effective_id'].map({
        1: 'No ID Required',
        0: 'ID Required'
    })

    return df


def get_group_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Get summary statistics by voter ID policy group."""
    benefit_cols = ['health_children', 'health_adults', 'health_seniors', 'food', 'eitc']

    summary = df.groupby('voter_id_policy').agg({
        'state': 'count',
        'welfare_score_adults': ['mean', 'median', 'std'],
        'welfare_score_any': ['mean', 'median', 'std'],
        **{col: 'sum' for col in benefit_cols}
    })

    # Flatten column names
    summary.columns = ['_'.join(col).strip('_') for col in summary.columns]
    summary = summary.rename(columns={'state_count': 'n_states'})

    return summary


if __name__ == "__main__":
    df = load_and_prepare()
    print(f"Loaded {len(df)} jurisdictions")
    print(f"\nNo Effective ID (tiers 4-5): {(df['no_effective_id'] == 1).sum()} states")
    print(f"ID Required (tiers 1-3): {(df['no_effective_id'] == 0).sum()} states")
    print(f"\nWelfare score (adults) distribution:")
    print(df['welfare_score_adults'].value_counts().sort_index())
    print(f"\nWelfare score (any) distribution:")
    print(df['welfare_score_any'].value_counts().sort_index())
