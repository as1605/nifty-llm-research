Rather than requesting the LLM to do analysis for 7, 30, 90, 180, 365 days, ask it to do for 3, 7, 14, 30 days instead. And make it try to optimise the returns for 1 week instead of 1 month. Update the logic everywhere the assumption of the previous long term dates was made @seed_prompts.py @stock_research.py @portfolio.py

Update the portfolio_basket prompt to focus on short term (maximising returns in one week) rather than long term (months) @seed_prompts.py 

