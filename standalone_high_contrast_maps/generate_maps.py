"""
Self-contained high-contrast map generator for voter ID and welfare benefits analysis.

Generates four figures showing the correlation between policies/demographics and electoral outcomes:
1. high_contrast_maps_2024.png - Voter ID vs electoral outcomes
2. welfare_high_contrast_maps_2024.png - Welfare benefits vs electoral outcomes
3. unauthorized_pop_high_contrast_maps_2024.png - Unauthorized pop vs electoral outcomes
4. unauthorized_pop_pct_high_contrast_maps_2024.png - Unauthorized pop % vs electoral outcomes
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geopandas as gpd
from matplotlib.gridspec import GridSpec
from pathlib import Path
import warnings

# Paths relative to this script
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / 'data'
OUTPUT_DIR = SCRIPT_DIR / 'output'

# High contrast colors
RED_VIVID = '#c41230'
BLUE_VIVID = '#0047ab'
GREEN_MATCH = '#2ca02c'
ORANGE_MISMATCH = '#ff7f0e'


def set_style():
    """Set consistent style matching main branch."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 11,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.edgecolor': '#333333',
        'grid.color': '#e0e0e0',
    })


def load_state_geodata():
    """Load state boundaries from local GeoJSON file."""
    geo_path = DATA_DIR / 'us_states.geojson'
    if geo_path.exists():
        gdf = gpd.read_file(geo_path)
        # Standardize to state_po column
        if 'STATEFP' in gdf.columns:
            gdf = gdf[gdf['STATEFP'].astype(int) <= 56]
            gdf = gdf.rename(columns={'STUSPS': 'state_po'})
        elif 'GEOID' in gdf.columns:
            gdf = gdf[gdf['GEOID'].astype(int) <= 56]
            if 'STUSPS' in gdf.columns:
                gdf = gdf.rename(columns={'STUSPS': 'state_po'})
        return gdf
    raise FileNotFoundError(f"State geodata not found at {geo_path}")


def load_electoral_data(year=None):
    """Load electoral data and return latest year results."""
    panel = pd.read_csv(DATA_DIR / 'panel_presidential_did.csv')
    if 'state' in panel.columns and 'state_po' not in panel.columns:
        panel = panel.rename(columns={'state': 'state_po'})

    if year is None:
        year = panel['year'].max()

    latest = panel[panel['year'] == year].groupby('state_po')['dem_share'].mean().reset_index()
    return latest, year


def get_candidate_labels(year):
    """Get candidate labels based on election year."""
    dem = 'Harris' if year == 2024 else 'Biden' if year == 2020 else 'Clinton' if year == 2016 else 'Dem'
    rep = 'Trump' if year >= 2016 else 'Rep'
    return dem, rep


def plot_state_map(ax, continental, alaska, hawaii, color_col, title, legend_elements):
    """Plot a single state map with Alaska/Hawaii insets."""
    continental.plot(ax=ax, color=continental[color_col], edgecolor='white', linewidth=1)

    if not alaska.empty:
        alaska_scaled = alaska.copy()
        alaska_scaled.geometry = alaska_scaled.geometry.scale(0.35, 0.35, origin=(0, 0))
        alaska_scaled.geometry = alaska_scaled.geometry.translate(-1800000, -1400000)
        alaska_scaled.plot(ax=ax, color=alaska[color_col].values[0], edgecolor='white', linewidth=1)

    if not hawaii.empty:
        hawaii_scaled = hawaii.copy()
        hawaii_scaled.geometry = hawaii_scaled.geometry.scale(1.0, 1.0, origin=(0, 0))
        hawaii_scaled.geometry = hawaii_scaled.geometry.translate(5200000, -1200000)
        hawaii_scaled.plot(ax=ax, color=hawaii[color_col].values[0], edgecolor='white', linewidth=1)

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.axis('off')
    ax.legend(handles=legend_elements, loc='lower left', fontsize=9, framealpha=0.95)


def create_three_panel_map(
    states_gdf,
    indicator_col,
    indicator_title,
    indicator_labels,
    match_title_template,
    figure_title,
    year,
    output_path=None,
    invert_match=False,
    invert_indicator_colors=False
):
    """
    Create a three-panel high-contrast map figure.

    Parameters:
    - states_gdf: GeoDataFrame with state_po, dem_share, and indicator column
    - indicator_col: column name for the binary indicator
    - indicator_title: title for top-left map
    - indicator_labels: (label_for_1, label_for_0) tuple for legend
    - match_title_template: title template for bottom map (uses {pct_match})
    - figure_title: overall figure title
    - year: election year
    - output_path: where to save the figure
    - invert_match: if True, match = indicator != dem_won (for voter ID)
    - invert_indicator_colors: if True, 1=red/0=blue instead of 1=blue/0=red
    """
    set_style()
    warnings.filterwarnings('ignore')

    dem_candidate, rep_candidate = get_candidate_labels(year)

    # Ensure dem_won exists
    states_gdf = states_gdf.copy()
    states_gdf['dem_won'] = (states_gdf['dem_share'] >= 50).astype(int)

    # Project to Albers
    states_gdf = states_gdf.to_crs('ESRI:102003')

    # Separate regions
    continental = states_gdf[~states_gdf['state_po'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])].copy()
    alaska = states_gdf[states_gdf['state_po'] == 'AK'].copy()
    hawaii = states_gdf[states_gdf['state_po'] == 'HI'].copy()

    # Create color columns
    if invert_indicator_colors:
        indicator_color_map = {1: RED_VIVID, 0: BLUE_VIVID}
    else:
        indicator_color_map = {1: BLUE_VIVID, 0: RED_VIVID}
    continental['color_indicator'] = continental[indicator_col].map(indicator_color_map)
    continental['color_vote'] = continental['dem_won'].map({1: BLUE_VIVID, 0: RED_VIVID})

    if invert_match:
        continental['match'] = (continental[indicator_col] != continental['dem_won']).astype(int)
    else:
        continental['match'] = (continental[indicator_col] == continental['dem_won']).astype(int)
    continental['color_match'] = continental['match'].map({1: GREEN_MATCH, 0: ORANGE_MISMATCH})

    # Apply colors to Alaska/Hawaii
    for region in [alaska, hawaii]:
        if not region.empty:
            region['color_indicator'] = region[indicator_col].map(indicator_color_map)
            region['color_vote'] = region['dem_won'].map({1: BLUE_VIVID, 0: RED_VIVID})
            if invert_match:
                region['match'] = (region[indicator_col] != region['dem_won']).astype(int)
            else:
                region['match'] = (region[indicator_col] == region['dem_won']).astype(int)
            region['color_match'] = region['match'].map({1: GREEN_MATCH, 0: ORANGE_MISMATCH})

    # Count for labels
    n_true = int(states_gdf[indicator_col].sum())
    n_false = len(states_gdf) - n_true
    n_match = int(continental['match'].sum())
    pct_match = 100 * n_match / len(continental)

    # Create figure
    fig = plt.figure(figsize=(14, 9))
    gs = GridSpec(2, 4, figure=fig, hspace=0.08, wspace=0.02,
                  left=0.01, right=0.99, top=0.94, bottom=0.02)

    ax_top_left = fig.add_subplot(gs[0, 0:2])
    ax_top_right = fig.add_subplot(gs[0, 2:4])
    ax_bottom = fig.add_subplot(gs[1, 1:3])

    # Top Left: Indicator map
    color_for_1 = RED_VIVID if invert_indicator_colors else BLUE_VIVID
    color_for_0 = BLUE_VIVID if invert_indicator_colors else RED_VIVID
    legend_indicator = [
        mpatches.Patch(facecolor=color_for_1, edgecolor='#333', label=f'{indicator_labels[0]} ({n_true} states)'),
        mpatches.Patch(facecolor=color_for_0, edgecolor='#333', label=f'{indicator_labels[1]} ({n_false} states)'),
    ]
    plot_state_map(ax_top_left, continental, alaska, hawaii, 'color_indicator',
                   indicator_title, legend_indicator)

    # Top Right: Electoral map
    legend_vote = [
        mpatches.Patch(facecolor=BLUE_VIVID, edgecolor='#333', label=f'{dem_candidate} Won'),
        mpatches.Patch(facecolor=RED_VIVID, edgecolor='#333', label=f'{rep_candidate} Won'),
    ]
    plot_state_map(ax_top_right, continental, alaska, hawaii, 'color_vote',
                   f'{year} Presidential Winner', legend_vote)

    # Bottom: Match map
    legend_match = [
        mpatches.Patch(facecolor=GREEN_MATCH, edgecolor='#333', label='Match'),
        mpatches.Patch(facecolor=ORANGE_MISMATCH, edgecolor='#333', label='Mismatch'),
    ]
    plot_state_map(ax_bottom, continental, alaska, hawaii, 'color_match',
                   match_title_template.format(pct_match=pct_match), legend_match)

    fig.suptitle(figure_title, fontsize=18, fontweight='bold', y=0.98)

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {output_path}")

    return fig


def create_high_contrast_maps(output_path=None, year=None):
    """Create voter ID vs electoral outcomes map."""
    states_gdf = load_state_geodata()
    electoral, year = load_electoral_data(year)

    policies = pd.read_csv(DATA_DIR / 'state_policies.csv')
    if 'abbrev' in policies.columns:
        policies = policies.rename(columns={'abbrev': 'state_po'})

    states_gdf = states_gdf.merge(policies[['state_po', 'id_strictness']], on='state_po', how='left')
    states_gdf = states_gdf.merge(electoral, on='state_po', how='left')

    # 2-tier: Tiers 1-3 = ID Required, Tiers 4-5 = No Effective ID
    states_gdf['id_strictness'] = states_gdf['id_strictness'].fillna(3)
    states_gdf['has_strict_id'] = (states_gdf['id_strictness'] <= 3).astype(int)

    return create_three_panel_map(
        states_gdf,
        indicator_col='has_strict_id',
        indicator_title='Voter ID Requirements',
        indicator_labels=('ID Required', 'No Effective ID'),
        match_title_template='Policy-Vote Alignment: {pct_match:.0f}% Match',
        figure_title='Voter ID Laws and Electoral Outcomes: The Visual Correlation',
        year=year,
        output_path=output_path,
        invert_match=True,  # ID Required matches Trump winning
        invert_indicator_colors=True  # ID Required = RED, No ID = BLUE
    )


def create_welfare_high_contrast_maps(output_path=None, year=None):
    """Create welfare benefits vs electoral outcomes map."""
    states_gdf = load_state_geodata()
    electoral, year = load_electoral_data(year)

    policies = pd.read_csv(DATA_DIR / 'state_policies.csv')
    if 'abbrev' in policies.columns:
        policies = policies.rename(columns={'abbrev': 'state_po'})

    policies['has_benefits'] = (
        (policies['health_children'] == 1) |
        (policies['health_adults'] == 1) |
        (policies['health_seniors'] == 1) |
        (policies['food'] == 1) |
        (policies['eitc'] == 1)
    ).astype(int)

    states_gdf = states_gdf.merge(policies[['state_po', 'has_benefits']], on='state_po', how='left')
    states_gdf = states_gdf.merge(electoral, on='state_po', how='left')
    states_gdf['has_benefits'] = states_gdf['has_benefits'].fillna(0).astype(int)

    return create_three_panel_map(
        states_gdf,
        indicator_col='has_benefits',
        indicator_title='Immigrant Welfare Benefits',
        indicator_labels=('Has Benefits', 'No Benefits'),
        match_title_template='Policy-Vote Alignment: {pct_match:.0f}% Match',
        figure_title='Immigrant Welfare Benefits and Electoral Outcomes: The Visual Correlation',
        year=year,
        output_path=output_path,
        invert_match=False  # Benefits matches Dem winning
    )


def create_unauthorized_pop_high_contrast_maps(output_path=None, year=None):
    """Create unauthorized population vs electoral outcomes map."""
    states_gdf = load_state_geodata()
    electoral, year = load_electoral_data(year)

    unauthorized_df = pd.read_csv(DATA_DIR / 'unauthorized_immigrant_pop_2023.csv')
    unauthorized_df = unauthorized_df[unauthorized_df['state_abbrev'] != 'US']
    unauthorized_df = unauthorized_df.rename(columns={'state_abbrev': 'state_po'})

    states_gdf = states_gdf.merge(unauthorized_df[['state_po', 'unauthorized_pop']], on='state_po', how='left')
    states_gdf = states_gdf.merge(electoral, on='state_po', how='left')

    median_pop = states_gdf['unauthorized_pop'].median()
    states_gdf['high_unauthorized'] = (states_gdf['unauthorized_pop'] >= median_pop).astype(int)

    return create_three_panel_map(
        states_gdf,
        indicator_col='high_unauthorized',
        indicator_title='Unauthorized Immigrant Population',
        indicator_labels=('Above Median', 'Below Median'),
        match_title_template='Population-Vote Alignment: {pct_match:.0f}% Match',
        figure_title='Unauthorized Immigrant Population and Electoral Outcomes',
        year=year,
        output_path=output_path,
        invert_match=False
    )


def create_unauthorized_pop_pct_high_contrast_maps(output_path=None, year=None):
    """Create unauthorized population % vs electoral outcomes map."""
    states_gdf = load_state_geodata()
    electoral, year = load_electoral_data(year)

    unauthorized_df = pd.read_csv(DATA_DIR / 'unauthorized_immigrant_pop_2023.csv')
    unauthorized_df = unauthorized_df[unauthorized_df['state_abbrev'] != 'US']
    unauthorized_df = unauthorized_df.rename(columns={'state_abbrev': 'state_po'})

    pop_df = pd.read_csv(DATA_DIR / 'state_population_historical.csv',
                         names=['state_po', 'pop_year', 'population'])
    pop_2024 = pop_df[pop_df['pop_year'] == 2024][['state_po', 'population']].copy()

    unauthorized_df = unauthorized_df.merge(pop_2024, on='state_po', how='left')
    unauthorized_df['unauthorized_pct'] = 100 * unauthorized_df['unauthorized_pop'] / unauthorized_df['population']

    states_gdf = states_gdf.merge(unauthorized_df[['state_po', 'unauthorized_pct']], on='state_po', how='left')
    states_gdf = states_gdf.merge(electoral, on='state_po', how='left')

    median_pct = states_gdf['unauthorized_pct'].median()
    states_gdf['high_unauthorized'] = (states_gdf['unauthorized_pct'] >= median_pct).astype(int)

    return create_three_panel_map(
        states_gdf,
        indicator_col='high_unauthorized',
        indicator_title='Unauthorized Pop. (% of State)',
        indicator_labels=('Above Median', 'Below Median'),
        match_title_template='Population %-Vote Alignment: {pct_match:.0f}% Match',
        figure_title='Unauthorized Immigrant % of Population and Electoral Outcomes',
        year=year,
        output_path=output_path,
        invert_match=False
    )


def generate_all_maps(year=2024):
    """Generate all four high-contrast map figures."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print(f"Generating High-Contrast Maps ({year})")
    print("="*60)

    create_high_contrast_maps(OUTPUT_DIR / f'high_contrast_maps_{year}.png', year=year)
    create_welfare_high_contrast_maps(OUTPUT_DIR / f'welfare_high_contrast_maps_{year}.png', year=year)
    create_unauthorized_pop_high_contrast_maps(OUTPUT_DIR / f'unauthorized_pop_high_contrast_maps_{year}.png', year=year)
    create_unauthorized_pop_pct_high_contrast_maps(OUTPUT_DIR / f'unauthorized_pop_pct_high_contrast_maps_{year}.png', year=year)

    print(f"\nAll figures saved to {OUTPUT_DIR}")
    print("="*60)


if __name__ == '__main__':
    generate_all_maps(year=2024)
