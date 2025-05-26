# 📊 LLM-Based Stock Research & Forecasting Agent

A modular stock research system has been designed to automate deep financial analysis and price forecasting of the NSE Top 100 stocks using LLM agents, web search, and financial document parsing. Forecasts are generated daily and saved to a PostgreSQL database, followed by the creation and mailing of an optimized weekly stock basket.

---

## 📚 Table of Contents

* [📊 LLM-Based Stock Research & Forecasting Agent](#-llm-based-stock-research--forecasting-agent)
* [🧭 Overview of the Workflow](#-overview-of-the-workflow)
* [🧠 Deep Research Agent](#-deep-research-agent)
* [🗃️ Result Storage to Aurora PostgreSQL](#️-result-storage-to-aurora-postgresql)
* [📈 Weekly Stock Basket Selector](#-weekly-stock-basket-selector)
* [🔁 Daily Scheduling](#-daily-scheduling)
* [📬 Email Integration (Amazon SES)](#-email-integration-amazon-ses)
* [🛠️ Tools and Technologies](#️-tools-and-technologies)

---

## 🧭 Overview of the Workflow

1. **Deep Research Agent** is invoked for each of the NSE Top 100 stocks daily.
2. **Market data**, **financial news**, and **investor reports** are gathered and analyzed using an LLM agent.
3. **Forecasted prices** are generated for the next:

   * 1 week
   * 1 month
   * 3 months
   * 6 months
   * 12 months
4. The results are saved to an **Amazon Aurora PostgreSQL** database.
5. After processing all stocks, a **portfolio optimization script** is run:

   * Top 5 stocks for the week are selected based on predicted returns.
   * The basket is saved to the database and emailed using **Amazon SES**.

---

## 🧠 Deep Research Agent

* Implemented in **Python** using **OpenAI API**, **agents**, and **tools**.
* Accepts a stock symbol and company name as input.
* Performs the following steps:

  * Conducts **web searches** to gather latest news and investor sentiment.
  * Fetches **financial quote and chart data** using APIs (e.g., Yahoo Finance, Alpha Vantage).
  * Parses **PDF reports** of investor briefings and market analysis (using tools like `PyMuPDF` or `pdfplumber`).
  * Uses the context to **forecast future stock prices** for the specified timeframes.
* Returns:

  ```json
  {
    "stock": "RELIANCE",
    "current_price": 2750.50,
    "forecast_1w": 2805.75,
    "forecast_1m": 2880.10,
    "forecast_3m": 2970.25,
    "forecast_6m": 3100.50,
    "forecast_12m": 3350.00
  }
  ```

---

## 🗃️ Result Storage to Aurora PostgreSQL

* A database-saving function is provided.
* Accepts the LLM output and saves it into a relational format with a timestamp and symbol key.
* Ensures **daily inserts** and supports **historical querying** for trend analysis.
* Example schema:

  ```sql
  CREATE TABLE stock_forecasts (
    id SERIAL PRIMARY KEY,
    stock_symbol VARCHAR(10),
    current_price NUMERIC,
    forecast_1w NUMERIC,
    forecast_1m NUMERIC,
    forecast_3m NUMERIC,
    forecast_6m NUMERIC,
    forecast_12m NUMERIC,
    forecast_date DATE DEFAULT CURRENT_DATE
  );
  ```

---

## 📈 Weekly Stock Basket Selector

* Invoked once daily after all 100 stocks have been processed.
* Reads all forecast entries for the current date from the database.
* Passes the data to an LLM with a prompt to select the **top 5 most promising stocks** based on short- to mid-term returns.
* Generates a structured basket output:

  ```json
  {
    "basket_date": "2025-05-27",
    "selected_stocks": ["INFY", "RELIANCE", "HDFCBANK", "LT", "TCS"],
    "reasoning_summary": "...",
    "expected_1m_return": "12.5%"
  }
  ```
* Sends the output as an **email via Amazon SES**.
* Saves the basket to a new `weekly_baskets` table in the DB:

  ```sql
  CREATE TABLE weekly_baskets (
    id SERIAL PRIMARY KEY,
    basket_date DATE,
    selected_stocks TEXT[],
    summary TEXT
  );
  ```

---

## 🔁 Daily Scheduling

* To be executed as part of a **cron job or scheduler**:

  1. Loop through NSE Top 100 stocks → run deep research agent → store forecasts.
  2. After all stocks → generate and email weekly basket → save to DB.

---

## 📬 Email Integration (Amazon SES)

* Email reports are composed in plain text or HTML.
* Sent via **Amazon SES** using SMTP credentials or the AWS SDK.
* Includes:

  * Selected stock symbols
  * Summary of LLM rationale
  * Links to database or dashboards (if available)

---

## 🛠️ Tools and Technologies

* **Python**
* **OpenAI GPT APIs**
* **Amazon Aurora PostgreSQL**
* **Amazon SES**
* **Web scraping & search tools**
* **PDF parsing tools**
* **Financial data APIs (e.g., Yahoo Finance)**
