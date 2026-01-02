"""
Voter ID Laws & Welfare Benefits Visualization Pipeline
========================================================

This pipeline generates narrative-driven visualizations showing the relationship
between state voter ID policies and welfare benefit availability.

Usage:
    python src/main.py

Outputs:
    - output/comparison_chart.png  (primary bar chart, 300 DPI)
    - output/comparison_chart.svg  (vector version)
    - output/strip_plot.html       (interactive distribution plot)
    - output/choropleth_map.html   (interactive US map)
    - output/summary_narrative.txt (key findings in plain text)
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from prepare_data import load_and_prepare
from stats import generate_narrative
from visualize import create_all_visualizations


def main():
    """Run the complete visualization pipeline."""
    print("=" * 60)
    print("VOTER ID & WELFARE BENEFITS VISUALIZATION PIPELINE")
    print("=" * 60)

    # Setup paths
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Load and prepare data
    print("\n[1/3] Loading and preparing data...")
    df = load_and_prepare()
    print(f"      Loaded {len(df)} jurisdictions")
    print(f"      - No Effective ID Requirement: {(df['no_effective_id'] == 1).sum()} states")
    print(f"      - ID Verification Required: {(df['no_effective_id'] == 0).sum()} states")

    # Step 2: Generate statistical narrative
    print("\n[2/3] Generating statistical analysis...")
    narrative = generate_narrative(df)

    # Save narrative
    narrative_path = output_dir / "summary_narrative.txt"
    with open(narrative_path, 'w') as f:
        f.write(narrative)
    print(f"      Saved: {narrative_path}")

    # Step 3: Create visualizations
    print("\n[3/3] Creating visualizations...")
    create_all_visualizations(df, output_dir)

    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\nOutputs saved to: {output_dir.absolute()}")
    print("\nFiles generated:")
    for f in sorted(output_dir.iterdir()):
        size = f.stat().st_size
        print(f"  - {f.name} ({size:,} bytes)")

    print("\n" + "=" * 60)
    print("KEY FINDING PREVIEW")
    print("=" * 60)
    # Print just the headline finding
    no_id_avg = df[df['no_effective_id'] == 1]['welfare_score'].mean()
    id_req_avg = df[df['no_effective_id'] == 0]['welfare_score'].mean()
    multiplier = no_id_avg / id_req_avg
    print(f"\nStates with no effective ID requirement offer {multiplier:.1f}x more")
    print(f"welfare benefits on average ({no_id_avg:.1f} vs {id_req_avg:.1f} out of 4).")


if __name__ == "__main__":
    main()
