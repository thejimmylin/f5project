"""Main entrypoint of the project.

- This file is the entrypoint of Google Cloud Function.
- It also provides a CLI to run the function locally.
"""
from pathlib import Path
from typing import cast

from finlab.online.order_executor import OrderExecutor, Position

import my_strategies
from f5project import F5Project, F5ProjectConfig

BASE_DIR = Path(__file__).resolve().parent


# Let `F5Project` handle all the boring stuff.
project = F5Project(config=F5ProjectConfig.from_json_or_env(BASE_DIR / ".secrets" / "index.json"))


# Decorate our `create_orders` function to make it a Google Cloud Function.
@project.gcf_endpoint
def create_orders(view_only: bool = True, fund: int = 10000, odd_lot: bool = True) -> list[dict]:
    # Set up project first
    project.setup()
    # Get backtest report with one of our strategies
    report = my_strategies.peg_strategy()
    # Use it to create stock position we should hold now
    position = Position.from_report(report, fund, odd_lot=odd_lot)
    # Get records with `view_only=True` to return it later
    # get Fugle account from `F5Project`. Make sure you call `project.login()` first.
    fugle_account = project.fugle_account()
    order_executor = OrderExecutor(position, fugle_account)
    records = cast(list[dict], order_executor.create_orders(view_only=True))
    # If `view_only=False`, actually create the orders.
    if not view_only:
        order_executor.create_orders(view_only=False)
    return records


if __name__ == "__main__":
    # Call the GCF endpoint.
    # If `directly = True`, it will call the function directly.
    # Otherwise, it will simulate a request to GCF and pass the `params` by request body.
    # The arguments will be overwrited by CLI arguments, like `python main.py -d`
    # See method `call_gcf_endpoint` docstring for more information.
    project.call_gcf_endpoint(params={"view_only": True, "fund": 10000, "odd_lot": True})
