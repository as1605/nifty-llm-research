Change yfinance output given to LLM to be of this format, fetch all relevant data using API. Update all functions accordingly and do not fetch unneeded data. Handle empty results too
@stock_research.py @yfinance_service.py 
**Stock Analysis Data for: [Company Name] ([TICKER.NS])**
**Date of Data:** [e.g 2025-09-16]
---
**## Key Information**
- **Beta:** [e.g., 1.45]
- **52-Week Range:** [e.g., ₹120.50 - ₹250.00]
- **Previous Close:** [e.g., ₹210.75]
- **10-Day Avg Volume:** [e.g., 1,500,000]
- **Day's Range:** [e.g., ₹208.10 - ₹215.40]
---
**## Recent News Headlines**
- **[Timestamp 1]:** [Headline 1] (Publisher: [Publisher 1])
- **[Timestamp 2]:** [Headline 2] (Publisher: [Publisher 2])
- **[Timestamp 3]:** [Headline 3] (Publisher: [Publisher 3])
---
**## Price and Volume History (Last 20 Days)**
- **2025-09-15:** Open: 208.50, High: 215.40, Low: 208.10, Close: 210.75, Volume: 2,100,000
- **2025-09-12:** Open: 205.00, High: 209.20, Low: 204.50, Close: 208.25, Volume: 1,850,000
- **2025-09-11:** Open: 202.10, High: 206.00, Low: 201.80, Close: 204.90, Volume: 1,600,000
- ... (and so on for the last 20 trading days)



Calculate gain using LTP from yfinance and target_price instead of taking it as response from LLM.

If the calculated gain is very different from the gain given by LLM, (off by more than 10%), then log a warning


If URL does not begin with http, append it to prevent error