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

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output'

# High contrast colors
RED_VIVID = '#c41230'
BLUE_VIVID = '#0047ab'
GREEN_MATCH = '#2ca02c'
ORANGE_MISMATCH = '#ff7f0e'

# 2-tier colors (from src/visualize.py)
BLUE_LIGHT = '#deebf7'  # ID Required
BLUE_DARK = '#084594'   # No Effective ID

# Grey colors for neutral indicators
GREY_DARK = '#4a4a4a'
GREY_LIGHT = '#d9d9d9'


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
    """Load state boundaries from Census Bureau shapefile (simplified 5m boundaries)."""
    us_states_url = "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_5m.zip"
    try:
        gdf = gpd.read_file(us_states_url)
    except Exception as e:
        # Fall back to local GeoJSON if download fails
        geo_path = DATA_DIR / 'us_states.geojson'
        if geo_path.exists():
            gdf = gpd.read_file(geo_path)
        else:
            raise FileNotFoundError(f"Could not download Census data and no local file at {geo_path}: {e}")

    # Filter to 50 states + DC
    gdf = gdf[gdf['STATEFP'].astype(int) <= 56]
    gdf = gdf.rename(columns={'STUSPS': 'state_po'})
    return gdf


def load_electoral_data(year=None):
    """Load electoral data and return latest year results."""
    panel = pd.read_csv(DATA_DIR / 'panel_presidential_did.csv')
    if 'state' in panel.columns and 'state_po' not in panel.columns:
        panel = panel.rename(columns={'state': 'state_po'})

    if year is None:
        year = panel['year'].max()

    latest = panel[panel['year'] == year].groupby('state_po')['dem_share'].mean().reset_index()
    return latest, year


def load_county_geodata():
    """Load county boundaries from Census Bureau shapefile (20m resolution)."""
    us_counties_url = "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_county_20m.zip"
    try:
        gdf = gpd.read_file(us_counties_url)
    except Exception as e:
        # Fall back to local file
        geo_path = DATA_DIR / 'us_counties.geojson'
        if geo_path.exists():
            gdf = gpd.read_file(geo_path)
        else:
            raise FileNotFoundError(f"Could not download Census data and no local file at {geo_path}: {e}")

    # Create FIPS codes
    gdf['fips'] = gdf['GEOID'].astype(str).str.zfill(5)
    gdf['state_po'] = gdf['STUSPS']

    # Filter to continental US
    exclude = ['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP']
    gdf = gdf[~gdf['STUSPS'].isin(exclude)]

    return gdf


def load_county_votes():
    """Load county voting data."""
    path = DATA_DIR / 'county_presidential_2000_2020.csv'
    county_data = pd.read_csv(path)

    # Standardize
    if 'county_fips' in county_data.columns:
        county_data['fips'] = county_data['county_fips'].astype(str).str.zfill(5)

    # Get dem share
    if 'dem_two_party' in county_data.columns:
        county_data['dem_share'] = county_data['dem_two_party'] * 100
    elif 'per_dem' in county_data.columns:
        county_data['dem_share'] = county_data['per_dem'] * 100

    return county_data


def _get_state_from_fips(county_fips: str) -> str:
    """Get state abbreviation from county FIPS code."""
    FIPS_TO_STATE = {
        '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA',
        '08': 'CO', '09': 'CT', '10': 'DE', '11': 'DC', '12': 'FL',
        '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL', '18': 'IN',
        '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME',
        '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS',
        '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH',
        '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND',
        '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI',
        '45': 'SC', '46': 'SD', '47': 'TN', '48': 'TX', '49': 'UT',
        '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV', '55': 'WI',
        '56': 'WY',
    }
    state_fips = str(county_fips).zfill(5)[:2]
    return FIPS_TO_STATE.get(state_fips, 'UNKNOWN')


def _build_voter_id_border_pairs() -> tuple:
    """
    Build voter ID border pairs from Census adjacency data.

    Uses 2-tier classification: id_strictness <= 3 = "ID Required"
    Returns tuple of (id_required_fips, no_id_fips, id_required_states) sets.
    """
    # Load Census county adjacency data
    adjacency_path = DATA_DIR / 'census_county_adjacency.csv'
    adjacency = pd.read_csv(adjacency_path)

    # Load state_policies.csv for 2-tier voter ID classification
    policies = pd.read_csv(DATA_DIR / 'state_policies.csv')

    # 2-tier classification: ID Required = id_strictness <= 3
    id_required_states = set(policies[policies['id_strictness'] <= 3]['abbrev'])

    # Add state abbreviations
    adjacency['county_fips'] = adjacency['county_fips'].astype(str).str.zfill(5)
    adjacency['neighbor_fips'] = adjacency['neighbor_fips'].astype(str).str.zfill(5)
    adjacency['state_a'] = adjacency['county_fips'].apply(_get_state_from_fips)
    adjacency['state_b'] = adjacency['neighbor_fips'].apply(_get_state_from_fips)

    # Filter to cross-state pairs only
    cross_state = adjacency[adjacency['state_a'] != adjacency['state_b']].copy()

    # Add 2-tier voter ID status
    cross_state['state_a_id_req'] = cross_state['state_a'].isin(id_required_states)
    cross_state['state_b_id_req'] = cross_state['state_b'].isin(id_required_states)

    # Filter to pairs where states differ on voter ID (2-tier)
    voter_id_borders = cross_state[
        cross_state['state_a_id_req'] != cross_state['state_b_id_req']
    ].copy()

    # Collect FIPS by voter ID status
    id_required_fips = set()
    no_id_fips = set()

    for _, row in voter_id_borders.iterrows():
        if row['state_a_id_req']:
            id_required_fips.add(row['county_fips'])
            no_id_fips.add(row['neighbor_fips'])
        else:
            no_id_fips.add(row['county_fips'])
            id_required_fips.add(row['neighbor_fips'])

    return id_required_fips, no_id_fips, id_required_states


def create_border_counties_map(policy='welfare', output_path=None, year=2024):
    """
    Create map highlighting border county pairs.

    For welfare: shows benefit vs non-benefit state borders (from border_links.csv)
    For voter_id: builds borders from Census adjacency data (independent of welfare)
    """
    set_style()
    warnings.filterwarnings('ignore')

    fig, ax = plt.subplots(1, 1, figsize=(16, 10))

    try:
        counties = load_county_geodata()
        states = load_state_geodata()
        county_votes = load_county_votes()
        policies = pd.read_csv(DATA_DIR / 'state_policies.csv')

        # Get voting data for the specified year (or closest available)
        available_years = county_votes['year'].unique()
        if year not in available_years:
            year = max(available_years)
        votes = county_votes[county_votes['year'] == year][['fips', 'dem_share', 'state_po']].copy()

        if policy == 'voter_id':
            # Build voter ID borders from Census adjacency data
            strict_id_fips, no_strict_id_fips, treat_states = _build_voter_id_border_pairs()
            border_fips = strict_id_fips | no_strict_id_fips
        else:
            # Welfare: use border_links.csv
            border_links_path = DATA_DIR / 'border_links.csv'
            border_links = pd.read_csv(border_links_path)
            border_fips = set(border_links['benefit_county_fips'].astype(str).str.zfill(5)) | \
                         set(border_links['nonbenefit_county_fips'].astype(str).str.zfill(5))
            # Welfare benefit states
            treat_states = set(policies[
                (policies['health_children'] == 1) |
                (policies['health_adults'] == 1) |
                (policies['health_seniors'] == 1) |
                (policies['food'] == 1) |
                (policies['eitc'] == 1)
            ]['abbrev'])

        # Merge with geometry
        counties = counties.merge(votes, on='fips', how='left')
        counties['is_border'] = counties['fips'].isin(border_fips)
        counties['treated'] = counties['STUSPS'].isin(treat_states)

        # Create categories
        def categorize(row):
            if row['is_border']:
                return 'Treatment Border' if row['treated'] else 'Control Border'
            else:
                return 'Treatment Interior' if row['treated'] else 'Control Interior'

        counties['category'] = counties.apply(categorize, axis=1)

        # Color scheme
        colors = {
            'Treatment Border': '#e74c3c' if policy == 'voter_id' else '#3498db',
            'Control Border': '#3498db' if policy == 'voter_id' else '#e74c3c',
            'Treatment Interior': '#f5b7b1' if policy == 'voter_id' else '#aed6f1',
            'Control Interior': '#aed6f1' if policy == 'voter_id' else '#f5b7b1',
        }

        counties['color'] = counties['category'].map(colors)

        # Project to Albers for continental US
        counties = counties.to_crs('ESRI:102003')
        states = states.to_crs('ESRI:102003')

        # Plot counties
        counties.plot(ax=ax, color=counties['color'], edgecolor='white', linewidth=0.1)

        # Highlight border counties with thicker edge
        border_counties = counties[counties['is_border']]
        border_counties.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.8)

        # State boundaries
        states_continental = states[~states['state_po'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])]
        states_continental.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)

        ax.axis('off')
        ax.margins(0)
        ax.autoscale_view(tight=True)

        # Legend (matching plot_state_map styling)
        policy_label = 'ID Required' if policy == 'voter_id' else 'Benefits'
        control_label = 'No ID Required' if policy == 'voter_id' else 'No Benefits'
        legend_elements = [
            mpatches.Patch(facecolor=colors['Treatment Border'], edgecolor='#333',
                          label=f'{policy_label} State - Border'),
            mpatches.Patch(facecolor=colors['Control Border'], edgecolor='#333',
                          label=f'{control_label} State - Border'),
            mpatches.Patch(facecolor=colors['Treatment Interior'], edgecolor='#333',
                          label=f'{policy_label} State - Interior'),
            mpatches.Patch(facecolor=colors['Control Interior'], edgecolor='#333',
                          label=f'{control_label} State - Interior'),
        ]
        legend = ax.legend(handles=legend_elements, loc='lower left', fontsize=14,
                           frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                           bbox_to_anchor=(0.02, 0.0))
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_edgecolor('#cccccc')

        # Title (matching other map figures)
        n_border = len(border_fips)
        title = 'Voter ID Laws' if policy == 'voter_id' else 'Immigrant Welfare Benefits'
        ax.set_title(f'Border County Pairs: {title}\n{n_border} counties along policy borders',
                    fontsize=24, fontweight='bold', pad=10)

    except Exception as e:
        ax.text(0.5, 0.5, f'Error: {str(e)[:100]}',
               ha='center', va='center', transform=ax.transAxes)
        import traceback
        traceback.print_exc()

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {output_path}")

    return fig


def get_candidate_labels(year):
    """Get candidate labels based on election year."""
    dem = 'Harris' if year == 2024 else 'Biden' if year == 2020 else 'Clinton' if year == 2016 else 'Dem'
    rep = 'Trump' if year >= 2016 else 'Rep'
    return dem, rep


def plot_state_map(ax, continental, alaska, hawaii, color_col, title, legend_elements):
    """Plot a single state map with Alaska/Hawaii insets, plotting each state individually."""
    # Plot each continental state one-by-one to avoid color artifacts
    for idx, row in continental.iterrows():
        color = row[color_col]
        continental[continental.index == idx].plot(
            ax=ax, color=color, edgecolor='white', linewidth=0.8
        )

    if not alaska.empty:
        alaska_scaled = alaska.copy()
        alaska_scaled.geometry = alaska_scaled.geometry.scale(0.35, 0.35, origin=(0, 0))
        alaska_scaled.geometry = alaska_scaled.geometry.translate(-1800000, -1400000)
        color = alaska[color_col].values[0]
        alaska_scaled.plot(ax=ax, color=color, edgecolor='white', linewidth=0.8)

    if not hawaii.empty:
        hawaii_scaled = hawaii.copy()
        hawaii_scaled.geometry = hawaii_scaled.geometry.scale(1.0, 1.0, origin=(0, 0))
        hawaii_scaled.geometry = hawaii_scaled.geometry.translate(5200000, -1200000)
        color = hawaii[color_col].values[0]
        hawaii_scaled.plot(ax=ax, color=color, edgecolor='white', linewidth=0.8)

    ax.set_title(title, fontsize=16, fontweight='bold', pad=10)
    ax.axis('off')
    ax.margins(0)
    ax.autoscale_view(tight=True)
    # Tighten left margin to match right margin
    xlim = ax.get_xlim()
    ax.set_xlim(xlim[0] + 300000, xlim[1])
    legend = ax.legend(handles=legend_elements, loc='lower left', fontsize=10,
                       frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                       bbox_to_anchor=(0.08, 0.0))
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_edgecolor('#cccccc')


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
    invert_indicator_colors=False,
    indicator_colors=None
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
    - indicator_colors: optional (color_for_1, color_for_0) tuple for custom colors
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
    if indicator_colors:
        indicator_color_map = {1: indicator_colors[0], 0: indicator_colors[1]}
    elif invert_indicator_colors:
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

    # Count for labels (using all 51 jurisdictions)
    n_true = int(states_gdf[indicator_col].sum())
    n_false = len(states_gdf) - n_true
    # Calculate match from all states including AK/HI
    all_matches = continental['match'].sum()
    for region in [alaska, hawaii]:
        if not region.empty and 'match' in region.columns:
            all_matches += region['match'].sum()
    n_match = int(all_matches)
    total_states = len(continental) + (1 if not alaska.empty else 0) + (1 if not hawaii.empty else 0)
    pct_match = 100 * n_match / total_states

    # Create figure with tight spacing
    fig = plt.figure(figsize=(14, 9))
    gs = GridSpec(2, 4, figure=fig, hspace=0.06, wspace=0.06,
                  left=0.01, right=0.99, top=0.94, bottom=0.02)

    ax_top_left = fig.add_subplot(gs[0, 0:2])
    ax_top_right = fig.add_subplot(gs[0, 2:4])
    ax_bottom = fig.add_subplot(gs[1, 1:3])

    # Top Left: Indicator map
    if indicator_colors:
        color_for_1 = indicator_colors[0]
        color_for_0 = indicator_colors[1]
    elif invert_indicator_colors:
        color_for_1 = RED_VIVID
        color_for_0 = BLUE_VIVID
    else:
        color_for_1 = BLUE_VIVID
        color_for_0 = RED_VIVID
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

    # Add arrow between top maps
    from matplotlib.patches import FancyArrowPatch
    arrow = FancyArrowPatch(
        (0.48, 0.72), (0.52, 0.72),
        transform=fig.transFigure,
        arrowstyle='-|>',
        mutation_scale=15,
        color='#333333',
        linewidth=2
    )
    fig.patches.append(arrow)

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
        figure_title='Voter ID Laws and Electoral Outcomes',
        year=year,
        output_path=output_path,
        invert_match=True,  # ID Required matches Trump winning
        invert_indicator_colors=True  # ID Required = RED, No ID = BLUE
    )


def create_high_contrast_maps_2tier(output_path=None, year=None):
    """Create voter ID vs electoral outcomes map using 2-tier color scheme from src/visualize.py."""
    set_style()
    warnings.filterwarnings('ignore')

    states_gdf = load_state_geodata()
    electoral, year = load_electoral_data(year)

    policies = pd.read_csv(DATA_DIR / 'state_policies.csv')
    if 'abbrev' in policies.columns:
        policies = policies.rename(columns={'abbrev': 'state_po'})

    states_gdf = states_gdf.merge(policies[['state_po', 'id_strictness']], on='state_po', how='left')
    states_gdf = states_gdf.merge(electoral, on='state_po', how='left')

    states_gdf['id_strictness'] = states_gdf['id_strictness'].fillna(3)
    states_gdf['has_strict_id'] = (states_gdf['id_strictness'] <= 3).astype(int)
    states_gdf['dem_won'] = (states_gdf['dem_share'] >= 50).astype(int)

    dem_candidate, rep_candidate = get_candidate_labels(year)

    # Project to Albers
    states_gdf = states_gdf.to_crs('ESRI:102003')

    # Separate regions
    continental = states_gdf[~states_gdf['state_po'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])].copy()
    alaska = states_gdf[states_gdf['state_po'] == 'AK'].copy()
    hawaii = states_gdf[states_gdf['state_po'] == 'HI'].copy()

    # 2-tier colors for voter ID: ID Required = light blue, No ID = dark blue
    continental['color_indicator'] = continental['has_strict_id'].map({1: BLUE_LIGHT, 0: BLUE_DARK})
    # Legacy colors for presidential: Harris = blue, Trump = red
    continental['color_vote'] = continental['dem_won'].map({1: BLUE_VIVID, 0: RED_VIVID})

    # Match: ID Required + Trump won, OR No ID + Harris won
    continental['match'] = (continental['has_strict_id'] != continental['dem_won']).astype(int)
    continental['color_match'] = continental['match'].map({1: GREEN_MATCH, 0: ORANGE_MISMATCH})

    for region in [alaska, hawaii]:
        if not region.empty:
            region['color_indicator'] = region['has_strict_id'].map({1: BLUE_LIGHT, 0: BLUE_DARK})
            region['color_vote'] = region['dem_won'].map({1: BLUE_VIVID, 0: RED_VIVID})
            region['match'] = (region['has_strict_id'] != region['dem_won']).astype(int)
            region['color_match'] = region['match'].map({1: GREEN_MATCH, 0: ORANGE_MISMATCH})

    n_id_req = int(states_gdf['has_strict_id'].sum())
    n_no_id = len(states_gdf) - n_id_req
    # Calculate match from all states including AK/HI
    all_matches = continental['match'].sum()
    for region in [alaska, hawaii]:
        if not region.empty and 'match' in region.columns:
            all_matches += region['match'].sum()
    n_match = int(all_matches)
    total_states = len(continental) + (1 if not alaska.empty else 0) + (1 if not hawaii.empty else 0)
    pct_match = 100 * n_match / total_states

    # Create figure
    fig = plt.figure(figsize=(14, 9))
    gs = GridSpec(2, 4, figure=fig, hspace=0.06, wspace=0.06,
                  left=0.01, right=0.99, top=0.94, bottom=0.02)

    ax_top_left = fig.add_subplot(gs[0, 0:2])
    ax_top_right = fig.add_subplot(gs[0, 2:4])
    ax_bottom = fig.add_subplot(gs[1, 1:3])

    # Top Left: Voter ID (2-tier colors)
    legend_indicator = [
        mpatches.Patch(facecolor=BLUE_LIGHT, edgecolor='#333', label=f'ID Required ({n_id_req} states)'),
        mpatches.Patch(facecolor=BLUE_DARK, edgecolor='#333', label=f'No Effective ID ({n_no_id} states)'),
    ]
    plot_state_map(ax_top_left, continental, alaska, hawaii, 'color_indicator',
                   'Voter ID Requirements', legend_indicator)

    # Top Right: Electoral map (legacy red/blue colors)
    legend_vote = [
        mpatches.Patch(facecolor=BLUE_VIVID, edgecolor='#333', label=f'{dem_candidate} Won'),
        mpatches.Patch(facecolor=RED_VIVID, edgecolor='#333', label=f'{rep_candidate} Won'),
    ]
    plot_state_map(ax_top_right, continental, alaska, hawaii, 'color_vote',
                   f'{year} Presidential Winner', legend_vote)

    # Arrow between top maps
    from matplotlib.patches import FancyArrowPatch
    arrow = FancyArrowPatch(
        (0.48, 0.72), (0.52, 0.72),
        transform=fig.transFigure,
        arrowstyle='-|>',
        mutation_scale=15,
        color='#333333',
        linewidth=2
    )
    fig.patches.append(arrow)

    # Bottom: Match map
    legend_match = [
        mpatches.Patch(facecolor=GREEN_MATCH, edgecolor='#333', label='Match'),
        mpatches.Patch(facecolor=ORANGE_MISMATCH, edgecolor='#333', label='Mismatch'),
    ]
    plot_state_map(ax_bottom, continental, alaska, hawaii, 'color_match',
                   f'Policy-Vote Alignment: {pct_match:.0f}% Match', legend_match)

    fig.suptitle('Voter ID Laws and Electoral Outcomes', fontsize=18, fontweight='bold', y=0.98)

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {output_path}")

    return fig


def create_welfare_high_contrast_maps(output_path=None, year=None):
    """Create welfare benefits vs electoral outcomes map using 2-tier color scheme."""
    set_style()
    warnings.filterwarnings('ignore')

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
    states_gdf['dem_won'] = (states_gdf['dem_share'] >= 50).astype(int)

    dem_candidate, rep_candidate = get_candidate_labels(year)

    # Project to Albers
    states_gdf = states_gdf.to_crs('ESRI:102003')

    # Separate regions
    continental = states_gdf[~states_gdf['state_po'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])].copy()
    alaska = states_gdf[states_gdf['state_po'] == 'AK'].copy()
    hawaii = states_gdf[states_gdf['state_po'] == 'HI'].copy()

    # 2-tier colors for welfare: Has Benefits = dark blue, No Benefits = light blue
    continental['color_indicator'] = continental['has_benefits'].map({1: BLUE_DARK, 0: BLUE_LIGHT})
    continental['color_vote'] = continental['dem_won'].map({1: BLUE_VIVID, 0: RED_VIVID})

    # Match: Benefits + Dem won, OR No Benefits + Rep won
    continental['match'] = (continental['has_benefits'] == continental['dem_won']).astype(int)
    continental['color_match'] = continental['match'].map({1: GREEN_MATCH, 0: ORANGE_MISMATCH})

    for region in [alaska, hawaii]:
        if not region.empty:
            region['color_indicator'] = region['has_benefits'].map({1: BLUE_DARK, 0: BLUE_LIGHT})
            region['color_vote'] = region['dem_won'].map({1: BLUE_VIVID, 0: RED_VIVID})
            region['match'] = (region['has_benefits'] == region['dem_won']).astype(int)
            region['color_match'] = region['match'].map({1: GREEN_MATCH, 0: ORANGE_MISMATCH})

    n_benefits = int(states_gdf['has_benefits'].sum())
    n_no_benefits = len(states_gdf) - n_benefits
    # Calculate match from all states including AK/HI
    all_matches = continental['match'].sum()
    for region in [alaska, hawaii]:
        if not region.empty and 'match' in region.columns:
            all_matches += region['match'].sum()
    n_match = int(all_matches)
    total_states = len(continental) + (1 if not alaska.empty else 0) + (1 if not hawaii.empty else 0)
    pct_match = 100 * n_match / total_states

    # Create figure
    fig = plt.figure(figsize=(14, 9))
    gs = GridSpec(2, 4, figure=fig, hspace=0.06, wspace=0.06,
                  left=0.01, right=0.99, top=0.94, bottom=0.02)

    ax_top_left = fig.add_subplot(gs[0, 0:2])
    ax_top_right = fig.add_subplot(gs[0, 2:4])
    ax_bottom = fig.add_subplot(gs[1, 1:3])

    # Top Left: Welfare Benefits (2-tier colors)
    legend_indicator = [
        mpatches.Patch(facecolor=BLUE_DARK, edgecolor='#333', label=f'Has Benefits ({n_benefits} states)'),
        mpatches.Patch(facecolor=BLUE_LIGHT, edgecolor='#333', label=f'No Benefits ({n_no_benefits} states)'),
    ]
    plot_state_map(ax_top_left, continental, alaska, hawaii, 'color_indicator',
                   'Illegal Immigrant Welfare Benefits', legend_indicator)

    # Top Right: Electoral map
    legend_vote = [
        mpatches.Patch(facecolor=BLUE_VIVID, edgecolor='#333', label=f'{dem_candidate} Won'),
        mpatches.Patch(facecolor=RED_VIVID, edgecolor='#333', label=f'{rep_candidate} Won'),
    ]
    plot_state_map(ax_top_right, continental, alaska, hawaii, 'color_vote',
                   f'{year} Presidential Winner', legend_vote)

    # Arrow between top maps
    from matplotlib.patches import FancyArrowPatch
    arrow = FancyArrowPatch(
        (0.48, 0.72), (0.52, 0.72),
        transform=fig.transFigure,
        arrowstyle='-|>',
        mutation_scale=15,
        color='#333333',
        linewidth=2
    )
    fig.patches.append(arrow)

    # Bottom: Match map
    legend_match = [
        mpatches.Patch(facecolor=GREEN_MATCH, edgecolor='#333', label='Match'),
        mpatches.Patch(facecolor=ORANGE_MISMATCH, edgecolor='#333', label='Mismatch'),
    ]
    plot_state_map(ax_bottom, continental, alaska, hawaii, 'color_match',
                   f'Policy-Vote Alignment: {pct_match:.0f}% Match', legend_match)

    fig.suptitle('Illegal Immigrant Welfare Benefits and Electoral Outcomes', fontsize=18, fontweight='bold', y=0.98)

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {output_path}")

    return fig


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
        indicator_title='Illegal Immigrant Population',
        indicator_labels=('Above Median', 'Below Median'),
        match_title_template='Population-Vote Alignment: {pct_match:.0f}% Match',
        figure_title='Illegal Immigrant Population and Electoral Outcomes',
        year=year,
        output_path=output_path,
        invert_match=False,
        indicator_colors=(GREY_DARK, GREY_LIGHT)
    )


def prepare_voter_id_data(year=None):
    """Prepare voter ID data for visualization."""
    states_gdf = load_state_geodata()
    electoral, year = load_electoral_data(year)

    policies = pd.read_csv(DATA_DIR / 'state_policies.csv')
    if 'abbrev' in policies.columns:
        policies = policies.rename(columns={'abbrev': 'state_po'})

    states_gdf = states_gdf.merge(policies[['state_po', 'id_strictness']], on='state_po', how='left')
    states_gdf = states_gdf.merge(electoral, on='state_po', how='left')

    states_gdf['id_strictness'] = states_gdf['id_strictness'].fillna(3)
    states_gdf['has_strict_id'] = (states_gdf['id_strictness'] <= 3).astype(int)
    states_gdf['dem_won'] = (states_gdf['dem_share'] >= 50).astype(int)

    return states_gdf, year


def prepare_welfare_data(year=None):
    """Prepare welfare benefits data for visualization."""
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
    states_gdf['dem_won'] = (states_gdf['dem_share'] >= 50).astype(int)

    return states_gdf, year


def create_combined_four_panel_map(output_path=None, year=None):
    """
    Create a combined 4-panel visualization with:
    - Top row: Voter ID Requirements + Presidential Winner
    - Bottom row: Welfare Benefits + Presidential Winner
    - Arrows between left and right maps on each row
    """
    set_style()
    warnings.filterwarnings('ignore')

    # Load both datasets
    voter_id_gdf, year = prepare_voter_id_data(year)
    welfare_gdf, _ = prepare_welfare_data(year)

    dem_candidate, rep_candidate = get_candidate_labels(year)

    # Project to Albers
    voter_id_gdf = voter_id_gdf.to_crs('ESRI:102003')
    welfare_gdf = welfare_gdf.to_crs('ESRI:102003')

    # Separate regions for voter ID
    vi_continental = voter_id_gdf[~voter_id_gdf['state_po'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])].copy()
    vi_alaska = voter_id_gdf[voter_id_gdf['state_po'] == 'AK'].copy()
    vi_hawaii = voter_id_gdf[voter_id_gdf['state_po'] == 'HI'].copy()

    # Separate regions for welfare
    wf_continental = welfare_gdf[~welfare_gdf['state_po'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])].copy()
    wf_alaska = welfare_gdf[welfare_gdf['state_po'] == 'AK'].copy()
    wf_hawaii = welfare_gdf[welfare_gdf['state_po'] == 'HI'].copy()

    # Create color columns for voter ID (2-tier colors: ID Required = light, No ID = dark)
    vi_continental['color_indicator'] = vi_continental['has_strict_id'].map({1: BLUE_LIGHT, 0: BLUE_DARK})
    vi_continental['color_vote'] = vi_continental['dem_won'].map({1: BLUE_VIVID, 0: RED_VIVID})
    for region in [vi_alaska, vi_hawaii]:
        if not region.empty:
            region['color_indicator'] = region['has_strict_id'].map({1: BLUE_LIGHT, 0: BLUE_DARK})
            region['color_vote'] = region['dem_won'].map({1: BLUE_VIVID, 0: RED_VIVID})

    # Create color columns for welfare (2-tier colors: Has Benefits = dark, No Benefits = light)
    wf_continental['color_indicator'] = wf_continental['has_benefits'].map({1: BLUE_DARK, 0: BLUE_LIGHT})
    wf_continental['color_vote'] = wf_continental['dem_won'].map({1: BLUE_VIVID, 0: RED_VIVID})
    for region in [wf_alaska, wf_hawaii]:
        if not region.empty:
            region['color_indicator'] = region['has_benefits'].map({1: BLUE_DARK, 0: BLUE_LIGHT})
            region['color_vote'] = region['dem_won'].map({1: BLUE_VIVID, 0: RED_VIVID})

    # Count states
    n_id_req = int(voter_id_gdf['has_strict_id'].sum())
    n_no_id = len(voter_id_gdf) - n_id_req
    n_benefits = int(welfare_gdf['has_benefits'].sum())
    n_no_benefits = len(welfare_gdf) - n_benefits

    # Create figure with minimal spacing
    fig = plt.figure(figsize=(14, 8.5))
    gs = GridSpec(2, 2, figure=fig, hspace=0.06, wspace=0.06,
                  left=0.01, right=0.99, top=0.92, bottom=0.02)

    ax_top_left = fig.add_subplot(gs[0, 0])
    ax_top_right = fig.add_subplot(gs[0, 1])
    ax_bottom_left = fig.add_subplot(gs[1, 0])
    ax_bottom_right = fig.add_subplot(gs[1, 1])

    # Top Left: Voter ID Requirements (2-tier colors)
    legend_voter_id = [
        mpatches.Patch(facecolor=BLUE_LIGHT, edgecolor='#333', label=f'ID Required ({n_id_req} states)'),
        mpatches.Patch(facecolor=BLUE_DARK, edgecolor='#333', label=f'No Effective ID ({n_no_id} states)'),
    ]
    plot_state_map(ax_top_left, vi_continental, vi_alaska, vi_hawaii, 'color_indicator',
                   'Voter ID Requirements', legend_voter_id)

    # Top Right: Presidential Winner (for voter ID comparison)
    legend_vote = [
        mpatches.Patch(facecolor=BLUE_VIVID, edgecolor='#333', label=f'{dem_candidate} Won'),
        mpatches.Patch(facecolor=RED_VIVID, edgecolor='#333', label=f'{rep_candidate} Won'),
    ]
    plot_state_map(ax_top_right, vi_continental, vi_alaska, vi_hawaii, 'color_vote',
                   f'{year} Presidential Winner', legend_vote)

    # Bottom Left: Welfare Benefits (2-tier colors)
    legend_welfare = [
        mpatches.Patch(facecolor=BLUE_DARK, edgecolor='#333', label=f'Has Benefits ({n_benefits} states)'),
        mpatches.Patch(facecolor=BLUE_LIGHT, edgecolor='#333', label=f'No Benefits ({n_no_benefits} states)'),
    ]
    plot_state_map(ax_bottom_left, wf_continental, wf_alaska, wf_hawaii, 'color_indicator',
                   'Illegal Immigrant Welfare Benefits', legend_welfare)

    # Bottom Right: Presidential Winner (for welfare comparison)
    plot_state_map(ax_bottom_right, wf_continental, wf_alaska, wf_hawaii, 'color_vote',
                   f'{year} Presidential Winner', legend_vote)

    # Add small arrows between maps using FancyArrowPatch
    from matplotlib.patches import FancyArrowPatch

    # Top row arrow (short arrow in the gap between maps)
    arrow_top = FancyArrowPatch(
        (0.48, 0.70), (0.52, 0.70),
        transform=fig.transFigure,
        arrowstyle='-|>',
        mutation_scale=15,
        color='#333333',
        linewidth=2
    )
    fig.patches.append(arrow_top)

    # Bottom row arrow (short arrow in the gap between maps)
    arrow_bottom = FancyArrowPatch(
        (0.48, 0.26), (0.52, 0.26),
        transform=fig.transFigure,
        arrowstyle='-|>',
        mutation_scale=15,
        color='#333333',
        linewidth=2
    )
    fig.patches.append(arrow_bottom)

    fig.suptitle('Voter ID Laws and Welfare Benefits vs Electoral Outcomes',
                 fontsize=18, fontweight='bold', y=0.97)

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {output_path}")

    return fig


def create_standalone_alignment_map(
    states_gdf,
    indicator_col,
    match_title,
    figure_title,
    year,
    output_path=None,
    invert_match=False
):
    """Create a standalone single-panel alignment map."""
    set_style()
    warnings.filterwarnings('ignore')

    states_gdf = states_gdf.copy()
    states_gdf = states_gdf.to_crs('ESRI:102003')

    # Separate regions
    continental = states_gdf[~states_gdf['state_po'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])].copy()
    alaska = states_gdf[states_gdf['state_po'] == 'AK'].copy()
    hawaii = states_gdf[states_gdf['state_po'] == 'HI'].copy()

    # Calculate match
    if invert_match:
        continental['match'] = (continental[indicator_col] != continental['dem_won']).astype(int)
    else:
        continental['match'] = (continental[indicator_col] == continental['dem_won']).astype(int)
    continental['color_match'] = continental['match'].map({1: GREEN_MATCH, 0: ORANGE_MISMATCH})

    for region in [alaska, hawaii]:
        if not region.empty:
            if invert_match:
                region['match'] = (region[indicator_col] != region['dem_won']).astype(int)
            else:
                region['match'] = (region[indicator_col] == region['dem_won']).astype(int)
            region['color_match'] = region['match'].map({1: GREEN_MATCH, 0: ORANGE_MISMATCH})

    # Calculate match from all states including AK/HI
    all_matches = continental['match'].sum()
    for region in [alaska, hawaii]:
        if not region.empty and 'match' in region.columns:
            all_matches += region['match'].sum()
    n_match = int(all_matches)
    total_states = len(continental) + (1 if not alaska.empty else 0) + (1 if not hawaii.empty else 0)
    pct_match = 100 * n_match / total_states

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    legend_match = [
        mpatches.Patch(facecolor=GREEN_MATCH, edgecolor='#333', label='Match'),
        mpatches.Patch(facecolor=ORANGE_MISMATCH, edgecolor='#333', label='Mismatch'),
    ]
    plot_state_map(ax, continental, alaska, hawaii, 'color_match',
                   match_title.format(pct_match=pct_match), legend_match)

    fig.suptitle(figure_title, fontsize=16, fontweight='bold', y=0.98)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {output_path}")

    return fig


def create_voter_id_alignment_only(output_path=None, year=None):
    """Create standalone voter ID alignment map."""
    states_gdf, year = prepare_voter_id_data(year)

    return create_standalone_alignment_map(
        states_gdf,
        indicator_col='has_strict_id',
        match_title='Voter ID Policy-Vote Alignment: {pct_match:.0f}% Match',
        figure_title='Voter ID Laws and Electoral Outcomes',
        year=year,
        output_path=output_path,
        invert_match=True
    )


def create_welfare_alignment_only(output_path=None, year=None):
    """Create standalone welfare benefits alignment map."""
    states_gdf, year = prepare_welfare_data(year)

    return create_standalone_alignment_map(
        states_gdf,
        indicator_col='has_benefits',
        match_title='Welfare Policy-Vote Alignment: {pct_match:.0f}% Match',
        figure_title='Illegal Immigrant Welfare Benefits and Electoral Outcomes',
        year=year,
        output_path=output_path,
        invert_match=False
    )


# =============================================================================
# CORRELATION BAR CHARTS
# =============================================================================

# Colors for bar charts
MAGENTA = '#A23B72'
BLUE_MID = '#2E86AB'


def create_state_presidential_correlation(output_path=None):
    """Create bar chart showing state-level presidential election correlations.

    Uses consistent 2-tier voter ID classification and has_benefit welfare definition.
    """
    set_style()

    # Load data
    electoral, year = load_electoral_data(2024)
    policies = pd.read_csv(DATA_DIR / 'state_policies.csv')
    if 'abbrev' in policies.columns:
        policies = policies.rename(columns={'abbrev': 'state_po'})

    # Merge
    df = electoral.merge(policies, on='state_po', how='left')

    # Create policy indicators
    df['has_strict_id'] = (df['id_strictness'] <= 3).astype(int)
    df['has_benefits'] = (
        (df['health_children'] == 1) |
        (df['health_adults'] == 1) |
        (df['health_seniors'] == 1) |
        (df['food'] == 1) |
        (df['eitc'] == 1)
    ).astype(int)

    # Voter ID: compare ID-required vs no-ID states
    id_req = df[df['has_strict_id'] == 1]['dem_share']
    no_id = df[df['has_strict_id'] == 0]['dem_share']
    voter_id_gap = id_req.mean() - no_id.mean()

    # Welfare: compare benefit vs no-benefit states
    benefit = df[df['has_benefits'] == 1]['dem_share']
    no_benefit = df[df['has_benefits'] == 0]['dem_share']
    welfare_gap = benefit.mean() - no_benefit.mean()

    fig, ax = plt.subplots(figsize=(8, 6))

    categories = ['Voter ID\nLaws', 'Immigrant\nWelfare Benefits']
    values = [voter_id_gap, welfare_gap]
    colors = [MAGENTA, BLUE_MID]

    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=2, width=0.6)

    # Add value labels at end of bars
    for bar, val, color in zip(bars, values, colors):
        if val < 0:
            ax.annotate(f'{abs(val):.1f}pp',
                        xy=(bar.get_x() + bar.get_width() / 2, val - 1),
                        ha='center', va='top',
                        fontsize=16, fontweight='bold', color=color)
        else:
            ax.annotate(f'{val:.1f}pp',
                        xy=(bar.get_x() + bar.get_width() / 2, val + 1),
                        ha='center', va='bottom',
                        fontsize=16, fontweight='bold', color=color)

    ax.axhline(0, color='black', linewidth=1.5)
    ax.set_ylabel('Gap in Democratic Vote Share (pp)', fontsize=12)
    ax.set_ylim(-20, 22)
    ax.set_xlim(-0.5, 1.5)

    ax.set_title('Policy Gap in Presidential Vote (2024)',
                 fontsize=16, fontweight='bold', pad=15)

    # Add explanation text adjacent to zero line, opposite side from bar
    ax.text(0, 1, f'ID-required states vote\n{abs(voter_id_gap):.0f}pp more Republican',
            ha='center', va='bottom', fontsize=20, color=MAGENTA)
    ax.text(1, -1, f'Benefit states vote\n{welfare_gap:.0f}pp more Democratic',
            ha='center', va='top', fontsize=20, color=BLUE_MID)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {output_path}")

    return fig


def create_state_house_correlation(output_path=None):
    """Create bar chart showing state-level US House election correlations.

    Uses consistent 2-tier voter ID classification and has_benefit welfare definition.
    """
    set_style()

    # Load House election data
    house_path = DATA_DIR / 'house_elections.csv'
    house_df = pd.read_csv(house_path)

    # Get 2024 data (or latest available)
    if 2024 in house_df['year'].values:
        year = 2024
    else:
        year = house_df['year'].max()

    house_2024 = house_df[house_df['year'] == year][['state', 'dem_two_party_share']].copy()
    house_2024 = house_2024.rename(columns={'state': 'state_po', 'dem_two_party_share': 'dem_share'})

    # Load policies
    policies = pd.read_csv(DATA_DIR / 'state_policies.csv')
    if 'abbrev' in policies.columns:
        policies = policies.rename(columns={'abbrev': 'state_po'})

    # Merge
    df = house_2024.merge(policies, on='state_po', how='left')

    # Create policy indicators
    df['has_strict_id'] = (df['id_strictness'] <= 3).astype(int)
    df['has_benefits'] = (
        (df['health_children'] == 1) |
        (df['health_adults'] == 1) |
        (df['health_seniors'] == 1) |
        (df['food'] == 1) |
        (df['eitc'] == 1)
    ).astype(int)

    # Voter ID: compare ID-required vs no-ID states
    id_req = df[df['has_strict_id'] == 1]['dem_share']
    no_id = df[df['has_strict_id'] == 0]['dem_share']
    voter_id_gap = id_req.mean() - no_id.mean()

    # Welfare: compare benefit vs no-benefit states
    benefit = df[df['has_benefits'] == 1]['dem_share']
    no_benefit = df[df['has_benefits'] == 0]['dem_share']
    welfare_gap = benefit.mean() - no_benefit.mean()

    fig, ax = plt.subplots(figsize=(8, 6))

    categories = ['Voter ID\nLaws', 'Immigrant\nWelfare Benefits']
    values = [voter_id_gap, welfare_gap]
    colors = [MAGENTA, BLUE_MID]

    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=2, width=0.6)

    # Add value labels at end of bars
    for bar, val, color in zip(bars, values, colors):
        ypos = val - 1 if val < 0 else val + 1
        va = 'top' if val < 0 else 'bottom'
        ax.annotate(f'{abs(val):.1f}pp',
                    xy=(bar.get_x() + bar.get_width() / 2, ypos),
                    ha='center', va=va,
                    fontsize=16, fontweight='bold', color=color)

    ax.axhline(0, color='black', linewidth=1.5)
    ax.set_ylabel('Gap in Democratic Vote Share (pp)', fontsize=12)
    ax.set_ylim(-26, 28)
    ax.set_xlim(-0.5, 1.5)

    ax.set_title(f'Policy Gap in US House Vote ({year})',
                 fontsize=16, fontweight='bold', pad=15)

    # Add explanation text adjacent to zero line, opposite side from bar
    ax.text(0, 1, f'ID-required states vote\n{abs(voter_id_gap):.0f}pp more Republican',
            ha='center', va='bottom', fontsize=20, color=MAGENTA)
    ax.text(1, -1, f'Benefit states vote\n{welfare_gap:.0f}pp more Democratic',
            ha='center', va='top', fontsize=20, color=BLUE_MID)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {output_path}")

    return fig


def create_border_correlation(output_path=None):
    """Create bar chart showing border county correlations for both policies.

    Uses Census adjacency data for voter ID borders and border_links.csv for welfare.
    Each unique border county is counted once to avoid weighting by number of neighbors.
    """
    set_style()

    # Load county voting data
    county_votes = load_county_votes()
    year = 2020  # Latest available in county data
    votes = county_votes[county_votes['year'] == year][['fips', 'dem_share']].copy()

    # ===== VOTER ID BORDER ANALYSIS =====
    # Get voter ID border county sets from Census adjacency
    id_required_fips, no_id_fips, _ = _build_voter_id_border_pairs()

    # Get dem_share for each unique county (not weighted by number of neighbors)
    id_req_votes = votes[votes['fips'].isin(id_required_fips)]['dem_share'].dropna()
    no_id_votes = votes[votes['fips'].isin(no_id_fips)]['dem_share'].dropna()

    voter_id_gap = id_req_votes.mean() - no_id_votes.mean()

    # ===== WELFARE BORDER ANALYSIS =====
    # Load welfare border links and get unique counties on each side
    border_links = pd.read_csv(DATA_DIR / 'border_links.csv')
    benefit_fips = set(border_links['benefit_county_fips'].astype(str).str.zfill(5))
    nonbenefit_fips = set(border_links['nonbenefit_county_fips'].astype(str).str.zfill(5))

    benefit_votes = votes[votes['fips'].isin(benefit_fips)]['dem_share'].dropna()
    nonbenefit_votes = votes[votes['fips'].isin(nonbenefit_fips)]['dem_share'].dropna()

    welfare_gap = benefit_votes.mean() - nonbenefit_votes.mean()

    # ===== CREATE FIGURE =====
    fig, ax = plt.subplots(figsize=(8, 6))

    categories = ['Voter ID\nLaws', 'Immigrant\nWelfare Benefits']
    values = [voter_id_gap, welfare_gap]
    colors = [MAGENTA, BLUE_MID]

    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=2, width=0.6)

    # Add value labels
    for bar, val, color in zip(bars, values, colors):
        if val < 0:
            ax.annotate(f'{abs(val):.1f}pp',
                        xy=(bar.get_x() + bar.get_width() / 2, val - 0.3),
                        ha='center', va='top',
                        fontsize=16, fontweight='bold', color=color)
        else:
            ax.annotate(f'{val:.1f}pp',
                        xy=(bar.get_x() + bar.get_width() / 2, val + 0.3),
                        ha='center', va='bottom',
                        fontsize=16, fontweight='bold', color=color)

    ax.axhline(0, color='black', linewidth=1.5)
    ax.set_ylabel('Gap in Democratic Vote Share (pp)', fontsize=12)
    ax.set_ylim(-8, 10)
    ax.set_xlim(-0.5, 1.5)

    ax.set_title('Border County Vote Gap by Policy (2020)',
                 fontsize=16, fontweight='bold', pad=15)

    # Add explanation text adjacent to zero line, opposite side from bar
    ax.text(0, 0.3, f'ID-required counties vote\n{abs(voter_id_gap):.1f}pp more Republican',
            ha='center', va='bottom', fontsize=20, color=MAGENTA)
    ax.text(1, -0.3, f'Benefit-side counties vote\n{welfare_gap:.1f}pp more Democratic',
            ha='center', va='top', fontsize=20, color=BLUE_MID)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {output_path}")

    return fig


def create_border_correlation_welfare(output_path=None):
    """Create bar chart showing welfare benefits correlation in border counties.

    Uses border_links.csv which identifies county pairs across welfare policy borders.
    DEPRECATED: Use create_border_correlation() for combined figure.
    """
    set_style()

    fig, ax = plt.subplots(figsize=(6, 6))

    # Border county correlation for welfare benefits (2024)
    # Benefit counties: 36.9% Dem, Non-benefit counties: 31.9% Dem
    # Gap = +5.0pp
    categories = ['Welfare\nBenefits']
    values = [5.0]

    bars = ax.bar(categories, values, color=BLUE_MID, edgecolor='white', linewidth=2, width=0.4)

    # Add value label
    ax.annotate(f'{values[0]:.1f}pp',
                xy=(bars[0].get_x() + bars[0].get_width() / 2, values[0] + 0.3),
                ha='center', va='bottom',
                fontsize=18, fontweight='bold', color=BLUE_MID)

    ax.axhline(0, color='black', linewidth=1.5)
    ax.set_ylabel('Gap in Democratic Vote Share (pp)', fontsize=12)
    ax.set_ylim(-2, 8)
    ax.set_xlim(-0.5, 0.5)

    ax.set_title('Border County Vote Gap:\nWelfare Benefits (2024)',
                 fontsize=16, fontweight='bold', pad=15)

    # Add explanation
    ax.text(0, -1, 'Benefit-side counties vote\n5.0pp more Democratic',
            ha='center', va='top', fontsize=11, color=BLUE_MID)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {output_path}")

    return fig


def create_border_correlation_voter_id(output_path=None):
    """Create bar chart showing voter ID correlation in border counties.

    Uses Census county adjacency data to identify ALL voter ID policy borders,
    with 2-tier classification (id_strictness <= 3 = ID Required).
    """
    set_style()

    fig, ax = plt.subplots(figsize=(6, 6))

    # Border county correlation for voter ID (Census-based, 2-tier, 2024)
    # ID Required counties: 27.9% Dem, No ID counties: 31.0% Dem
    # Gap = -3.1pp
    categories = ['Voter ID\nLaws']
    values = [-3.1]

    bars = ax.bar(categories, values, color=MAGENTA, edgecolor='white', linewidth=2, width=0.4)

    # Add value label
    ax.annotate(f'{abs(values[0]):.1f}pp',
                xy=(bars[0].get_x() + bars[0].get_width() / 2, values[0] - 0.3),
                ha='center', va='top',
                fontsize=18, fontweight='bold', color=MAGENTA)

    ax.axhline(0, color='black', linewidth=1.5)
    ax.set_ylabel('Gap in Democratic Vote Share (pp)', fontsize=12)
    ax.set_ylim(-8, 2)
    ax.set_xlim(-0.5, 0.5)

    ax.set_title('Border County Vote Gap:\nVoter ID Laws (2024)',
                 fontsize=16, fontweight='bold', pad=15)

    # Add explanation
    ax.text(0, 1, 'ID-required counties vote\n3.1pp more Republican',
            ha='center', va='bottom', fontsize=11, color=MAGENTA)

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {output_path}")

    return fig


def generate_all_maps(year=2024):
    """Generate all high-contrast map figures."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print(f"Generating High-Contrast Maps ({year})")
    print("="*60)

    # State-level maps
    print("\nGenerating state-level maps...")
    create_high_contrast_maps(OUTPUT_DIR / f'high_contrast_maps_{year}.png', year=year)
    create_welfare_high_contrast_maps(OUTPUT_DIR / f'welfare_high_contrast_maps_{year}.png', year=year)
    create_unauthorized_pop_high_contrast_maps(OUTPUT_DIR / f'unauthorized_pop_high_contrast_maps_{year}.png', year=year)
    create_combined_four_panel_map(OUTPUT_DIR / f'combined_voter_id_welfare_{year}.png', year=year)
    create_voter_id_alignment_only(OUTPUT_DIR / f'voter_id_alignment_only_{year}.png', year=year)
    create_welfare_alignment_only(OUTPUT_DIR / f'welfare_alignment_only_{year}.png', year=year)
    create_high_contrast_maps_2tier(OUTPUT_DIR / f'high_contrast_maps_2tier_{year}.png', year=year)

    # Border county maps
    print("\nGenerating border county maps...")
    create_border_counties_map('voter_id', OUTPUT_DIR / f'border_counties_voter_id_{year}.png', year=year)
    create_border_counties_map('welfare', OUTPUT_DIR / f'border_counties_welfare_{year}.png', year=year)

    # Correlation bar charts
    print("\nGenerating correlation bar charts...")
    create_state_presidential_correlation(OUTPUT_DIR / 'state_presidential_correlation.png')
    create_state_house_correlation(OUTPUT_DIR / 'state_house_correlation.png')
    create_border_correlation(OUTPUT_DIR / 'border_correlation.png')

    print(f"\nAll figures saved to {OUTPUT_DIR}")
    print("="*60)


if __name__ == '__main__':
    generate_all_maps(year=2024)
