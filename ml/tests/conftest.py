import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def daily():
    dates = pd.date_range('2010-01-01', periods=430)
    return pd.concat([pd.DataFrame({'sku': sku, 'date': dates,
                         'demand': (np.arange(430) % 7 + offset).astype(float),
                         'price': 2.0 + np.arange(430) / 1000})
                      for sku, offset in [('10001', 0), ('10002', 3)]], ignore_index=True)
