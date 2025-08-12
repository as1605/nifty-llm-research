@get_prompt_config @setup_db.py  @PromptConfig 
Create a setup script which seeds the db with a basic prompt for each usecase. Also add a description to the PromptConfig, which the user can set.
When querying for a promptconfig, we should use only name and parameter default=True. If the result is None, we should run the db seeder function, and retry again.


Add instructions inside the prompt to tell the LLM to output only the JSON, without any other text


get_prompt_config should take in only "name" as a parameter, and in case the prompt is not found even after seeding, just throw an error which is visible to the user


update @stock_research.py  accordingly and also save its base prompt in the seed. For parsing the JSON, use json.loads instead of eval function


the model should be fetched from the prompt config rather than keeping it as a property of the class itself


move the temperature also to the promptconfig, save it in the db


get_completion should take in only the prompt config and the params, and it should interpolate the string itself rather than taking from the inherited class