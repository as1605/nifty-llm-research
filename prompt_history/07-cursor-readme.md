@nifty-llm-research @README.md 
Go through the entire codebase again and update the README, by taking into account the changes done, also add new instructions for setup and running the code. 

Ensure everything is migrated from SQL to MongoDB, OpenAI to Perplexity, and uv to pip venv

Also add a changelog by going through the history of git diff, and summarising each change.

Also generate a small guide for anyone who wants to understand how this repository is working and encourage them to contribute by following the best practices, and logging the prompts for each change in the prompts directory.

Update all the .cursor/rules accordingly. Clean any outdated or unused code

If these tasks are too large, divide into subtasks and perform them sequentially


The prompts directory is still not to be accessed or modified by Cursor, update the .cursor/rules accordingly. Mention in the README that a new user can refer to it to see what all prompts were run to generate this repository. Encourage any future modification should also be added as a new file.


Move the changelog to a separate markdown file from the README. Generate a detailed changelog by first going through the git diff of each commit in the git log. Each commit should be summarised in upto 100 words, with key code references which had major changes