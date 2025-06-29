Understand the structure of the Forecast, which is used in optimize_portfolio. Now, rather than getting the expected_1m_gain from the LLM, we want to calculate it as the weighted average of the 1m gains of those stocks, where the weight will be it's corresponding weight in the portfolio as given in the Basket output. Also, handle the case where a stock has multiple 1 month forecasts, so you should take average of them first.

Modify the model to make it an optional field

stock_picker_candidates should have the unique stocks rather than repeated entries of same stock