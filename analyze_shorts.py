#!/usr/bin/env python3
"""Analyze collected YouTube Shorts using Σ₀ framework."""

import json
import statistics

# Load collected shorts
with open('data/youtube/raw_shorts_dataset.jsonl') as f:
    shorts = [json.loads(line) for line in f if line.strip()]

print(f'[COLLECTED] {len(shorts)} YouTube Shorts')
print()

# Load gaming subset
with open('data/youtube/gaming_shorts.jsonl') as f:
    gaming = [json.loads(line) for line in f if line.strip()]

print(f'[GAMING SUBSET] {len(gaming)} shorts ({100*len(gaming)/len(shorts):.1f}%)')
print()

# Load extracted features
with open('data/youtube/features_v10.jsonl') as f:
    features = [json.loads(line) for line in f if line.strip()]

print(f'[FEATURES EXTRACTED] {len(features)} feature vectors')
print()

# Analyze engagement
views = [f['engagement']['views'] for f in features]
likes = [f['engagement']['likes'] for f in features]
engagement_rates = [f['engagement']['engagement_rate'] for f in features]

print('[ENGAGEMENT METRICS]')
print(f'  Views: min={int(min(views)):,} | max={int(max(views)):,} | median={int(statistics.median(views)):,}')
print(f'  Likes: min={int(min(likes)):,} | max={int(max(likes)):,} | median={int(statistics.median(likes)):,}')
print(f'  Engagement Rate: min={min(engagement_rates):.3%} | max={max(engagement_rates):.3%} | median={statistics.median(engagement_rates):.3%}')
print()

# Analyze Σ₀ features
entropies = [f['sigma0']['entropy_proxy'] for f in features]
motions = [f['sigma0']['motion_proxy'] for f in features]
hooks = [f['sigma0']['hook_strength'] for f in features]
retention_proxies = [f['sigma0']['retention_proxy'] for f in features]
velocity_scores = [f['sigma0']['velocity_score'] for f in features]
surprise_gaps = [f['sigma0']['surprise_gap'] for f in features]

# Calculate collapse risk (same formula as feature extractor)
def calc_collapse_risk(sigma0):
    entropy = sigma0['entropy_proxy']
    retention = sigma0['retention_proxy']
    velocity = sigma0['velocity_score']
    return max(0, (1-entropy)*0.35 + (1-retention)*0.35 + (1-velocity)*0.30)

collapse_risks = [calc_collapse_risk(f['sigma0']) for f in features]

print('[SIGMA0 STABILITY METRICS]')
print(f'  Entropy (diversity): min={min(entropies):.3f} | avg={statistics.mean(entropies):.3f} | max={max(entropies):.3f}')
print(f'  Motion (action): min={min(motions):.3f} | avg={statistics.mean(motions):.3f} | max={max(motions):.3f}')
print(f'  Hook Strength (opening): min={min(hooks):.3f} | avg={statistics.mean(hooks):.3f} | max={max(hooks):.3f}')
print(f'  Collapse Risk (degenerate): min={min(collapse_risks):.3f} | avg={statistics.mean(collapse_risks):.3f} | max={max(collapse_risks):.3f}')
print()

# Correlation analysis
print('[SIGMA0 TO ENGAGEMENT CORRELATION]')

# High-engagement shorts (top 25%)
high_eng_threshold = statistics.quantiles(views, n=4)[2]  # 75th percentile
high_eng = [f for f in features if f['engagement']['views'] >= high_eng_threshold]
low_eng = [f for f in features if f['engagement']['views'] < high_eng_threshold]

avg_entropy_high = statistics.mean([f['sigma0']['entropy_proxy'] for f in high_eng])
avg_entropy_low = statistics.mean([f['sigma0']['entropy_proxy'] for f in low_eng])

avg_motion_high = statistics.mean([f['sigma0']['motion_proxy'] for f in high_eng])
avg_motion_low = statistics.mean([f['sigma0']['motion_proxy'] for f in low_eng])

avg_collapse_high = statistics.mean([calc_collapse_risk(f['sigma0']) for f in high_eng])
avg_collapse_low = statistics.mean([calc_collapse_risk(f['sigma0']) for f in low_eng])

print(f'  High-engagement shorts (n={len(high_eng)}):')
print(f'    Entropy: {avg_entropy_high:.3f} | Motion: {avg_motion_high:.3f} | Collapse Risk: {avg_collapse_high:.3f}')
print(f'  Low-engagement shorts (n={len(low_eng)}):')
print(f'    Entropy: {avg_entropy_low:.3f} | Motion: {avg_motion_low:.3f} | Collapse Risk: {avg_collapse_low:.3f}')
print()

# Key insight: what makes shorts viral?
print('[SIGMA0 INSIGHTS - Collapse Theory Application]')
if avg_entropy_high > avg_entropy_low:
    print(f'  [YES] HIGH-PERFORMING Shorts have higher ENTROPY ({avg_entropy_high:.3f} vs {avg_entropy_low:.3f})')
    print('    Validates: Content diversity prevents collapse onto degenerate attractor')
else:
    print(f'  [NO] Entropy NOT a strong differentiator')

if avg_motion_high > avg_motion_low:
    print(f'  [YES] HIGH-PERFORMING Shorts have more MOTION ({avg_motion_high:.3f} vs {avg_motion_low:.3f})')
    print('    Validates: Action/energy prevents static collapse')
else:
    print(f'  [NO] Motion NOT a strong differentiator')

if avg_collapse_high < avg_collapse_low:
    print(f'  [YES] HIGH-PERFORMING Shorts have LOW COLLAPSE RISK ({avg_collapse_high:.3f} vs {avg_collapse_low:.3f})')
    print('    Validates: Stability filter works - low-risk shorts perform better')
else:
    print(f'  [NO] Collapse risk NOT inversely correlated')

print()
print('[TOP 5 MOST ENGAGED SHORTS]')
top5 = sorted(features, key=lambda f: f['engagement']['views'], reverse=True)[:5]
for i, f in enumerate(top5, 1):
    title = f['title'][:60]
    cr = calc_collapse_risk(f['sigma0'])
    print(f'  {i}. {title}')
    print(f'     Views: {int(f["engagement"]["views"]):,} | Engagement: {f["engagement"]["engagement_rate"]:.2%}')
    print(f'     Collapse Risk: {cr:.3f} (stable=0.3, degenerate=0.7)')
    print()
