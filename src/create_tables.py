"""Create Twitter-friendly table images."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
from prepare_data import load_and_prepare

df = load_and_prepare()
df['has_any_health'] = ((df['health_children'] == 1) | (df['health_adults'] == 1) | (df['health_seniors'] == 1)).astype(int)
df['has_any_benefit'] = ((df['has_any_health'] == 1) | (df['food'] == 1) | (df['eitc'] == 1)).astype(int)

output_dir = Path(__file__).parent.parent / 'output'

no_id = df[df['no_effective_id'] == 1]
id_req = df[df['no_effective_id'] == 0]

tier_labels = {
    1: 'Strict Photo ID',
    2: 'Strict Non-Photo ID',
    3: 'Non-Strict Photo ID',
    4: 'Non-Strict Non-Photo ID',
    5: 'No Document Required'
}

colors = ['#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#084594']
text_colors = ['#333', '#333', '#333', '#333', 'white']

# ============================================================================
# TABLE 1: Simple 2-tier comparison (MAIN TWEET)
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))
ax.axis('off')

data = [
    ('Healthcare', f"{no_id['has_any_health'].mean()*100:.0f}%", f"{id_req['has_any_health'].mean()*100:.0f}%"),
    ('Food Assistance', f"{no_id['food'].mean()*100:.0f}%", f"{id_req['food'].mean()*100:.0f}%"),
    ('EITC (tax credits)', f"{no_id['eitc'].mean()*100:.0f}%", f"{id_req['eitc'].mean()*100:.0f}%"),
    ('ANY BENEFIT', f"{no_id['has_any_benefit'].mean()*100:.0f}%", f"{id_req['has_any_benefit'].mean()*100:.0f}%"),
]

# Title
ax.text(0.5, 0.95, 'State Welfare Benefits for Illegal Immigrants', fontsize=18, fontweight='bold',
        ha='center', transform=ax.transAxes)
ax.text(0.5, 0.88, 'by Voter ID Requirement', fontsize=14, ha='center', transform=ax.transAxes, color='#555')

# Column headers
ax.text(0.35, 0.78, 'No Effective ID', fontsize=13, fontweight='bold', ha='center', transform=ax.transAxes, color='#084594')
ax.text(0.35, 0.73, '(24 states)', fontsize=11, ha='center', transform=ax.transAxes, color='#666')
ax.text(0.65, 0.78, 'ID Required', fontsize=13, fontweight='bold', ha='center', transform=ax.transAxes, color='#888')
ax.text(0.65, 0.73, '(27 states)', fontsize=11, ha='center', transform=ax.transAxes, color='#666')

# Data rows
y_positions = [0.60, 0.48, 0.36, 0.22]
for i, (label, no_id_val, id_val) in enumerate(data):
    y = y_positions[i]
    weight = 'bold' if i == 3 else 'normal'
    size = 13 if i == 3 else 12

    # Row background for ANY BENEFIT
    if i == 3:
        rect = Rectangle((0.08, y-0.04), 0.84, 0.10, transform=ax.transAxes,
                         facecolor='#f0f0f0', edgecolor='none', zorder=0)
        ax.add_patch(rect)

    ax.text(0.12, y, label, fontsize=size, fontweight=weight, ha='left', transform=ax.transAxes)
    ax.text(0.35, y, no_id_val, fontsize=size+2, fontweight='bold', ha='center', transform=ax.transAxes, color='#084594')
    ax.text(0.65, y, id_val, fontsize=size+2, fontweight='bold', ha='center', transform=ax.transAxes, color='#888')

# Footer
ax.text(0.5, 0.08, 'All differences statistically significant (p < 0.02, Fisher\'s exact test)',
        fontsize=10, ha='center', transform=ax.transAxes, color='#666', style='italic')
ax.text(0.5, 0.02, 'Sources: NCSL (Voter ID), KFF/NILC (Health), ITEP (EITC) - 2024',
        fontsize=9, ha='center', transform=ax.transAxes, color='#999')

plt.tight_layout()
fig.savefig(output_dir / 'table_2tier_simple.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print('Created: table_2tier_simple.png')

# ============================================================================
# TABLE 2: 5-tier gradient (FOLLOW-UP)
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 7))
ax.axis('off')

# Title
ax.text(0.5, 0.95, 'Welfare Benefits for Illegal Immigrants by Voter ID Tier', fontsize=16, fontweight='bold',
        ha='center', transform=ax.transAxes)

# Column headers
headers = ['Tier', 'Voter ID Policy', 'N', 'Health', 'Food', 'EITC', 'ANY']
x_positions = [0.05, 0.18, 0.42, 0.52, 0.62, 0.72, 0.85]
for x, header in zip(x_positions, headers):
    ax.text(x, 0.85, header, fontsize=11, fontweight='bold', ha='left' if x < 0.4 else 'center',
            transform=ax.transAxes)

# Horizontal line
ax.plot([0.03, 0.97], [0.82, 0.82], color='#333', linewidth=1.5, transform=ax.transAxes, clip_on=False)

# Data rows
y_start = 0.74
y_step = 0.11

for i, tier in enumerate([1, 2, 3, 4, 5]):
    y = y_start - i * y_step
    group = df[df['id_strictness'] == tier]
    n = len(group)

    # Background color
    rect = Rectangle((0.03, y-0.04), 0.94, 0.10, transform=ax.transAxes,
                     facecolor=colors[i], edgecolor='#ccc', linewidth=0.5, zorder=0)
    ax.add_patch(rect)

    tc = text_colors[i]
    ax.text(x_positions[0], y, str(tier), fontsize=11, ha='left', transform=ax.transAxes, color=tc)
    ax.text(x_positions[1], y, tier_labels[tier], fontsize=10, ha='left', transform=ax.transAxes, color=tc)
    ax.text(x_positions[2], y, str(n), fontsize=11, ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_positions[3], y, f"{group['has_any_health'].mean()*100:.0f}%", fontsize=11, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_positions[4], y, f"{group['food'].mean()*100:.0f}%", fontsize=11, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_positions[5], y, f"{group['eitc'].mean()*100:.0f}%", fontsize=11, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_positions[6], y, f"{group['has_any_benefit'].mean()*100:.0f}%", fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)

# Footer
ax.text(0.5, 0.12, 'Clear gradient: As voter ID requirements weaken, benefits increase from 0% to 80%',
        fontsize=11, ha='center', transform=ax.transAxes, color='#333', fontweight='bold')
ax.text(0.5, 0.05, 'Spearman correlation: ρ = 0.57, p < 0.0001',
        fontsize=10, ha='center', transform=ax.transAxes, color='#666', style='italic')

plt.tight_layout()
fig.savefig(output_dir / 'table_5tier_gradient.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print('Created: table_5tier_gradient.png')

# ============================================================================
# TABLE 3: Healthcare breakdown (FOLLOW-UP for granularity)
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 7))
ax.axis('off')

# Title
ax.text(0.5, 0.95, 'Healthcare Benefits for Illegal Immigrants: Detailed Breakdown', fontsize=16, fontweight='bold',
        ha='center', transform=ax.transAxes)

# Column headers
headers = ['Tier', 'Voter ID Policy', 'N', 'Adults', 'Children', 'Seniors', 'Any Health']
x_positions = [0.05, 0.18, 0.42, 0.52, 0.64, 0.76, 0.88]
for x, header in zip(x_positions, headers):
    ax.text(x, 0.85, header, fontsize=10, fontweight='bold', ha='left' if x < 0.4 else 'center',
            transform=ax.transAxes)

ax.plot([0.03, 0.97], [0.82, 0.82], color='#333', linewidth=1.5, transform=ax.transAxes, clip_on=False)

y_start = 0.74
y_step = 0.11

for i, tier in enumerate([1, 2, 3, 4, 5]):
    y = y_start - i * y_step
    group = df[df['id_strictness'] == tier]
    n = len(group)

    rect = Rectangle((0.03, y-0.04), 0.94, 0.10, transform=ax.transAxes,
                     facecolor=colors[i], edgecolor='#ccc', linewidth=0.5, zorder=0)
    ax.add_patch(rect)

    tc = text_colors[i]
    ax.text(x_positions[0], y, str(tier), fontsize=11, ha='left', transform=ax.transAxes, color=tc)
    ax.text(x_positions[1], y, tier_labels[tier], fontsize=10, ha='left', transform=ax.transAxes, color=tc)
    ax.text(x_positions[2], y, str(n), fontsize=11, ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_positions[3], y, f"{group['health_adults'].mean()*100:.0f}%", fontsize=11, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_positions[4], y, f"{group['health_children'].mean()*100:.0f}%", fontsize=11, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_positions[5], y, f"{group['health_seniors'].mean()*100:.0f}%", fontsize=11, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)
    ax.text(x_positions[6], y, f"{group['has_any_health'].mean()*100:.0f}%", fontsize=12, fontweight='bold', ha='center', transform=ax.transAxes, color=tc)

# Footer with stats
ax.text(0.5, 0.12, 'No state with strict voter ID (Tiers 1-2) offers ANY healthcare to illegal immigrants',
        fontsize=11, ha='center', transform=ax.transAxes, color='#333', fontweight='bold')
ax.text(0.5, 0.05, "Adults: p=0.008**, Children: p<0.001***, Seniors: p=0.22 (Fisher's exact)",
        fontsize=10, ha='center', transform=ax.transAxes, color='#666', style='italic')

plt.tight_layout()
fig.savefig(output_dir / 'table_healthcare_breakdown.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print('Created: table_healthcare_breakdown.png')

# ============================================================================
# TABLE 4: Stark divide - big numbers (MAIN TWEET alternative)
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 5))
ax.axis('off')

# Title
ax.text(0.5, 0.92, 'The Stark Divide', fontsize=20, fontweight='bold',
        ha='center', transform=ax.transAxes)
ax.text(0.5, 0.82, 'Percentage of states offering ANY welfare benefit to illegal immigrants',
        fontsize=12, ha='center', transform=ax.transAxes, color='#555')

# Big numbers
ax.text(0.25, 0.50, f"{no_id['has_any_benefit'].mean()*100:.0f}%", fontsize=72, fontweight='bold',
        ha='center', transform=ax.transAxes, color='#084594')
ax.text(0.75, 0.50, f"{id_req['has_any_benefit'].mean()*100:.0f}%", fontsize=72, fontweight='bold',
        ha='center', transform=ax.transAxes, color='#888')

ax.text(0.25, 0.28, 'No Effective\nVoter ID', fontsize=14, ha='center', transform=ax.transAxes, color='#084594')
ax.text(0.25, 0.18, '(24 states)', fontsize=11, ha='center', transform=ax.transAxes, color='#666')
ax.text(0.75, 0.28, 'Voter ID\nRequired', fontsize=14, ha='center', transform=ax.transAxes, color='#888')
ax.text(0.75, 0.18, '(27 states)', fontsize=11, ha='center', transform=ax.transAxes, color='#666')

ax.text(0.5, 0.50, 'vs', fontsize=24, ha='center', va='center', transform=ax.transAxes, color='#999')

ax.text(0.5, 0.05, "p < 0.0001 (Fisher's exact test)", fontsize=10, ha='center', transform=ax.transAxes, color='#666', style='italic')

plt.tight_layout()
fig.savefig(output_dir / 'table_stark_divide.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print('Created: table_stark_divide.png')

print('\nAll table images saved to output/')
