For analyze_stocks, make a flag --parallel which should be false by default, and if enabled, should use the taskgroup, otherwise should process each stock one by one in a for loop

force-llm should require 5 forecasts to be present. 

In the markdown output in docs/basket, also write the sources used for each selected stock. In the sources, give the domain name instead of 1 2 3 4 as the link preview. each link in a new line

Do not log a warning when Initial JSON parsing failed.

Color the logs according to the level.

Add shorter alias for each flag in the scripts. Shorten --force-llm to -fl, --force-nse to -fn and -f should mean both enabled. Shorten --index to -i and --parallel to -p. Shorten --filter-top-n to -n and --basket-size-k to -k and --since-days to -d

The name of the generated outputs should have the current date and time instead of the since date

Save usage_metadata also in the metadata of each LLM call

In the index.md, give the link to the output without .md extension, so it renders in GitHub Pages