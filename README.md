This is the code release for the paper [Bridging the Reasoning Gap: Small LLMs Can Plan with Generalised Strategies](https://arxiv.org/abs/2501.18817). It contains all the neccessary code to replicate the results of the paper, the results themselves, most responses from the LLMs used and the code to generate the tables found in the paper. 

The only requirement for this code is Python (my current version is `3.11`) and the `openai` module. The version number used by the authors can be found in `requirements.txt`.

Repository Structure:

<pre>
🛠️ reasoning-gap
├── 📁 examples                                         
│   ├── 📁 problem_sets                                 
│   │   ├── 📄 crt_problem_set.json 
│   │   ├── 📄 example_blocksworld_set.json             
│   ├── 📁 responses
│   │   ├── 📁 blocksworld                              
│   │   │   ├── 📁 strategy_1_example_set
│   │   │   │   ├── 📁 round_0
│   │   │   │   │   ├── 📄 prob_0000_response.json
│   │   │   │   │   ├── 📄 (... more problem responses)
│   │   │   │   │   ├── 📄 solution_results.json
│   │   │   │   │   ├── 📄 solution_summary.json
│   │   │   │   │   ├── 📁 (... more rounds)
│   │   ├── 📁 crt
│   │   │   ├── 📄 answers_example.json
│   │   │   ├── 📄 answers_example_round_1.json
│   │   │   ├── 📄 answers_example_round_2.json
│   ├── 📁 strategies
│   │   ├── 📁 blocksworld
│   │   │   ├── 📄 strategy_1.json                         
│   │   │   ├── 📁 responses
│   │   │   │   ├── 📄 strategy_1_response.json
│   │   ├── 📁 crt
│   │   │   ├── 📄 strategy_1.json                         
│   │   │   ├── 📁 responses
│   │   │   │   ├── 📄 strategy_1_response.json
├── 📁paper_data
│   ├── 📁problem_sets
│   │   ├── 📄crt_3_problem_set.json
│   │   ├── 📄large_problems_20.json
│   │   ├── 📄main_problems_50.json
│   │   ├── 📄mid_problems_20.json
│   ├── 📁responses
│   │   ├── 📁blocksworld
│   │   │   ├── 📁baseline_o1_results
│   │   │   │   ├── 📁no_strategy
│   │   │   │   │   ├── 📁round_0
│   │   │   │   │   │   ├── 📄prob_0000_response.json
│   │   │   │   │   │   ├── 📄prob_0001_response.json
│   │   │   │   │   │   ├── 📄prob_0002_response.json
│   │   │   │   │   │   ├── 📄(... many more responses)
│   │   │   │   │   │   ├── 📄solution_results.json
│   │   │   │   │   │   ├── 📄solution_summary.json
│   │   │   │   │   ├── 📁 (... 5 rounds total)
│   │   │   ├── 📁larger_problem_sizes
│   │   │   │   ├── 📁large_test_problems
│   │   │   │   │   ├── 📁handwritten
│   │   │   │   │   │   ├── 📁round_0
│   │   │   │   │   │   │   ├── 📄prob_0000_response.json
│   │   │   │   │   │   │   ├── 📄prob_0001_response.json
│   │   │   │   │   │   │   ├── 📄prob_0002_response.json
│   │   │   │   │   │   │   ├── 📄(... many more responses)
│   │   │   │   │   │   │   ├── 📄solution_results.json
│   │   │   │   │   │   │   ├── 📄solution_summary.json
│   │   │   │   │   │   ├── 📁 (... 5 rounds total)
│   │   │   │   │   ├── 📁no_strategy
│   │   │   │   │   │   ├── 📁 (... 5 rounds total)
│   │   │   │   │   ├── 📁strategy_1
│   │   │   │   │   │   ├── 📁 (... 5 rounds total)
│   │   │   │   ├── 📁mid_test_problems
│   │   │   │   │   ├── 📁(... same structure as large_test_problems)
│   │   │   ├── 📁o1_mini_results
│   │   │   │   ├── 📁error_correction_through_repetition
│   │   │   │   │   ├── 📁no_strategy
│   │   │   │   │   │   ├── 📁round_0
│   │   │   │   │   │   ├── 📁round_1
│   │   │   │   │   │   │   ├── 📄prob_0000_response.json
│   │   │   │   │   │   │   ├── 📄prob_0002_response.json
│   │   │   │   │   │   │   ├── 📄prob_0003_response.json
│   │   │   │   │   │   │   ├── 📄(... many more responses)
│   │   │   │   │   │   │   ├── 📄solution_results.json
│   │   │   │   │   │   │   ├── 📄solution_summary.json
│   │   │   │   │   │   ├── 📁(... 5 rounds total)
│   │   │   │   │   ├── 📁strategy_1
│   │   │   │   │   │   ├── 📁round_0
│   │   │   │   │   │   ├── 📁round_1
│   │   │   │   │   │   │   ├── 📄prob_0002_response.json
│   │   │   │   │   │   │   ├── 📄prob_0005_response.json
│   │   │   │   │   │   │   ├── 📄prob_0007_response.json
│   │   │   │   │   │   │   ├── 📄(... many more responses)
│   │   │   │   │   │   │   ├── 📄solution_results.json
│   │   │   │   │   │   │   ├── 📄solution_summary.json
│   │   │   │   │   │   ├── 📁(... 5 rounds total)
│   │   │   │   │   ├── 📁(... 2 more generated strategies)
│   │   │   │   ├── 📁main_results
│   │   │   │   │   ├── 📁handwritten
│   │   │   │   │   │   ├── 📁round_0
│   │   │   │   │   │   │   ├── 📄prob_0000_response.json
│   │   │   │   │   │   │   ├── 📄prob_0001_response.json
│   │   │   │   │   │   │   ├── 📄prob_0002_response.json
│   │   │   │   │   │   │   ├── 📄prob_0003_response.json
│   │   │   │   │   │   │   ├── 📄(... many more responses)
│   │   │   │   │   │   │   ├── 📄solution_results.json
│   │   │   │   │   │   │   ├── 📄solution_summary.json
│   │   │   │   │   │   ├── 📁 (... 5 rounds total)
│   │   │   │   │   ├── 📁(no_strategy + 3 generated strategies)
│   │   ├── 📁crt
│   │   │   ├── 📁3.5_turbo
│   │   │   │   ├── 📁generated_strategy_1
│   │   │   │   │   ├── 📄round_0_results.json
│   │   │   │   │   ├── 📄round_1_results.json
│   │   │   │   │   ├── 📄round_2_results.json
│   │   │   │   ├── 📁(... 2 more generated strategies)
│   │   │   │   ├── 📁handwritten_strategy
│   │   │   │   │   ├── 📄round_0_results.json
│   │   │   │   │   ├── 📄round_1_results.json
│   │   │   │   │   ├── 📄round_2_results.json
│   │   │   │   ├── 📁no_strategy
│   │   │   │   │   ├── 📄round_0_results.json
│   │   │   │   │   ├── 📄round_1_results.json
│   │   │   │   │   ├── 📄round_2_results.json
│   │   │   ├── 📁4o
│   │   │   │   ├── 📁(... same structure as above)
│   │   │   ├── 📁4o_mini
│   │   │   │   ├── 📁(... same structure as above)
│   ├── 📁strategies
│   │   ├── 📁blocksworld
│   │   │   ├── 📁responses
│   │   │   │   ├── 📄generated_strategy_1_response.json
│   │   │   │   ├── 📄generated_strategy_2_response.json
│   │   │   │   ├── 📄generated_strategy_3_response.json
│   │   │   ├── 📄strategy_generated_1.json
│   │   │   ├── 📄strategy_generated_2.json
│   │   │   ├── 📄strategy_generated_3.json
│   │   │   ├── 📄strategy_handwritten.json
│   │   ├── 📁crt
│   │   │   ├── 📄crt_strategy_generated_1.json
│   │   │   ├── 📄crt_strategy_generated_2.json
│   │   │   ├── 📄crt_strategy_generated_3.json
│   │   │   ├── 📁responses
│   │   │   │   ├── 📄generated_strategy_1_response.json
│   │   │   │   ├── 📄generated_strategy_2_response.json
│   │   │   │   ├── 📄generated_strategy_3_response.json
│   │   │   ├── 📄strategy_handwritten.json
├── 📄actions.py
├── 📄block_code.py
├── 📄crt_templates.json
├── 📄experiment_code.py
├── 📄generate_problem_sets.py
├── 📄main.ipynb
├── 📄main.py
├── 📄prompts.py
├── 📄README.md
├── 📄requirements.txt
├── 📄tables.ipynb
</pre>
