"""Visualization module for voter ID and welfare analysis."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
from pathlib import Path
from typing import Optional
import warnings

from stats import calculate_percentages, calculate_odds_ratios, calculate_welfare_score_comparison


def set_style():
    """Set consistent style for all matplotlib figures."""
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


def create_comparison_chart(df: pd.DataFrame, output_path: Optional[Path] = None) -> plt.Figure:
    """
    Create the primary narrative-driven comparison bar chart.

    Shows percentage of states offering each benefit, split by voter ID policy,
    with clear labels and annotations highlighting the gap.
    """
    set_style()

    pct_df = calculate_percentages(df)
    odds = calculate_odds_ratios(df)

    # Calculate headline stats
    no_id_avg = df[df['no_effective_id'] == 1]['welfare_score'].mean()
    id_req_avg = df[df['no_effective_id'] == 0]['welfare_score'].mean()
    multiplier = no_id_avg / id_req_avg if id_req_avg > 0 else float('inf')

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))

    # Prepare data for plotting
    benefits = ['Health', 'Food', 'Cash', 'Eitc']
    benefit_labels = ['Healthcare\n(for illegals)', 'Food Assistance\n(for illegals)', 'Cash Assistance\n(for illegals)', 'EITC\n(for illegals)']

    x = np.arange(len(benefits))
    width = 0.35

    no_id_pcts = [pct_df[(pct_df['voter_id_policy'] == 'No ID Required') &
                          (pct_df['benefit'] == b)]['percentage'].values[0] for b in benefits]
    id_req_pcts = [pct_df[(pct_df['voter_id_policy'] == 'ID Required') &
                           (pct_df['benefit'] == b)]['percentage'].values[0] for b in benefits]

    # Colors
    no_id_color = '#2E86AB'  # Blue
    id_req_color = '#A23B72'  # Magenta/pink

    # Create bars
    # Get actual counts
    n_no_id = (df['no_effective_id'] == 1).sum()
    n_id_req = (df['no_effective_id'] == 0).sum()

    bars1 = ax.bar(x - width/2, no_id_pcts, width, label=f'No ID Required ({n_no_id} states)',
                   color=no_id_color, edgecolor='white', linewidth=1.5)
    bars2 = ax.bar(x + width/2, id_req_pcts, width, label=f'ID Required ({n_id_req} states)',
                   color=id_req_color, edgecolor='white', linewidth=1.5)

    # Add value labels on bars
    for bar, pct in zip(bars1, no_id_pcts):
        height = bar.get_height()
        ax.annotate(f'{pct:.0f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold', color=no_id_color)

    for bar, pct in zip(bars2, id_req_pcts):
        height = bar.get_height()
        ax.annotate(f'{pct:.0f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold', color=id_req_color)

    # Styling
    ax.set_ylabel('Percentage of States Offering Benefit', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(benefit_labels, fontsize=11)
    ax.set_ylim(0, 105)
    ax.legend(loc='upper right', fontsize=11, frameon=True, fancybox=True, shadow=True)

    # Title with narrative framing
    ax.set_title(
        f'States Without Voter ID Offer {multiplier:.1f}x More Welfare Benefits to Illegal Immigrants',
        fontsize=16, fontweight='bold', pad=20
    )

    # Subtitle
    fig.text(0.5, 0.91, 'Percentage of states offering state-funded benefits to illegal immigrants',
             ha='center', fontsize=11, color='#666666')

    # Source footnote
    fig.text(0.02, 0.02,
             'Sources: NCSL (No-ID voting), NILC (Health, Food, Cash, EITC maps, 2023-2024)',
             fontsize=9, color='#888888', style='italic')

    plt.tight_layout()
    plt.subplots_adjust(top=0.88, bottom=0.12)

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        # Also save SVG
        svg_path = output_path.with_suffix('.svg')
        fig.savefig(svg_path, format='svg', bbox_inches='tight', facecolor='white')

    return fig


def create_strip_plot(df: pd.DataFrame, output_path: Optional[Path] = None) -> go.Figure:
    """
    Create an interactive strip plot showing state distribution across welfare scores.
    """
    # Add jitter for visibility
    df_plot = df.copy()
    np.random.seed(42)
    df_plot['jitter'] = np.random.uniform(-0.15, 0.15, len(df_plot))

    # Color mapping
    colors = {'No ID Required': '#2E86AB', 'ID Required': '#A23B72'}

    fig = go.Figure()

    for policy, color in colors.items():
        subset = df_plot[df_plot['voter_id_policy'] == policy]
        n = len(subset)

        fig.add_trace(go.Scatter(
            x=subset['welfare_score'] + subset['jitter'],
            y=[policy] * len(subset),
            mode='markers+text',
            name=f'{policy} (n={n})',
            marker=dict(size=14, color=color, line=dict(width=1, color='white')),
            text=subset['abbrev'],
            textposition='middle center',
            textfont=dict(size=8, color='white'),
            hovertemplate='<b>%{customdata[0]}</b><br>Welfare Score: %{customdata[1]}<extra></extra>',
            customdata=np.stack([subset['state'], subset['welfare_score']], axis=-1)
        ))

    # Calculate means for annotation
    no_id_mean = df[df['no_effective_id'] == 1]['welfare_score'].mean()
    id_req_mean = df[df['no_effective_id'] == 0]['welfare_score'].mean()

    # Add mean lines
    fig.add_shape(type="line", x0=no_id_mean, x1=no_id_mean,
                  y0=-0.4, y1=0.4, yref='y',
                  line=dict(color='#2E86AB', width=3, dash='dash'))
    fig.add_shape(type="line", x0=id_req_mean, x1=id_req_mean,
                  y0=0.6, y1=1.4, yref='y',
                  line=dict(color='#A23B72', width=3, dash='dash'))

    # Add mean annotations
    fig.add_annotation(x=no_id_mean, y=-0.5, text=f'Mean: {no_id_mean:.1f}',
                       showarrow=False, font=dict(color='#2E86AB', size=11))
    fig.add_annotation(x=id_req_mean, y=1.5, text=f'Mean: {id_req_mean:.1f}',
                       showarrow=False, font=dict(color='#A23B72', size=11))

    fig.update_layout(
        title=dict(
            text='Distribution of States by Welfare Benefits for Illegal Immigrants and Voter ID Policy',
            font=dict(size=16)
        ),
        xaxis=dict(
            title='Welfare Score (Number of Benefits for Illegals: 0-4)',
            tickmode='array',
            tickvals=[0, 1, 2, 3, 4],
            range=[-0.5, 4.5],
            gridcolor='#e0e0e0'
        ),
        yaxis=dict(
            title='',
            categoryorder='array',
            categoryarray=['ID Required', 'No ID Required'],
            gridcolor='#e0e0e0'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        ),
        plot_bgcolor='white',
        height=400,
        width=900
    )

    if output_path:
        fig.write_html(output_path)

    return fig


def create_choropleth_map(df: pd.DataFrame, output_path: Optional[Path] = None) -> go.Figure:
    """
    Create an interactive US choropleth map with clear visual encoding for laypeople.

    - Blue states = No ID Required for voting
    - Gray states = ID Required for voting
    - Checkmarks inside each state = number of welfare benefits (0-4)
    """
    df_plot = df.copy()

    # State centroids (approximate lat/lon for label placement)
    state_coords = {
        'AL': (32.7, -86.7), 'AK': (64.0, -153.0), 'AZ': (34.2, -111.6),
        'AR': (34.8, -92.2), 'CA': (37.2, -119.4), 'CO': (39.0, -105.5),
        'CT': (41.6, -72.7), 'DE': (39.0, -75.5), 'FL': (28.6, -82.4),
        'GA': (32.6, -83.4), 'HI': (20.8, -156.3), 'ID': (44.4, -114.6),
        'IL': (40.0, -89.2), 'IN': (39.9, -86.3), 'IA': (42.0, -93.5),
        'KS': (38.5, -98.4), 'KY': (37.8, -85.7), 'LA': (31.0, -92.0),
        'ME': (45.4, -69.2), 'MD': (39.0, -76.8), 'MA': (42.2, -71.5),
        'MI': (44.3, -85.4), 'MN': (46.3, -94.3), 'MS': (32.7, -89.7),
        'MO': (38.3, -92.5), 'MT': (47.0, -110.0), 'NE': (41.5, -99.8),
        'NV': (39.3, -116.6), 'NH': (43.6, -71.5), 'NJ': (40.2, -74.7),
        'NM': (34.5, -106.0), 'NY': (42.9, -75.5), 'NC': (35.5, -79.8),
        'ND': (47.4, -100.3), 'OH': (40.4, -82.8), 'OK': (35.6, -97.5),
        'OR': (44.0, -120.5), 'PA': (40.9, -77.8), 'RI': (41.7, -71.5),
        'SC': (33.9, -80.9), 'SD': (44.4, -100.2), 'TN': (35.8, -86.3),
        'TX': (31.5, -99.4), 'UT': (39.3, -111.7), 'VT': (44.0, -72.7),
        'VA': (37.5, -78.8), 'WA': (47.4, -120.5), 'WV': (38.9, -80.5),
        'WI': (44.6, -89.7), 'WY': (43.0, -107.5), 'DC': (38.9, -77.0)
    }

    # Create hover text
    df_plot['hover_text'] = df_plot.apply(
        lambda r: f"<b>{r['state']}</b><br>" +
                  f"Voter ID: {'No ID Required' if r['no_effective_id'] else 'ID Required'}<br>" +
                  f"Welfare Benefits for Illegals: {r['welfare_score']}/4<br>" +
                  f"---<br>" +
                  f"Healthcare: {'✓' if r['health'] else '✗'}<br>" +
                  f"Food: {'✓' if r['food'] else '✗'}<br>" +
                  f"Cash: {'✓' if r['cash'] else '✗'}<br>" +
                  f"EITC: {'✓' if r['eitc'] else '✗'}",
        axis=1
    )

    # Simple two-color scheme
    # No ID Required = 1 (blue), ID Required = 0 (gray)
    colorscale = [[0, '#E0E0E0'], [1, '#2E86AB']]

    fig = go.Figure()

    # Add choropleth layer
    fig.add_trace(go.Choropleth(
        locations=df_plot['abbrev'],
        z=df_plot['no_effective_id'],
        locationmode='USA-states',
        colorscale=colorscale,
        zmin=0,
        zmax=1,
        showscale=False,
        hovertemplate='%{customdata}<extra></extra>',
        customdata=df_plot['hover_text'],
        marker_line_color='white',
        marker_line_width=1
    ))

    # Add text annotations for each state
    annotations = []
    for _, row in df_plot.iterrows():
        abbrev = row['abbrev']
        if abbrev not in state_coords:
            continue

        lat, lon = state_coords[abbrev]
        welfare_score = int(row['welfare_score'])
        is_no_id = row['no_effective_id'] == 1

        # Create checkmarks string
        checkmarks = '✓' * welfare_score if welfare_score > 0 else '—'

        # Text color: white on blue, dark on gray
        text_color = 'white' if is_no_id else '#333333'

        # Combine abbreviation and checkmarks
        label_text = f"<b>{abbrev}</b><br>{checkmarks}"

        annotations.append(dict(
            x=lon,
            y=lat,
            xref='x',
            yref='y',
            text=label_text,
            showarrow=False,
            font=dict(size=9, color=text_color, family='Arial'),
            align='center'
        ))

    # Calculate stats for title
    no_id_avg = df_plot[df_plot['no_effective_id'] == 1]['welfare_score'].mean()
    id_req_avg = df_plot[df_plot['no_effective_id'] == 0]['welfare_score'].mean()

    fig.update_layout(
        title=dict(
            text=f'Voter ID Requirements & Welfare Benefits for Illegal Immigrants by State<br>' +
                 f'<sub>Blue states (No ID Required) average {no_id_avg:.1f} benefits for illegals vs {id_req_avg:.1f} in gray states</sub>',
            font=dict(size=16),
            x=0.5
        ),
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
            bgcolor='rgba(0,0,0,0)'
        ),
        annotations=[
            # Legend
            dict(x=0.02, y=0.15, xref='paper', yref='paper',
                 text='<b>Legend</b>', showarrow=False,
                 font=dict(size=12, color='#333333'), align='left'),
            dict(x=0.02, y=0.10, xref='paper', yref='paper',
                 text='<span style="color:#2E86AB">■</span> No ID Required',
                 showarrow=False, font=dict(size=11), align='left'),
            dict(x=0.02, y=0.05, xref='paper', yref='paper',
                 text='<span style="color:#E0E0E0">■</span> ID Required',
                 showarrow=False, font=dict(size=11), align='left'),
            dict(x=0.02, y=0.00, xref='paper', yref='paper',
                 text='✓ = 1 welfare benefit',
                 showarrow=False, font=dict(size=11), align='left'),
        ],
        height=650,
        width=1000
    )

    if output_path:
        fig.write_html(output_path)

    return fig


def create_static_map(df: pd.DataFrame, output_path: Optional[Path] = None) -> plt.Figure:
    """
    Create a static US map with proper state boundaries using geopandas.
    - Colors: 5 shades based on ID strictness (darker = looser ID laws)
    - Symbols: Individual letters for each welfare type (H, F, C, E)
    """
    set_style()
    warnings.filterwarnings('ignore', category=UserWarning)

    # Load US states shapefile from Census Bureau
    us_states_url = "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_5m.zip"

    try:
        states_gdf = gpd.read_file(us_states_url)
    except Exception as e:
        print(f"Error loading shapefile: {e}")
        print("Falling back to simple visualization...")
        return None

    # Filter to just US states (exclude territories)
    states_gdf = states_gdf[states_gdf['STATEFP'].astype(int) <= 56]

    # Merge with our data
    states_gdf = states_gdf.merge(df, left_on='STUSPS', right_on='abbrev', how='left')

    # Fill NaN values
    states_gdf['id_strictness'] = states_gdf['id_strictness'].fillna(3)
    states_gdf['welfare_score'] = states_gdf['welfare_score'].fillna(0)
    for col in ['health', 'food', 'cash', 'eitc']:
        states_gdf[col] = states_gdf[col].fillna(0)

    # Project to Albers Equal Area for proper US visualization
    states_gdf = states_gdf.to_crs('ESRI:102003')

    # 5 shades: Tier 1 (strictest) = lightest, Tier 5 (loosest) = darkest
    # Using a blue gradient
    strictness_colors = {
        1: '#deebf7',  # Lightest - Strict Photo ID
        2: '#9ecae1',  # Light - Strict Non-Photo ID
        3: '#4292c6',  # Medium - Non-Strict Photo ID
        4: '#2171b5',  # Dark - Non-Strict Non-Photo ID
        5: '#084594'   # Darkest - No Document Required
    }

    # Separate Alaska and Hawaii for repositioning
    continental = states_gdf[~states_gdf['STUSPS'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])]
    alaska = states_gdf[states_gdf['STUSPS'] == 'AK'].copy()
    hawaii = states_gdf[states_gdf['STUSPS'] == 'HI'].copy()

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10))

    def get_color(strictness):
        return strictness_colors.get(int(strictness), '#4292c6')

    def get_text_color(strictness):
        # White text for darker shades (3, 4, 5), dark text for lighter (1, 2)
        return 'white' if strictness >= 3 else '#333333'

    def get_welfare_symbols(row):
        """Build string of welfare type symbols: H=Health, F=Food, C=Cash, E=EITC"""
        symbols = []
        if row.get('health', 0) == 1:
            symbols.append('H')
        if row.get('food', 0) == 1:
            symbols.append('F')
        if row.get('cash', 0) == 1:
            symbols.append('C')
        if row.get('eitc', 0) == 1:
            symbols.append('E')
        return ' '.join(symbols) if symbols else ''

    # Plot continental states
    for idx, row in continental.iterrows():
        strictness = row['id_strictness'] if pd.notna(row['id_strictness']) else 3
        color = get_color(strictness)
        continental[continental.index == idx].plot(
            ax=ax, color=color, edgecolor='white', linewidth=0.8
        )

    # Transform and plot Alaska
    if not alaska.empty:
        alaska_scaled = alaska.copy()
        alaska_scaled.geometry = alaska_scaled.geometry.scale(0.35, 0.35, origin=(0, 0))
        alaska_scaled.geometry = alaska_scaled.geometry.translate(-1800000, -1400000)
        strictness = alaska['id_strictness'].values[0] if pd.notna(alaska['id_strictness'].values[0]) else 3
        alaska_scaled.plot(ax=ax, color=get_color(strictness), edgecolor='white', linewidth=0.8)

    # Transform and plot Hawaii
    if not hawaii.empty:
        hawaii_scaled = hawaii.copy()
        hawaii_scaled.geometry = hawaii_scaled.geometry.scale(1.0, 1.0, origin=(0, 0))
        hawaii_scaled.geometry = hawaii_scaled.geometry.translate(5200000, -1200000)
        strictness = hawaii['id_strictness'].values[0] if pd.notna(hawaii['id_strictness'].values[0]) else 3
        hawaii_scaled.plot(ax=ax, color=get_color(strictness), edgecolor='white', linewidth=0.8)

    # Add welfare symbols to states (no abbreviations)
    for idx, row in continental.iterrows():
        centroid = row.geometry.centroid
        strictness = row['id_strictness'] if pd.notna(row['id_strictness']) else 3
        text_color = get_text_color(strictness)
        welfare_symbols = get_welfare_symbols(row)

        # Welfare symbols (H F C E) - centered in state
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(centroid.x, centroid.y),
                        ha='center', va='center', fontsize=12, fontweight='bold',
                        color=text_color)

    # Add Alaska welfare symbols
    if not alaska.empty:
        row = alaska.iloc[0]
        strictness = row['id_strictness'] if pd.notna(row['id_strictness']) else 3
        text_color = get_text_color(strictness)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-2050000, -1780000), ha='center', va='center',
                        fontsize=12, fontweight='bold', color=text_color)

    # Add Hawaii welfare symbols
    if not hawaii.empty:
        row = hawaii.iloc[0]
        strictness = row['id_strictness'] if pd.notna(row['id_strictness']) else 3
        text_color = get_text_color(strictness)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-1050000, -1680000), ha='center', va='center',
                        fontsize=12, fontweight='bold', color=text_color)

    # Title
    ax.set_title('Voter ID Strictness & Welfare Benefits for Illegal Immigrants',
                 fontsize=18, fontweight='bold', pad=20)

    # Create legend for colors (ID strictness) - positioned at lower left
    legend_elements = [
        mpatches.Patch(facecolor=strictness_colors[5], edgecolor='#666', label='No ID Required'),
        mpatches.Patch(facecolor=strictness_colors[4], edgecolor='#666', label='Non-Strict Non-Photo'),
        mpatches.Patch(facecolor=strictness_colors[3], edgecolor='#666', label='Non-Strict Photo'),
        mpatches.Patch(facecolor=strictness_colors[2], edgecolor='#666', label='Strict Non-Photo'),
        mpatches.Patch(facecolor=strictness_colors[1], edgecolor='#666', label='Strict Photo ID'),
    ]
    legend1 = ax.legend(handles=legend_elements, loc='lower left', fontsize=10,
                        frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                        title='Voter ID Requirements', title_fontsize=11,
                        bbox_to_anchor=(0.12, 0.01))
    legend1.get_frame().set_facecolor('white')
    legend1.get_frame().set_edgecolor('#cccccc')
    ax.add_artist(legend1)

    # Create welfare benefits legend with same style - positioned adjacent to voter ID legend
    from matplotlib.lines import Line2D
    welfare_elements = [
        Line2D([0], [0], marker='$H$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='Healthcare'),
        Line2D([0], [0], marker='$F$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='Food Assistance'),
        Line2D([0], [0], marker='$C$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='Cash Assistance'),
        Line2D([0], [0], marker='$E$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='EITC Tax Credit'),
    ]
    legend2 = ax.legend(handles=welfare_elements, loc='lower left', fontsize=10,
                        frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                        title='Benefits for Illegals', title_fontsize=11,
                        bbox_to_anchor=(0.33, 0.01), handletextpad=0.5)
    legend2.get_frame().set_facecolor('white')
    legend2.get_frame().set_edgecolor('#cccccc')
    ax.add_artist(legend2)

    ax.axis('off')
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

    return fig


def create_static_map_3tier(df: pd.DataFrame, output_path: Optional[Path] = None) -> plt.Figure:
    """
    Create a static US map with 3-tier voter ID classification.
    - Tier 1 (Strict): Old tiers 1-2 - Must show ID
    - Tier 2 (Non-Strict): Old tier 3 - ID requested, alternatives allowed
    - Tier 3 (Weak/None): Old tiers 4-5 - Minimal or no ID requirement
    """
    set_style()
    warnings.filterwarnings('ignore', category=UserWarning)

    # Load US states shapefile from Census Bureau
    us_states_url = "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_5m.zip"

    try:
        states_gdf = gpd.read_file(us_states_url)
    except Exception as e:
        print(f"Error loading shapefile: {e}")
        return None

    # Filter to just US states (exclude territories)
    states_gdf = states_gdf[states_gdf['STATEFP'].astype(int) <= 56]

    # Merge with our data
    states_gdf = states_gdf.merge(df, left_on='STUSPS', right_on='abbrev', how='left')

    # Fill NaN values
    states_gdf['id_strictness'] = states_gdf['id_strictness'].fillna(3)
    states_gdf['welfare_score'] = states_gdf['welfare_score'].fillna(0)
    for col in ['health', 'food', 'cash', 'eitc']:
        states_gdf[col] = states_gdf[col].fillna(0)

    # Collapse 5 tiers into 3
    def collapse_tier(tier):
        tier = int(tier)
        if tier <= 2:
            return 1  # Strict (old 1-2)
        elif tier == 3:
            return 2  # Non-Strict (old 3)
        else:
            return 3  # Weak/None (old 4-5)

    states_gdf['tier_3'] = states_gdf['id_strictness'].apply(collapse_tier)

    # Project to Albers Equal Area for proper US visualization
    states_gdf = states_gdf.to_crs('ESRI:102003')

    # 3-color gradient: lightest (strict) to darkest (weak/none)
    tier_colors = {
        1: '#deebf7',  # Lightest - Strict (must show ID)
        2: '#6baed6',  # Medium - Non-Strict (alternatives allowed)
        3: '#084594'   # Darkest - Weak/None (minimal or no ID)
    }

    # Separate Alaska and Hawaii for repositioning
    continental = states_gdf[~states_gdf['STUSPS'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])]
    alaska = states_gdf[states_gdf['STUSPS'] == 'AK'].copy()
    hawaii = states_gdf[states_gdf['STUSPS'] == 'HI'].copy()

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10))

    def get_color(tier):
        return tier_colors.get(int(tier), '#6baed6')

    def get_text_color(tier):
        return 'white' if tier >= 2 else '#333333'

    def get_welfare_symbols(row):
        symbols = []
        if row.get('health', 0) == 1:
            symbols.append('H')
        if row.get('food', 0) == 1:
            symbols.append('F')
        if row.get('cash', 0) == 1:
            symbols.append('C')
        if row.get('eitc', 0) == 1:
            symbols.append('E')
        return ' '.join(symbols) if symbols else ''

    # Plot continental states
    for idx, row in continental.iterrows():
        tier = row['tier_3']
        color = get_color(tier)
        continental[continental.index == idx].plot(
            ax=ax, color=color, edgecolor='white', linewidth=0.8
        )

    # Transform and plot Alaska
    if not alaska.empty:
        alaska_scaled = alaska.copy()
        alaska_scaled.geometry = alaska_scaled.geometry.scale(0.35, 0.35, origin=(0, 0))
        alaska_scaled.geometry = alaska_scaled.geometry.translate(-1800000, -1400000)
        tier = collapse_tier(alaska['id_strictness'].values[0]) if pd.notna(alaska['id_strictness'].values[0]) else 2
        alaska_scaled.plot(ax=ax, color=get_color(tier), edgecolor='white', linewidth=0.8)

    # Transform and plot Hawaii
    if not hawaii.empty:
        hawaii_scaled = hawaii.copy()
        hawaii_scaled.geometry = hawaii_scaled.geometry.scale(1.0, 1.0, origin=(0, 0))
        hawaii_scaled.geometry = hawaii_scaled.geometry.translate(5200000, -1200000)
        tier = collapse_tier(hawaii['id_strictness'].values[0]) if pd.notna(hawaii['id_strictness'].values[0]) else 2
        hawaii_scaled.plot(ax=ax, color=get_color(tier), edgecolor='white', linewidth=0.8)

    # Add welfare symbols to states
    for idx, row in continental.iterrows():
        centroid = row.geometry.centroid
        tier = row['tier_3']
        text_color = get_text_color(tier)
        welfare_symbols = get_welfare_symbols(row)

        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(centroid.x, centroid.y),
                        ha='center', va='center', fontsize=12, fontweight='bold',
                        color=text_color)

    # Add Alaska welfare symbols
    if not alaska.empty:
        row = alaska.iloc[0]
        tier = collapse_tier(row['id_strictness']) if pd.notna(row['id_strictness']) else 2
        text_color = get_text_color(tier)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-2050000, -1780000), ha='center', va='center',
                        fontsize=12, fontweight='bold', color=text_color)

    # Add Hawaii welfare symbols
    if not hawaii.empty:
        row = hawaii.iloc[0]
        tier = collapse_tier(row['id_strictness']) if pd.notna(row['id_strictness']) else 2
        text_color = get_text_color(tier)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-1050000, -1680000), ha='center', va='center',
                        fontsize=12, fontweight='bold', color=text_color)

    # Title
    ax.set_title('Voter ID Strictness & Welfare Benefits for Illegal Immigrants',
                 fontsize=18, fontweight='bold', pad=20)

    # Create legend for colors (3-tier)
    legend_elements = [
        mpatches.Patch(facecolor=tier_colors[3], edgecolor='#666', label='Weak / No ID Required'),
        mpatches.Patch(facecolor=tier_colors[2], edgecolor='#666', label='Non-Strict ID'),
        mpatches.Patch(facecolor=tier_colors[1], edgecolor='#666', label='Strict ID Required'),
    ]
    legend1 = ax.legend(handles=legend_elements, loc='lower left', fontsize=10,
                        frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                        title='Voter ID Requirements', title_fontsize=11,
                        bbox_to_anchor=(0.12, 0.01))
    legend1.get_frame().set_facecolor('white')
    legend1.get_frame().set_edgecolor('#cccccc')
    ax.add_artist(legend1)

    # Create welfare benefits legend
    from matplotlib.lines import Line2D
    welfare_elements = [
        Line2D([0], [0], marker='$H$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='Healthcare'),
        Line2D([0], [0], marker='$F$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='Food Assistance'),
        Line2D([0], [0], marker='$C$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='Cash Assistance'),
        Line2D([0], [0], marker='$E$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='EITC Tax Credit'),
    ]
    legend2 = ax.legend(handles=welfare_elements, loc='lower left', fontsize=10,
                        frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                        title='Benefits for Illegals', title_fontsize=11,
                        bbox_to_anchor=(0.29, 0.01), handletextpad=0.5)
    legend2.get_frame().set_facecolor('white')
    legend2.get_frame().set_edgecolor('#cccccc')
    ax.add_artist(legend2)

    ax.axis('off')
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

    return fig


def create_static_map_2tier(df: pd.DataFrame, output_path: Optional[Path] = None) -> plt.Figure:
    """
    Create a static US map with 2-tier voter ID classification.
    - Tier 1: Old tiers 1-3 - ID verification required (strict or non-strict)
    - Tier 2: Old tiers 4-5 - No effective ID requirement (affidavit or no document)
    """
    set_style()
    warnings.filterwarnings('ignore', category=UserWarning)

    us_states_url = "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_5m.zip"

    try:
        states_gdf = gpd.read_file(us_states_url)
    except Exception as e:
        print(f"Error loading shapefile: {e}")
        return None

    states_gdf = states_gdf[states_gdf['STATEFP'].astype(int) <= 56]
    states_gdf = states_gdf.merge(df, left_on='STUSPS', right_on='abbrev', how='left')

    states_gdf['id_strictness'] = states_gdf['id_strictness'].fillna(3)
    states_gdf['welfare_score'] = states_gdf['welfare_score'].fillna(0)
    for col in ['health', 'food', 'cash', 'eitc']:
        states_gdf[col] = states_gdf[col].fillna(0)

    # Collapse 5 tiers into 2
    def collapse_tier(tier):
        tier = int(tier)
        if tier <= 3:
            return 1  # ID verification required
        else:
            return 2  # No effective ID requirement

    states_gdf['tier_2'] = states_gdf['id_strictness'].apply(collapse_tier)
    states_gdf = states_gdf.to_crs('ESRI:102003')

    # 2-color: light (ID required) vs dark (no effective ID)
    tier_colors = {
        1: '#deebf7',  # Light - ID verification required
        2: '#084594'   # Dark - No effective ID requirement
    }

    continental = states_gdf[~states_gdf['STUSPS'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])]
    alaska = states_gdf[states_gdf['STUSPS'] == 'AK'].copy()
    hawaii = states_gdf[states_gdf['STUSPS'] == 'HI'].copy()

    fig, ax = plt.subplots(figsize=(16, 10))

    def get_color(tier):
        return tier_colors.get(int(tier), '#deebf7')

    def get_text_color(tier):
        return 'white' if tier == 2 else '#333333'

    def get_welfare_symbols(row):
        symbols = []
        if row.get('health', 0) == 1:
            symbols.append('H')
        if row.get('food', 0) == 1:
            symbols.append('F')
        if row.get('cash', 0) == 1:
            symbols.append('C')
        if row.get('eitc', 0) == 1:
            symbols.append('E')
        return ' '.join(symbols) if symbols else ''

    for idx, row in continental.iterrows():
        tier = row['tier_2']
        color = get_color(tier)
        continental[continental.index == idx].plot(
            ax=ax, color=color, edgecolor='white', linewidth=0.8
        )

    if not alaska.empty:
        alaska_scaled = alaska.copy()
        alaska_scaled.geometry = alaska_scaled.geometry.scale(0.35, 0.35, origin=(0, 0))
        alaska_scaled.geometry = alaska_scaled.geometry.translate(-1800000, -1400000)
        tier = collapse_tier(alaska['id_strictness'].values[0]) if pd.notna(alaska['id_strictness'].values[0]) else 1
        alaska_scaled.plot(ax=ax, color=get_color(tier), edgecolor='white', linewidth=0.8)

    if not hawaii.empty:
        hawaii_scaled = hawaii.copy()
        hawaii_scaled.geometry = hawaii_scaled.geometry.scale(1.0, 1.0, origin=(0, 0))
        hawaii_scaled.geometry = hawaii_scaled.geometry.translate(5200000, -1200000)
        tier = collapse_tier(hawaii['id_strictness'].values[0]) if pd.notna(hawaii['id_strictness'].values[0]) else 1
        hawaii_scaled.plot(ax=ax, color=get_color(tier), edgecolor='white', linewidth=0.8)

    for idx, row in continental.iterrows():
        centroid = row.geometry.centroid
        tier = row['tier_2']
        text_color = get_text_color(tier)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(centroid.x, centroid.y),
                        ha='center', va='center', fontsize=12, fontweight='bold',
                        color=text_color)

    if not alaska.empty:
        row = alaska.iloc[0]
        tier = collapse_tier(row['id_strictness']) if pd.notna(row['id_strictness']) else 1
        text_color = get_text_color(tier)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-2050000, -1780000), ha='center', va='center',
                        fontsize=12, fontweight='bold', color=text_color)

    if not hawaii.empty:
        row = hawaii.iloc[0]
        tier = collapse_tier(row['id_strictness']) if pd.notna(row['id_strictness']) else 1
        text_color = get_text_color(tier)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-1050000, -1680000), ha='center', va='center',
                        fontsize=12, fontweight='bold', color=text_color)

    ax.set_title('Voter ID Strictness & Welfare Benefits for Illegal Immigrants',
                 fontsize=18, fontweight='bold', pad=20)

    legend_elements = [
        mpatches.Patch(facecolor=tier_colors[2], edgecolor='#666', label='No Effective ID Requirement'),
        mpatches.Patch(facecolor=tier_colors[1], edgecolor='#666', label='ID Verification Required'),
    ]
    legend1 = ax.legend(handles=legend_elements, loc='lower left', fontsize=10,
                        frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                        title='Voter ID Requirements', title_fontsize=11,
                        bbox_to_anchor=(0.12, 0.01))
    legend1.get_frame().set_facecolor('white')
    legend1.get_frame().set_edgecolor('#cccccc')
    ax.add_artist(legend1)

    from matplotlib.lines import Line2D
    welfare_elements = [
        Line2D([0], [0], marker='$H$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='Healthcare'),
        Line2D([0], [0], marker='$F$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='Food Assistance'),
        Line2D([0], [0], marker='$C$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='Cash Assistance'),
        Line2D([0], [0], marker='$E$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='EITC Tax Credit'),
    ]
    legend2 = ax.legend(handles=welfare_elements, loc='lower left', fontsize=10,
                        frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                        title='Benefits for Illegals', title_fontsize=11,
                        bbox_to_anchor=(0.29, 0.01), handletextpad=0.5)
    legend2.get_frame().set_facecolor('white')
    legend2.get_frame().set_edgecolor('#cccccc')
    ax.add_artist(legend2)

    ax.axis('off')
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

    return fig


def create_all_visualizations(df: pd.DataFrame, output_dir: Path):
    """Generate all visualizations and save to output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Creating comparison bar chart...")
    create_comparison_chart(df, output_dir / "comparison_chart.png")

    print("Creating strip plot...")
    create_strip_plot(df, output_dir / "strip_plot.html")

    print("Creating interactive choropleth map...")
    create_choropleth_map(df, output_dir / "choropleth_map.html")

    print("Creating static state map with checkmarks...")
    create_static_map(df, output_dir / "state_map.png")

    print(f"All visualizations saved to {output_dir}")


if __name__ == "__main__":
    from prepare_data import load_and_prepare

    df = load_and_prepare()
    output_dir = Path(__file__).parent.parent / "output"
    create_all_visualizations(df, output_dir)
