"""Data preparation module for voter ID and welfare analysis."""

import pandas as pd
from pathlib import Path


def load_and_prepare(data_path: str = None) -> pd.DataFrame:
    """
    Load state policy data and prepare for analysis.

    Returns DataFrame with:
    - Original columns (state, abbrev, no_id_voting, health, food, cash, eitc)
    - welfare_score: sum of all 4 benefit columns (0-4)
    - voter_id_policy: human-readable label for grouping
    """
    if data_path is None:
        data_path = Path(__file__).parent.parent / "data" / "state_policies.csv"

    df = pd.read_csv(data_path)

    # Calculate composite welfare score (0-4)
    benefit_cols = ['health', 'food', 'cash', 'eitc']
    df['welfare_score'] = df[benefit_cols].sum(axis=1)

    # Human-readable group labels
    df['voter_id_policy'] = df['no_id_voting'].map({
        1: 'No ID Required',
        0: 'ID Required'
    })

    return df


def get_group_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Get summary statistics by voter ID policy group."""
    benefit_cols = ['health', 'food', 'cash', 'eitc']

    summary = df.groupby('voter_id_policy').agg({
        'state': 'count',
        'welfare_score': ['mean', 'median', 'std'],
        **{col: 'sum' for col in benefit_cols}
    })

    # Flatten column names
    summary.columns = ['_'.join(col).strip('_') for col in summary.columns]
    summary = summary.rename(columns={'state_count': 'n_states'})

    return summary


if __name__ == "__main__":
    df = load_and_prepare()
    print(f"Loaded {len(df)} jurisdictions")
    print(f"\nNo ID Required: {(df['no_id_voting'] == 1).sum()} states")
    print(f"ID Required: {(df['no_id_voting'] == 0).sum()} states")
    print(f"\nWelfare score distribution:")
    print(df['welfare_score'].value_counts().sort_index())
