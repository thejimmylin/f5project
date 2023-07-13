"""Finlab Strategies

More strategies can be found at https://ai.finlab.tw/strategies/?tab=FinLab台股
"""

__all__ = ["peg_strategy"]


def peg_strategy():
    from finlab import data
    from finlab.backtest import sim

    pe = data.get("price_earning_ratio:本益比")
    rev = data.get("monthly_revenue:當月營收")
    rev_ma3 = rev.average(3)
    rev_ma12 = rev.average(12)
    營業利益成長率 = data.get("fundamental_features:營業利益成長率")
    peg = pe / 營業利益成長率
    cond1 = rev_ma3 / rev_ma12 > 1.1
    cond2 = rev / rev.shift() > 0.9

    cond_all = cond1 & cond2
    result = peg * cond_all
    position = result[result > 0].is_smallest(10).reindex(rev.index_str_to_date().index, method="ffill")

    report = sim(
        position=position,
        fee_ratio=1.425 / 1000 / 3,
        stop_loss=0.1,
        upload=False,
        name="本益成長比",
        live_performance_start="2021-06-01",
    )
    return report
