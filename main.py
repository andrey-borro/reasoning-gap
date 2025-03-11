from typing import Literal

import json
import os

import experiment_code as ec 

def generate_initial_blocksworld_solutions(
        problem_set: str,
        model_name: Literal['gpt-4o-mini-2024-07-18', 'gpt-4o-2024-11-20', 'o1-mini-2024-09-12', 'o1-preview-2024-09-12'],
        main_solution_directory: str,
        *,
        strategy: str = None,
        summarise_solutions: bool = True
):
    """Generates response files for `problem_set` into `{target_dir}/round_0` using the `model_name` model. 
    By default will summarise solutions into a json file, then evaluate them and save the solution results.

    Will use no strategy if strategy is None (default), or `strategy` if it is given.
    
    If you wish to use a different model from `gpt-4o-2024-11-20` to summarise, you will have to set `summarise_solutions` to False, 
    and do it manually using `generate_solution_summaries`. 
    """

    if not ec.make_directory(main_solution_directory): # setup the directory.
        return
    
    initial_round_dir = f'{main_solution_directory}/round_0'

    os.mkdir(initial_round_dir) # makes the initial dir

    # load problems from problem_set (tag, opt_cost, state, num_blocks)
    with open(problem_set) as in_file:
        problems: list[dict] = json.load(in_file)
    
    for index, problem in enumerate(problems):
        print(f'Generating response file {index + 1}/{len(problems)} to {problem["tag"]}')
        state = (None, problem['state'])
        file_path = f'{initial_round_dir}/{problem['tag']}_response.json'
        ec.generate_initial_blocksworld_solution(state, strategy, file_path, model_name)
    
    if summarise_solutions:
        generate_blocksworld_solutions_summary(problem_set, f'{initial_round_dir}/round_0')
        evaluate_solution_file(problem_set, initial_round_dir)


def generate_blocksworld_solutions_summary(problem_set: str, responses_directory: str, *, summary_model: str = 'gpt-4o-2024-11-20') -> None:
    """Summarises the solutions from `response_dir` against the `problem_set` file, into one json file.
    
    File format: `{prob_tag : action_list}`. `action_list` is `list[str]` 

    Summary model is optional argument to set the GPT model. 
    """

    # load problems from dir (tag, opt_cost, state, num_blocks)
    with open(problem_set) as in_file:
        problems: list[dict] = json.load(in_file)
    
    solutions = {}
    solutions_file_path  = f'{responses_directory}/solution_summary.json'

    for index, problem in enumerate(problems):
        problem_tag = problem['tag']
        print(f'Summarising solution {index + 1}/{len(problems)} for {problem_tag}', end = ' ')

        if problem_tag in solutions:
            print(f'WARNING: Overwriting entry {problem_tag} to solutions file in {responses_directory}')

        response_file_path = f'{responses_directory}/{problem_tag}_response.json'
        try:
            solutions[problem_tag] = ec.generate_blocksworld_solution_summary(response_file_path, summary_model)
        except FileNotFoundError:
            print(f'Skipping {response_file_path} (does not exist).')
            continue # skip over the ones that ddon't have responses 

        with open(solutions_file_path, 'w') as wfile:
            json.dump(solutions, wfile)
        
        print(f'(saved to {solutions_file_path})')
    
    # realistically this is only ever useful when the dict is entirely empty (all previous solutions were correct),
    # but it is a simple fix to any missing file shenanigans
    with open(solutions_file_path, 'w') as wfile:
        json.dump(solutions, wfile)

def evaluate_solution_file(problem_set: str, response_dir: str): #TODO - fix this up
    """Evaluates the solutions from the `{response_dir}/solution_summary.json` file against the `problem_set` file. 
    
    Stores result data in `{response_dir}/solution_results.json` 
    """
    # load problems from dir (tag, opt_cost, state, num_blocks)
    with open(problem_set) as in_file:
        problems: list[dict] = json.load(in_file)
    
    solution_file_path = f'{response_dir}/solution_summary.json'
    with open(solution_file_path) as in_file:
        solutions_dict: dict = json.load(in_file)
    results = []

    for problem in problems:
        try:
            model_used = solutions_dict[problem['tag']]['model_used']
            solution = solutions_dict[problem['tag']]['solution']
        except KeyError:
            continue # skip over the ones not in the solution file
        result_entry = ec.evaluate_blocksworld_solution(problem, solution, model_used)
        results.append(result_entry)
    
    with open(f'{response_dir}/solution_results.json', 'w') as outfile:
        json.dump(results, outfile)

    print(f'Evaluated {solution_file_path}, with results saved to {response_dir}/solution_results.json')
    return results

def do_blocksworld_error_correction(
        problem_set: str, 
        parent_dir: str, 
        stop_round: int, 
        correction_model: str, 
        *, 
        start_round: int = 0, 
        strategy: str = None,
        summarise_solutions: bool = True,
        repeat_only: bool = False
    ):

    """Performs blocksworld error correction across the round directories in `parent_dir`. 
    `repeat_only` if skipping the error information and just repeating the query as-is."""

    for current_round in range(start_round, stop_round + 1):
        print() # makes some space for the logs
        from_dir = f'{parent_dir}/round_{current_round}'
        to_dir = f'{parent_dir}/round_{current_round + 1}'

        if not os.path.exists(from_dir):
            raise FileNotFoundError(f'Faulty from_dir : {from_dir}')

        solution_file_path = f'{from_dir}/solution_results.json'
        ec.error_correct_blocksworld_solution_file(solution_file_path, to_dir, correction_model, strategy = strategy, repeat_only = repeat_only)
        if summarise_solutions:
            generate_blocksworld_solutions_summary(problem_set, to_dir)
            evaluate_solution_file(problem_set, to_dir)

def generate_blocksworld_strategies(num_strategies: int, model_name: str, target_dir: str):
    """Strongest model as of Dec 2024 is `o1-preview-2024-09-12`"""
    if not ec.make_directory(target_dir): # setup the directory.
        return
    
    os.mkdir(f'{target_dir}/responses') # dump the response pickles in here
    
    for i in range(num_strategies):
        print(f'Generating strategy {i+1}/{num_strategies}')
        ec.generate_blocksworld_strategy(target_dir, i+1, model_name)


def generate_initial_crt_solutions(
        problems_json_path: str, 
        answer_json_path: str, 
        answer_model: Literal['gpt-3.5-turbo-0125', 'gpt-4o-mini-2024-07-18', 'gpt-4o-2024-11-20', 'o1-mini-2024-09-12'], 
        *, 
        strategy: str | None = None, 
        summary_model: str | None = 'o1-mini-2024-09-12' 
    ) -> None:
    with open(problems_json_path) as infile:
        problems_dict = json.load(infile)
    
    answer_dict = {}

    for index, (prob_tag, value) in enumerate(problems_dict.items()):
        print(f'Solving CRT {prob_tag} [{index + 1}/{len(problems_dict)}]', end = ' ')
        answer_dict[prob_tag] = value
        target_answer = answer_dict[prob_tag]['answer']

        solution_text = ec.generate_crt_solution(value['question'], strategy, answer_model)
        proposed_answer = ec.summarise_crt_solution(solution_text, summary_model)

        answer_dict[prob_tag]['proposed_answer'] = proposed_answer
        if proposed_answer is None:
            answer_dict[prob_tag]['result'] = 'UNPARSEABLE'
        elif target_answer['A'] == proposed_answer['A'] and target_answer['B'] == proposed_answer['B']:
            answer_dict[prob_tag]['result'] = 'CORRECT'
        else:
            answer_dict[prob_tag]['result'] = 'INCORRECT'

        print(f'RESULT: {answer_dict[prob_tag]['result']}')

        if index % 10 == 0:
            print(f'Autosaving to {answer_json_path}.')
            with open(answer_json_path, 'w') as outfile:
                json.dump(answer_dict, outfile, indent = 2)

    with open(answer_json_path, 'w') as outfile:
        json.dump(answer_dict, outfile, indent = 2)


def generate_crt_strategies(num_strategies: int, model_name: str, target_dir: str):
    """Strongest model as of Dec 2024 is `o1-preview-2024-09-12`"""
    if not ec.make_directory(target_dir): # setup the directory.
        return
    
    os.mkdir(f'{target_dir}/responses')
    
    for i in range(num_strategies):
        print(f'Generating CRT strategy {i+1}/{num_strategies}')
        ec.generate_crt_strategy(target_dir, i+1, model_name)


def do_crt_error_correction(
        solution_file_tag: str,
        correction_model: Literal['gpt-3.5-turbo-0125', 'gpt-4o-mini-2024-07-18', 'gpt-4o-2024-11-20', 'o1-mini-2024-09-12'], 
        stop_round: int,
        *, 
        strategy: str | None = None, 
        summary_model: str | None = 'o1-mini-2024-09-12',
        start_round: int = 0
    ):
    """Repeats incorrect CRT corrections x number of times. `solution_file_tag` should be file path without the .json"""
    
    # we cheese it here slightly by just regenerating the problem_set and the running the crt initial_answers code again.
    for current_round in range(start_round, stop_round):
        solution_file = f'{solution_file_tag}_round_{current_round}' if current_round > 0 else solution_file_tag
        with open(f'{solution_file}.json') as infile:
            solutions = json.load(infile)

        temp_problems = {}
        for key in solutions:
            if not solutions[key]['result'] == 'CORRECT':
                temp_problems[key] = {
                    'question' : solutions[key]['question'],
                    'answer' : solutions[key]['answer']
                }
        
        with open(f'{solution_file}_temp_corrections.json', 'w') as outfile:
            json.dump(temp_problems, outfile, indent = 2)
        
        print(f'\nRunning error correction on {solution_file_tag}, round {current_round + 1}\n')
        generate_initial_crt_solutions(
            f'{solution_file}_temp_corrections.json', 
            f'{solution_file_tag}_round_{current_round + 1}.json',
            correction_model,
            strategy = strategy,
            summary_model = summary_model
        )

        os.remove(f'{solution_file}_temp_corrections.json') # delete any evidence of what we have done