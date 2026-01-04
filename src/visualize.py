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

    # Calculate headline stats using adults score
    no_id_avg = df[df['no_effective_id'] == 1]['welfare_score_adults'].mean()
    id_req_avg = df[df['no_effective_id'] == 0]['welfare_score_adults'].mean()
    multiplier = no_id_avg / id_req_avg if id_req_avg > 0 else float('inf')

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))

    # Prepare data for plotting - new column names
    benefits = ['health_adults', 'health_children', 'health_seniors', 'food', 'eitc']
    benefit_labels = [
        'Healthcare\n(Adults)',
        'Healthcare\n(Children)',
        'Healthcare\n(Seniors 65+)',
        'Food\nAssistance',
        'EITC\n(ITIN Filers)'
    ]

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
                    fontsize=11, fontweight='bold', color=no_id_color)

    for bar, pct in zip(bars2, id_req_pcts):
        height = bar.get_height()
        ax.annotate(f'{pct:.0f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=11, fontweight='bold', color=id_req_color)

    # Styling
    ax.set_ylabel('Percentage of States Offering Benefit', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(benefit_labels, fontsize=10)
    ax.set_ylim(0, 105)
    ax.legend(loc='upper right', fontsize=11, frameon=True, fancybox=True, shadow=True)

    # Title with narrative framing
    if id_req_avg > 0:
        title_text = f'States Without Voter ID Offer {multiplier:.1f}x More Benefits to Illegal Immigrant Adults'
    else:
        title_text = 'States Without Voter ID Exclusively Offer Benefits to Illegal Immigrant Adults'
    ax.set_title(title_text, fontsize=15, fontweight='bold', pad=20)

    # Subtitle
    fig.text(0.5, 0.91, 'Percentage of states offering state-funded benefits to illegal immigrants',
             ha='center', fontsize=11, color='#666666')

    # Source footnote
    fig.text(0.02, 0.02,
             'Sources: NCSL (Voter ID), KFF/NILC (Health), NILC (Food), ITEP (EITC) - 2024',
             fontsize=9, color='#888888', style='italic')

    plt.tight_layout()
    plt.subplots_adjust(top=0.88, bottom=0.12)

    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        svg_path = output_path.with_suffix('.svg')
        fig.savefig(svg_path, format='svg', bbox_inches='tight', facecolor='white')

    return fig


def create_strip_plot(df: pd.DataFrame, output_path: Optional[Path] = None) -> go.Figure:
    """
    Create an interactive strip plot showing state distribution across welfare scores.
    """
    df_plot = df.copy()
    np.random.seed(42)
    df_plot['jitter'] = np.random.uniform(-0.15, 0.15, len(df_plot))

    colors = {'No ID Required': '#2E86AB', 'ID Required': '#A23B72'}

    fig = go.Figure()

    for policy, color in colors.items():
        subset = df_plot[df_plot['voter_id_policy'] == policy]
        n = len(subset)

        fig.add_trace(go.Scatter(
            x=subset['welfare_score_adults'] + subset['jitter'],
            y=[policy] * len(subset),
            mode='markers+text',
            name=f'{policy} (n={n})',
            marker=dict(size=14, color=color, line=dict(width=1, color='white')),
            text=subset['abbrev'],
            textposition='middle center',
            textfont=dict(size=8, color='white'),
            hovertemplate='<b>%{customdata[0]}</b><br>Welfare Score: %{customdata[1]}<extra></extra>',
            customdata=np.stack([subset['state'], subset['welfare_score_adults']], axis=-1)
        ))

    # Calculate means for annotation
    no_id_mean = df[df['no_effective_id'] == 1]['welfare_score_adults'].mean()
    id_req_mean = df[df['no_effective_id'] == 0]['welfare_score_adults'].mean()

    # Add mean lines
    fig.add_shape(type="line", x0=no_id_mean, x1=no_id_mean,
                  y0=-0.4, y1=0.4, yref='y',
                  line=dict(color='#2E86AB', width=3, dash='dash'))
    fig.add_shape(type="line", x0=id_req_mean, x1=id_req_mean,
                  y0=0.6, y1=1.4, yref='y',
                  line=dict(color='#A23B72', width=3, dash='dash'))

    # Add mean annotations
    fig.add_annotation(x=no_id_mean, y=-0.5, text=f'Mean: {no_id_mean:.2f}',
                       showarrow=False, font=dict(color='#2E86AB', size=11))
    fig.add_annotation(x=id_req_mean, y=1.5, text=f'Mean: {id_req_mean:.2f}',
                       showarrow=False, font=dict(color='#A23B72', size=11))

    fig.update_layout(
        title=dict(
            text='Distribution of States by Welfare Benefits for Illegal Immigrant Adults',
            font=dict(size=16)
        ),
        xaxis=dict(
            title='Welfare Score (health_adults + food + eitc: 0-3)',
            tickmode='array',
            tickvals=[0, 1, 2, 3],
            range=[-0.5, 3.5],
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
    Create an interactive US choropleth map with clear visual encoding.
    """
    df_plot = df.copy()

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

    # Create hover text with new columns
    df_plot['hover_text'] = df_plot.apply(
        lambda r: f"<b>{r['state']}</b><br>" +
                  f"Voter ID: {'No ID Required' if r['no_effective_id'] else 'ID Required'}<br>" +
                  f"Adults Welfare Score: {r['welfare_score_adults']}/3<br>" +
                  f"---<br>" +
                  f"Health (adults): {'Yes' if r['health_adults'] else 'No'}<br>" +
                  f"Health (children): {'Yes' if r['health_children'] else 'No'}<br>" +
                  f"Health (seniors): {'Yes' if r['health_seniors'] else 'No'}<br>" +
                  f"Food: {'Yes' if r['food'] else 'No'}<br>" +
                  f"EITC: {'Yes' if r['eitc'] else 'No'}",
        axis=1
    )

    colorscale = [[0, '#E0E0E0'], [1, '#2E86AB']]

    fig = go.Figure()

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

    no_id_avg = df_plot[df_plot['no_effective_id'] == 1]['welfare_score_adults'].mean()
    id_req_avg = df_plot[df_plot['no_effective_id'] == 0]['welfare_score_adults'].mean()

    fig.update_layout(
        title=dict(
            text=f'Voter ID Requirements & Welfare Benefits for Illegal Immigrant Adults<br>' +
                 f'<sub>Blue states (No ID Required) average {no_id_avg:.2f} benefits vs {id_req_avg:.2f} in gray states</sub>',
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
            dict(x=0.02, y=0.15, xref='paper', yref='paper',
                 text='<b>Legend</b>', showarrow=False,
                 font=dict(size=12, color='#333333'), align='left'),
            dict(x=0.02, y=0.10, xref='paper', yref='paper',
                 text='<span style="color:#2E86AB">Blue</span> = No ID Required',
                 showarrow=False, font=dict(size=11), align='left'),
            dict(x=0.02, y=0.05, xref='paper', yref='paper',
                 text='<span style="color:#E0E0E0">Gray</span> = ID Required',
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
    - Symbols: Individual letters for each welfare type (A=Adults health, C=Children, S=Seniors, F=Food, E=EITC)
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
    states_gdf['welfare_score_adults'] = states_gdf['welfare_score_adults'].fillna(0)
    for col in ['health_children', 'health_adults', 'health_seniors', 'food', 'eitc']:
        states_gdf[col] = states_gdf[col].fillna(0)

    states_gdf = states_gdf.to_crs('ESRI:102003')

    strictness_colors = {
        1: '#deebf7',
        2: '#9ecae1',
        3: '#4292c6',
        4: '#2171b5',
        5: '#084594'
    }

    continental = states_gdf[~states_gdf['STUSPS'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])]
    alaska = states_gdf[states_gdf['STUSPS'] == 'AK'].copy()
    hawaii = states_gdf[states_gdf['STUSPS'] == 'HI'].copy()

    fig, ax = plt.subplots(figsize=(16, 10))

    def get_color(strictness):
        return strictness_colors.get(int(strictness), '#4292c6')

    def get_text_color(strictness):
        return 'white' if strictness >= 3 else '#333333'

    def get_welfare_symbols(row):
        """Build string of welfare type symbols"""
        symbols = []
        if row.get('health_adults', 0) == 1:
            symbols.append('Ha')  # Healthcare adults
        if row.get('health_children', 0) == 1:
            symbols.append('Hc')  # Healthcare children
        if row.get('health_adults', 0) == 1 or row.get('health_seniors', 0) == 1:
            symbols.append('Hs')  # Healthcare seniors (included in adults coverage or seniors-only)
        if row.get('food', 0) == 1:
            symbols.append('F')
        if row.get('eitc', 0) == 1:
            symbols.append('E')
        return ' '.join(symbols) if symbols else ''

    for idx, row in continental.iterrows():
        strictness = row['id_strictness'] if pd.notna(row['id_strictness']) else 3
        color = get_color(strictness)
        continental[continental.index == idx].plot(
            ax=ax, color=color, edgecolor='white', linewidth=0.8
        )

    if not alaska.empty:
        alaska_scaled = alaska.copy()
        alaska_scaled.geometry = alaska_scaled.geometry.scale(0.35, 0.35, origin=(0, 0))
        alaska_scaled.geometry = alaska_scaled.geometry.translate(-1800000, -1400000)
        strictness = alaska['id_strictness'].values[0] if pd.notna(alaska['id_strictness'].values[0]) else 3
        alaska_scaled.plot(ax=ax, color=get_color(strictness), edgecolor='white', linewidth=0.8)

    if not hawaii.empty:
        hawaii_scaled = hawaii.copy()
        hawaii_scaled.geometry = hawaii_scaled.geometry.scale(1.0, 1.0, origin=(0, 0))
        hawaii_scaled.geometry = hawaii_scaled.geometry.translate(5200000, -1200000)
        strictness = hawaii['id_strictness'].values[0] if pd.notna(hawaii['id_strictness'].values[0]) else 3
        hawaii_scaled.plot(ax=ax, color=get_color(strictness), edgecolor='white', linewidth=0.8)

    for idx, row in continental.iterrows():
        centroid = row.geometry.centroid
        strictness = row['id_strictness'] if pd.notna(row['id_strictness']) else 3
        text_color = get_text_color(strictness)
        welfare_symbols = get_welfare_symbols(row)

        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(centroid.x, centroid.y),
                        ha='center', va='center', fontsize=10, fontweight='bold',
                        color=text_color)

    if not alaska.empty:
        row = alaska.iloc[0]
        strictness = row['id_strictness'] if pd.notna(row['id_strictness']) else 3
        text_color = get_text_color(strictness)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-2050000, -1780000), ha='center', va='center',
                        fontsize=10, fontweight='bold', color=text_color)

    if not hawaii.empty:
        row = hawaii.iloc[0]
        strictness = row['id_strictness'] if pd.notna(row['id_strictness']) else 3
        text_color = get_text_color(strictness)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-1050000, -1680000), ha='center', va='center',
                        fontsize=10, fontweight='bold', color=text_color)

    ax.set_title('Voter ID Strictness & Welfare Benefits for Illegal Immigrants',
                 fontsize=18, fontweight='bold', pad=20)

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
                        bbox_to_anchor=(0.10, 0.01))
    legend1.get_frame().set_facecolor('white')
    legend1.get_frame().set_edgecolor('#cccccc')
    ax.add_artist(legend1)

    from matplotlib.lines import Line2D
    welfare_elements = [
        Line2D([0], [0], marker='$Ha$', color='w', linestyle='', markersize=12,
               markerfacecolor='#333', markeredgecolor='#333', label='Ha = Health (Adults)'),
        Line2D([0], [0], marker='$Hc$', color='w', linestyle='', markersize=12,
               markerfacecolor='#333', markeredgecolor='#333', label='Hc = Health (Children)'),
        Line2D([0], [0], marker='$Hs$', color='w', linestyle='', markersize=12,
               markerfacecolor='#333', markeredgecolor='#333', label='Hs = Health (Seniors 65+)'),
        Line2D([0], [0], marker='$F$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='F = Food Assistance'),
        Line2D([0], [0], marker='$E$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='E = EITC (ITIN filers)'),
    ]
    legend2 = ax.legend(handles=welfare_elements, loc='lower left', fontsize=10,
                        frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                        title='Benefits for Illegal Immigrants', title_fontsize=11,
                        bbox_to_anchor=(0.30, 0.01), handletextpad=0.5)
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
    states_gdf['welfare_score_adults'] = states_gdf['welfare_score_adults'].fillna(0)
    for col in ['health_children', 'health_adults', 'health_seniors', 'food', 'eitc']:
        states_gdf[col] = states_gdf[col].fillna(0)

    def collapse_tier(tier):
        tier = int(tier)
        if tier <= 3:
            return 1
        else:
            return 2

    states_gdf['tier_2'] = states_gdf['id_strictness'].apply(collapse_tier)
    states_gdf = states_gdf.to_crs('ESRI:102003')

    tier_colors = {
        1: '#deebf7',
        2: '#084594'
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
        if row.get('health_adults', 0) == 1:
            symbols.append('Ha')  # Healthcare adults
        if row.get('health_children', 0) == 1:
            symbols.append('Hc')  # Healthcare children
        if row.get('health_adults', 0) == 1 or row.get('health_seniors', 0) == 1:
            symbols.append('Hs')  # Healthcare seniors (included in adults coverage or seniors-only)
        if row.get('food', 0) == 1:
            symbols.append('F')
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
                        ha='center', va='center', fontsize=10, fontweight='bold',
                        color=text_color)

    if not alaska.empty:
        row = alaska.iloc[0]
        tier = collapse_tier(row['id_strictness']) if pd.notna(row['id_strictness']) else 1
        text_color = get_text_color(tier)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-2050000, -1780000), ha='center', va='center',
                        fontsize=10, fontweight='bold', color=text_color)

    if not hawaii.empty:
        row = hawaii.iloc[0]
        tier = collapse_tier(row['id_strictness']) if pd.notna(row['id_strictness']) else 1
        text_color = get_text_color(tier)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-1050000, -1680000), ha='center', va='center',
                        fontsize=10, fontweight='bold', color=text_color)

    ax.set_title('Voter ID Strictness & Welfare Benefits for Illegal Immigrants',
                 fontsize=18, fontweight='bold', pad=20)

    legend_elements = [
        mpatches.Patch(facecolor=tier_colors[2], edgecolor='#666', label='No Effective ID Requirement'),
        mpatches.Patch(facecolor=tier_colors[1], edgecolor='#666', label='ID Verification Required'),
    ]
    legend1 = ax.legend(handles=legend_elements, loc='lower left', fontsize=10,
                        frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                        title='Voter ID Requirements', title_fontsize=11,
                        bbox_to_anchor=(0.10, 0.01))
    legend1.get_frame().set_facecolor('white')
    legend1.get_frame().set_edgecolor('#cccccc')
    ax.add_artist(legend1)

    from matplotlib.lines import Line2D
    welfare_elements = [
        Line2D([0], [0], marker='$Ha$', color='w', linestyle='', markersize=12,
               markerfacecolor='#333', markeredgecolor='#333', label='Ha = Health (Adults)'),
        Line2D([0], [0], marker='$Hc$', color='w', linestyle='', markersize=12,
               markerfacecolor='#333', markeredgecolor='#333', label='Hc = Health (Children)'),
        Line2D([0], [0], marker='$Hs$', color='w', linestyle='', markersize=12,
               markerfacecolor='#333', markeredgecolor='#333', label='Hs = Health (Seniors 65+)'),
        Line2D([0], [0], marker='$F$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='F = Food Assistance'),
        Line2D([0], [0], marker='$E$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='E = EITC (ITIN filers)'),
    ]
    legend2 = ax.legend(handles=welfare_elements, loc='lower left', fontsize=10,
                        frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                        title='Benefits for Illegal Immigrants', title_fontsize=11,
                        bbox_to_anchor=(0.27, 0.01), handletextpad=0.5)
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
    - Tier 1-2: Strict ID (must present ID)
    - Tier 3-4: Non-Strict ID (ID requested, alternatives allowed)
    - Tier 5: No Document Required
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
    states_gdf['welfare_score_adults'] = states_gdf['welfare_score_adults'].fillna(0)
    for col in ['health_children', 'health_adults', 'health_seniors', 'food', 'eitc']:
        states_gdf[col] = states_gdf[col].fillna(0)

    def collapse_tier_3(tier):
        tier = int(tier)
        if tier <= 2:
            return 1  # Strict ID
        elif tier <= 4:
            return 2  # Non-Strict ID
        else:
            return 3  # No Document Required

    states_gdf['tier_3'] = states_gdf['id_strictness'].apply(collapse_tier_3)
    states_gdf = states_gdf.to_crs('ESRI:102003')

    tier_colors = {
        1: '#deebf7',  # Light blue - Strict ID
        2: '#6baed6',  # Medium blue - Non-Strict ID
        3: '#084594'   # Dark blue - No Document
    }

    continental = states_gdf[~states_gdf['STUSPS'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'AS', 'MP'])]
    alaska = states_gdf[states_gdf['STUSPS'] == 'AK'].copy()
    hawaii = states_gdf[states_gdf['STUSPS'] == 'HI'].copy()

    fig, ax = plt.subplots(figsize=(16, 10))

    def get_color(tier):
        return tier_colors.get(int(tier), '#deebf7')

    def get_text_color(tier):
        return 'white' if tier == 3 else '#333333'

    def get_welfare_symbols(row):
        symbols = []
        if row.get('health_adults', 0) == 1:
            symbols.append('Ha')
        if row.get('health_children', 0) == 1:
            symbols.append('Hc')
        if row.get('health_adults', 0) == 1 or row.get('health_seniors', 0) == 1:
            symbols.append('Hs')
        if row.get('food', 0) == 1:
            symbols.append('F')
        if row.get('eitc', 0) == 1:
            symbols.append('E')
        return ' '.join(symbols) if symbols else ''

    for idx, row in continental.iterrows():
        tier = row['tier_3']
        color = get_color(tier)
        continental[continental.index == idx].plot(
            ax=ax, color=color, edgecolor='white', linewidth=0.8
        )

    if not alaska.empty:
        alaska_scaled = alaska.copy()
        alaska_scaled.geometry = alaska_scaled.geometry.scale(0.35, 0.35, origin=(0, 0))
        alaska_scaled.geometry = alaska_scaled.geometry.translate(-1800000, -1400000)
        tier = collapse_tier_3(alaska['id_strictness'].values[0]) if pd.notna(alaska['id_strictness'].values[0]) else 1
        alaska_scaled.plot(ax=ax, color=get_color(tier), edgecolor='white', linewidth=0.8)

    if not hawaii.empty:
        hawaii_scaled = hawaii.copy()
        hawaii_scaled.geometry = hawaii_scaled.geometry.scale(1.0, 1.0, origin=(0, 0))
        hawaii_scaled.geometry = hawaii_scaled.geometry.translate(5200000, -1200000)
        tier = collapse_tier_3(hawaii['id_strictness'].values[0]) if pd.notna(hawaii['id_strictness'].values[0]) else 1
        hawaii_scaled.plot(ax=ax, color=get_color(tier), edgecolor='white', linewidth=0.8)

    for idx, row in continental.iterrows():
        centroid = row.geometry.centroid
        tier = row['tier_3']
        text_color = get_text_color(tier)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(centroid.x, centroid.y),
                        ha='center', va='center', fontsize=10, fontweight='bold',
                        color=text_color)

    if not alaska.empty:
        row = alaska.iloc[0]
        tier = collapse_tier_3(row['id_strictness']) if pd.notna(row['id_strictness']) else 1
        text_color = get_text_color(tier)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-2050000, -1780000), ha='center', va='center',
                        fontsize=10, fontweight='bold', color=text_color)

    if not hawaii.empty:
        row = hawaii.iloc[0]
        tier = collapse_tier_3(row['id_strictness']) if pd.notna(row['id_strictness']) else 1
        text_color = get_text_color(tier)
        welfare_symbols = get_welfare_symbols(row)
        if welfare_symbols:
            ax.annotate(welfare_symbols, xy=(-1050000, -1680000), ha='center', va='center',
                        fontsize=10, fontweight='bold', color=text_color)

    ax.set_title('Voter ID Strictness & Welfare Benefits for Illegal Immigrants',
                 fontsize=18, fontweight='bold', pad=20)

    legend_elements = [
        mpatches.Patch(facecolor=tier_colors[3], edgecolor='#666', label='No Document Required (Tier 5)'),
        mpatches.Patch(facecolor=tier_colors[2], edgecolor='#666', label='Non-Strict ID (Tiers 3-4)'),
        mpatches.Patch(facecolor=tier_colors[1], edgecolor='#666', label='Strict ID (Tiers 1-2)'),
    ]
    legend1 = ax.legend(handles=legend_elements, loc='lower left', fontsize=10,
                        frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                        title='Voter ID Requirements', title_fontsize=11,
                        bbox_to_anchor=(0.10, 0.01))
    legend1.get_frame().set_facecolor('white')
    legend1.get_frame().set_edgecolor('#cccccc')
    ax.add_artist(legend1)

    from matplotlib.lines import Line2D
    welfare_elements = [
        Line2D([0], [0], marker='$Ha$', color='w', linestyle='', markersize=12,
               markerfacecolor='#333', markeredgecolor='#333', label='Ha = Health (Adults)'),
        Line2D([0], [0], marker='$Hc$', color='w', linestyle='', markersize=12,
               markerfacecolor='#333', markeredgecolor='#333', label='Hc = Health (Children)'),
        Line2D([0], [0], marker='$Hs$', color='w', linestyle='', markersize=12,
               markerfacecolor='#333', markeredgecolor='#333', label='Hs = Health (Seniors 65+)'),
        Line2D([0], [0], marker='$F$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='F = Food Assistance'),
        Line2D([0], [0], marker='$E$', color='w', linestyle='', markersize=10,
               markerfacecolor='#333', markeredgecolor='#333', label='E = EITC (ITIN filers)'),
    ]
    legend2 = ax.legend(handles=welfare_elements, loc='lower left', fontsize=10,
                        frameon=True, fancybox=True, shadow=True, framealpha=0.95,
                        title='Benefits for Illegal Immigrants', title_fontsize=11,
                        bbox_to_anchor=(0.27, 0.01), handletextpad=0.5)
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

    print("Creating static state map (5-tier)...")
    create_static_map(df, output_dir / "state_map.png")

    print("Creating static state map (2-tier)...")
    create_static_map_2tier(df, output_dir / "state_map_2tier.png")

    print("Creating static state map (3-tier)...")
    create_static_map_3tier(df, output_dir / "state_map_3tier.png")

    print(f"All visualizations saved to {output_dir}")


if __name__ == "__main__":
    from prepare_data import load_and_prepare

    df = load_and_prepare()
    output_dir = Path(__file__).parent.parent / "output"
    create_all_visualizations(df, output_dir)
