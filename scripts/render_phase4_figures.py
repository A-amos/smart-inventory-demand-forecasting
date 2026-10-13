"""Polish axes on preserved actual final forecasts; never fit/tune models."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.common import RESEARCH, read_json
from ml.eda import finish, plt
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter

predictions = pd.read_csv(RESEARCH / 'results/final-test-predictions.csv', dtype={'sku': 'string'}, parse_dates=['date'])
eda = read_json(RESEARCH / 'eda/summary.json')
frozen = read_json(RESEARCH / 'results/frozen-selection.json')
fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
for ax, sku in zip(axes, eda['representative_skus'], strict=True):
    rows = predictions[predictions.sku.eq(sku)]
    truth = rows[rows.model.eq(frozen['selected'])].sort_values('date')
    ax.plot(truth.date, truth.actual, color='#233449', label='Actual', linewidth=1.6)
    for name in frozen['finalists']:
        forecast = rows[rows.model.eq(name)].sort_values('date')
        ax.plot(forecast.date, forecast.prediction, label=name, linewidth=.9, alpha=.85)
    ax.set(title=f'SKU {sku} (representative chosen from training)', ylabel='Units/day')
axes[0].legend(ncol=3, fontsize=8)
locator = AutoDateLocator(minticks=4, maxticks=6)
axes[-1].xaxis.set_major_locator(locator)
axes[-1].xaxis.set_major_formatter(ConciseDateFormatter(locator))
axes[-1].set_xlabel('Final test date')
finish(fig, RESEARCH / 'results/representative-final-forecasts.png')
print('Actual representative forecast figure rendered with non-overlapping date labels')
