"""Create congruent 5-tier table and standalone 2-tier stats."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
from scipy import stats
from prepare_data import load_and_prepare

df = load_and_prepare()
df['has_any_health'] = ((df['health_children'] == 1) | (df['health_adults'] == 1) | (df['health_seniors'] == 1)).astype(int)
df['has_any_benefit'] = ((df['has_any_health'] == 1) | (df['food'] == 1) | (df['eitc'] == 1)).astype(int)

output_dir = Path(__file__).parent.parent / 'output'

tier_labels = {
    1: 'Strict Photo ID',
    2: 'Strict Non-Photo',
    3: 'Non-Strict Photo',
    4: 'Non-Strict Non-Photo',
    5: 'No Document Req'
}

colors = ['#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#084594']
text_colors = ['#333', '#333', '#333', '#333', 'white']

# ============================================================================
# TABLE 1: Full 5-tier breakdown with correlation stats (congruent)
# ============================================================================
fig, ax = plt.subplots(figsize=(14, 7.5))
ax.axis('off')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# Title
ax.text(0.5, 0.97, 'Welfare Benefits for Illegal Immigrants: Full Breakdown', fontsize=20, fontweight='bold',
        ha='center', transform=ax.transAxes)
ax.text(0.5, 0.93, 'Percentage of states offering each benefit, by voter ID strictness tier', fontsize=12,
        ha='center', transform=ax.transAxes, color='#555')

# Headers
x_pos = [0.03, 0.10, 0.30, 0.40, 0.52, 0.64, 0.74, 0.84, 0.94]

ax.text(x_pos[0], 0.89, 'Tier', fontsize=10, fontweight='bold', ha='left', transform=ax.transAxes)
ax.text(x_pos[1], 0.89, 'Voter ID Policy', fontsize=10, fontweight='bold', ha='left', transform=ax.transAxes)
ax.text(x_pos[2], 0.89, 'N', fontsize=10, fontweight='bold', ha='center', transform=ax.transAxes)
ax.text(x_pos[3], 0.895, 'Health', fontsize=10, fontweight='bold', ha='center', transform=ax.transAxes)
ax.text(x_pos[3], 0.87, '(Adults)', fontsize=9, ha='center', transform=ax.transAxes, color='#555')
ax.text(x_pos[4], 0.895, 'Health', fontsize=10, fontweight='bold', ha='center', transform=ax.transAxes)
ax.text(x_pos[4], 0.87, '(Children)', fontsize=9, ha='center', transform=ax.transAxes, color='#555')
ax.text(x_pos[5], 0.895, 'Health', fontsize=10, fontweight='bold', ha='center', transform=ax.transAxes)
ax.text(x_pos[5], 0.87, '(Seniors)', fontsize=9, ha='center', transform=ax.transAxes, color='#555')
ax.text(x_pos[6], 0.89, 'Food', fontsize=10, fontweight='bold', ha='center', transform=ax.transAxes)
ax.text(x_pos[7], 0.89, 'EITC', fontsize=10, fontweight='bold', ha='center', transform=ax.transAxes)
ax.text(x_pos[8], 0.89, 'ANY', fontsize=10, fontweight='bold', ha='center', transform=ax.transAxes)

ax.plot([0.02, 0.98], [0.855, 0.855], color='#333', linewidth=1.5, transform=ax.transAxes, clip_on=False)

# Data rows
y_start = 0.81
y_step = 0.095

for i, tier in enumerate([1, 2, 3, 4, 5]):
    y = y_start - i * y_step
    group = df[df['id_strictness'] == tier]
    n = len(group)

    rect = Rectangle((0.02, y-0.038), 0.96, 0.085, transform=ax.transAxes,
                     facecolor=colors[i], edgecolor='#ccc', linewidth=0.5, zorder=0)
    ax.add_patch(rect)

    tc = text_colors[i]
    ax.text(x_pos[0], y, str(tier), fontsize=11, ha='left', transform=ax.transAxes, color=tc)
    ax.text(x_pos[1], y, tier_labels[tier], fontsize=10, ha='left', transform=ax.transAxes, color=tc)
    ax.text(x_pos[2], y, str(n), fontsize=11, ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_pos[3], y, f"{group['health_adults'].mean()*100:.0f}%", fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_pos[4], y, f"{group['health_children'].mean()*100:.0f}%", fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_pos[5], y, f"{group['health_seniors'].mean()*100:.0f}%", fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_pos[6], y, f"{group['food'].mean()*100:.0f}%", fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_pos[7], y, f"{group['eitc'].mean()*100:.0f}%", fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_pos[8], y, f"{group['has_any_benefit'].mean()*100:.0f}%", fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)

# Bottom section: p-trend from logistic regression
ax.plot([0.02, 0.98], [0.31, 0.31], color='#333', linewidth=1, transform=ax.transAxes, clip_on=False)

ax.text(0.5, 0.26, 'Test for Trend Across Tiers (Logistic Regression)',
        fontsize=13, fontweight='bold', ha='center', transform=ax.transAxes)

import statsmodels.api as sm

benefit_cols = [('Health (Adults)', 'health_adults'), ('Health (Children)', 'health_children'),
                ('Health (Seniors)', 'health_seniors'), ('Food', 'food'), ('EITC', 'eitc'),
                ('ANY Benefit', 'has_any_benefit')]

y_trend = 0.20
for label, col in benefit_cols:
    X = sm.add_constant(df['id_strictness'])
    y = df[col]

    try:
        model = sm.Logit(y, X)
        result = model.fit(disp=0)
        p_trend = result.pvalues['id_strictness']
    except:
        p_trend = 1.0

    sig = '***' if p_trend < 0.001 else '**' if p_trend < 0.01 else '*' if p_trend < 0.05 else ''

    if p_trend < 0.0001:
        p_str = '<0.0001'
    else:
        p_str = f'{p_trend:.4f}'

    ax.text(0.25, y_trend, label, fontsize=10, ha='left', transform=ax.transAxes)
    ax.text(0.58, y_trend, f'p(trend) = {p_str}', fontsize=10, fontweight='bold', ha='center', transform=ax.transAxes, color='#084594')
    ax.text(0.78, y_trend, sig, fontsize=11, fontweight='bold', ha='left', transform=ax.transAxes, color='#c00')
    y_trend -= 0.028

ax.text(0.5, 0.02, 'Logistic regression with tier (1-5) as continuous predictor. * p<0.05, ** p<0.01, *** p<0.001',
        fontsize=9, ha='center', transform=ax.transAxes, color='#666', style='italic')

plt.tight_layout()
fig.savefig(output_dir / 'table_granular_pvalues.png', dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.05)
plt.close()
print('Created: table_granular_pvalues.png')

# ============================================================================
# TABLE 2: Standalone 2-tier comparison (No ID vs ID Required)
# ============================================================================
no_id = df[df['no_effective_id'] == 1]
id_req = df[df['no_effective_id'] == 0]

fig, ax = plt.subplots(figsize=(10, 7))
ax.axis('off')
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

ax.text(0.5, 0.95, 'Statistical Comparison: No ID vs ID Required', fontsize=18, fontweight='bold',
        ha='center', transform=ax.transAxes)
ax.text(0.5, 0.90, 'Fisher exact test for each benefit category', fontsize=12,
        ha='center', transform=ax.transAxes, color='#555')

# Headers
ax.text(0.08, 0.82, 'Benefit', fontsize=12, fontweight='bold', ha='left', transform=ax.transAxes)
ax.text(0.38, 0.82, 'No ID', fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes, color='#084594')
ax.text(0.58, 0.82, 'ID Req', fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes, color='#666')
ax.text(0.74, 0.82, 'p-value', fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes)
ax.text(0.88, 0.82, 'Sig', fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes)

ax.text(0.38, 0.78, '(24 states)', fontsize=9, ha='center', transform=ax.transAxes, color='#666')
ax.text(0.58, 0.78, '(27 states)', fontsize=9, ha='center', transform=ax.transAxes, color='#666')

ax.plot([0.05, 0.95], [0.75, 0.75], color='#333', linewidth=1.5, transform=ax.transAxes, clip_on=False)

test_data = [
    ('Health (Adults)', 'health_adults'),
    ('Health (Children)', 'health_children'),
    ('Health (Seniors)', 'health_seniors'),
    ('Food Assistance', 'food'),
    ('EITC', 'eitc'),
    ('ANY Benefit', 'has_any_benefit'),
]

y_row = 0.68
for i, (label, col) in enumerate(test_data):
    no_id_pct = no_id[col].mean() * 100
    id_pct = id_req[col].mean() * 100

    a = no_id[col].sum()
    b = len(no_id) - a
    c = id_req[col].sum()
    d = len(id_req) - c
    _, p = stats.fisher_exact([[a, b], [c, d]])

    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''

    # Highlight ANY row
    if i == 5:
        rect = Rectangle((0.05, y_row-0.025), 0.90, 0.07, transform=ax.transAxes,
                         facecolor='#f0f0f0', edgecolor='none', zorder=0)
        ax.add_patch(rect)
        weight = 'bold'
    else:
        weight = 'normal'

    ax.text(0.08, y_row, label, fontsize=12, fontweight=weight, ha='left', transform=ax.transAxes)
    ax.text(0.38, y_row, f'{no_id_pct:.0f}%', fontsize=14, fontweight='bold', ha='center', transform=ax.transAxes, color='#084594')
    ax.text(0.48, y_row, 'vs', fontsize=10, ha='center', transform=ax.transAxes, color='#999')
    ax.text(0.58, y_row, f'{id_pct:.0f}%', fontsize=14, fontweight='bold', ha='center', transform=ax.transAxes, color='#666')
    ax.text(0.74, y_row, f'{p:.4f}', fontsize=11, ha='center', transform=ax.transAxes)
    ax.text(0.88, y_row, sig, fontsize=14, fontweight='bold', ha='center', transform=ax.transAxes, color='#c00')

    y_row -= 0.09

ax.text(0.5, 0.12, 'Significance: * p<0.05, ** p<0.01, *** p<0.001',
        fontsize=10, ha='center', transform=ax.transAxes, color='#666', style='italic')

plt.tight_layout()
fig.savefig(output_dir / 'table_2tier_stats.png', dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.05)
plt.close()
print('Created: table_2tier_stats.png')
