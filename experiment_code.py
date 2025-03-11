import os
import re
import json

from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion

from prompts import *
from block_code import test_plan, int_state_to_char

# TODO - this is new!
def make_directory(dir_name: str) -> bool:
    """Creates the last directory in the dirpath. Will abort if the parent dir does not exist or `dir_name` already exists."""
    try:
        os.mkdir(dir_name)
    except FileNotFoundError:
        print(f'Only the top directory is created automatically (`{dir_name}` is invalid).')
        return False
    except FileExistsError:
        print(f'Directory {dir_name} already exists. Aborting.')
        return False
    
    return True


def get_response(client: OpenAI, messages: dict, model_name: str) -> ChatCompletion:
    """Returns an OpenAI ChatCompletion object in response to a messages dict input (see OpenAI docs for more info)"""
    # messages = [{'role': 'user', 'content': [ {'type': 'text', 'text': user_text} ]}]
    response = client.chat.completions.create(
        model = model_name,
        messages = messages
    )

    return response

def generate_response_file(file_path: str, messages: dict, model_name: str) -> None:
    # TODO - this needs testing for sure - major change.
    """
    Saves the messages dict and response info in `.json` format to `file_path`.

    #### Messages example: 
    ```
    [ 
        {"role": "user", "content": [{"text": `text`, "type": "text"}]},
        {"role": "assistant", "content": [{"text": `text`, "type": "text"}]}
    ]
    ```
    ### Main Dict Format:
    - messsages
    - response
        - content
        - model
        - output_tokens (not incl. reasoning)
        - input_tokens
        - reasoning_tokens
    """
    client = OpenAI(api_key = os.getenv('OPENAI_API_KEY_LAB')) # replace with however you store your key
    response = get_response(client, messages, model_name)

    # I only keep the parts of the response that I personally care about. 
    # If you need to get at/store more information this is the place to do that. 

    save_dict = {
        'messages' : messages,
        'response' : {
            'content': response.choices[0].message.content,
            'model': response.model,
            'output_tokens': response.usage.completion_tokens - response.usage.completion_tokens_details.reasoning_tokens,
            'input_tokens': response.usage.prompt_tokens,
            'reasoning_tokens' : response.usage.completion_tokens_details.reasoning_tokens
        }
    }
    with open(file_path, 'w') as save_file:
        json.dump(save_dict, save_file)

def generate_general_strategy(strategy_prompt: str, target_dir: str, strategy_num: int, model_name: str):
    """Generates a strategy to `target_dir`."""
    messages = [{'role': 'user', 'content': [{'text': strategy_prompt, 'type': 'text'}]}]
    infile_path = f'{target_dir}/responses/strategy_{strategy_num}_response.json'
    outfile_path = f'{target_dir}/strategy_{strategy_num}.json'
    generate_response_file(infile_path, messages, model_name)
    with open(infile_path, 'r') as infile:
        save_data = {'strategy' : json.load(infile)['response']['content']}
    with open(outfile_path, 'w') as outfile:
        json.dump(save_data, outfile)

# PDDL / BlocksWorld

def parse_pddl_text(text: str) -> list[str]:
    """Parses a `str` response into a `list[str]` of PDDL actions."""
    action_list  = []
    for action in text.strip().split('\n'):
        action = action.strip()
        if action[0] + action[-1] == '()':
            action_list.append(action)

    return action_list


def generate_blocksworld_solution_summary(response_file_path: str, summary_model: str) -> dict:
    """Takes a .json filepath as input, with the input messages and response data inside the file. 
    Returns a dictionary with list of BlocksWorld PDDL actions from the solution in the ChatCompletion (`solution`), 
    and the model used to create the initial (pre-summary) solution (`model_used`)."""

    client = OpenAI(api_key = os.getenv('OPENAI_API_KEY_LAB')) # replace with however you store your key

    with open(response_file_path, 'r') as load_file: 
        response_data = json.load(load_file)
    
    response_text = response_data['response']['content']
    model_used = response_data['response']['model']

    messages = [
        {"role": "assistant", "content": [{"text": response_text, "type": "text"}]},
        {'role': 'user', 'content': [{'text': BLOCKSWORLD_SUMMARY_PROMPT, 'type': 'text'}]}
    ]

    summary: ChatCompletion = get_response(client, messages, summary_model)
    solution = parse_pddl_text(summary.choices[0].message.content)

    return {
        'model_used' : model_used,
        'solution' : solution
    }

def evaluate_blocksworld_solution(problem: dict, solution: list[str], model_used: str):
    """Evaluates the list of actions in solution `solution` as a solution to the state in `problem`. Returns the full `dict` for forming `solution_results.json`"""
    state = int_state_to_char((None, problem['state']))
    result_entry = {
        'problem_data' : problem,
        'result_data' : {
            'solution' : solution, # list[str]
            'solution_length': len(solution), # int
            'test_result' : test_plan(solution, state), # dict - result, last_action, final_state
        }
    }

    # small QOL touchup
    result_entry['problem_data']['state'] = state
    result_entry['result_data']['model_used'] = model_used

    return result_entry

def generate_blocksworld_strategy(target_dir: str, strategy_num: int, model_name: str):
    generate_general_strategy(BLOCKSWORLD_STRATEGY_PROMPT, target_dir, strategy_num, model_name)


def generate_initial_blocksworld_solution(state: tuple[str | int | None, list[list[str | int]]], strategy: str, file_path: str, model_name: str):
    """Generates a response file for a given blocksworld tasks to the `file_path`"""
    prompt = get_blocksworld_task_prompt(int_state_to_char(state), strategy)
    messages = [{'role': 'user', 'content': [{'text': prompt, 'type': 'text'}]}]
    generate_response_file(file_path, messages, model_name)

#TODO - just dumped the below ones in
def error_correct_blocksworld_solution_file(
        solution_file: str,
        destination_directory: str, 
        correction_model : str, 
        *, 
        strategy: str = None,
        repeat_only: bool = False
    ):
    """
    Corrects the incorrect tasks from `solution_file`, into `destination_directory`. 
     - `repeat_only` for removing the error correction message and just running the task again instead.
    """

    if not make_directory(destination_directory): # setup the directory.
        raise FileExistsError(f'ERROR: {destination_directory} already exists.')

    with open(solution_file) as in_file:
        result_dicts: dict = json.load(in_file)

    print(f'Loaded {solution_file} for correction.')

    for index, result_dict in enumerate(result_dicts):
        problem = result_dict['problem_data']
        solution = result_dict['result_data']['solution']
        result_type = result_dict['result_data']['test_result']['result']
        last_action = result_dict['result_data']['test_result']['last_action']
        final_state = result_dict['result_data']['test_result']['final_state']

        if result_type == 'SUCCESS': # skip the ones that dont need correcting
            continue

        print(f'Correcting {problem['tag']} [{index + 1}/{len(result_dicts)}]' + (' (repeat only)' if repeat_only else ''))

        messages = [ 
            {'role': 'user', 'content': [{'text': get_blocksworld_task_prompt(problem['state'], strategy), 'type': 'text'}]},
        ]

        # TODO - make sure this works.
        if not repeat_only:
            messages.append({'role': 'assistant', 'content': [{'text': '\n'.join(solution), 'type': 'text'}]})
            messages.append({'role': 'user', 'content': [{'text': get_blocksworld_fix_prompt(result_type, last_action, final_state), 'type': 'text'}]})

        generate_response_file(f'{destination_directory}/{problem['tag']}_response.json', messages, correction_model)

# CRT Type 3

def extract_crt_formula(solution_text: str) -> str:
    """Returns the extracted answer from the larger CRT solution in order to mask the task and reasoning steps from the summarisation model."""
    cleaned_text = solution_text.replace('\n', ' ').replace('\'', '"').strip()
    re_match = re.search(r'@@(.*?)@@', cleaned_text)

    try:
        return re_match.group(1)
    except:
        return 'NONE'
    
def parse_crt_formula(formula_text: str) -> dict | None:
    """Turns the summarised formula text into a dictionary format, so that it can be easily evaluated.
    
    Expected return format:

    `{'A': int, 'B': int}` or `None`
    """
    cleaned_text = formula_text.replace('\n', ' ').replace('\'', '"').strip()
    re_match = re.search(r'(\{.*?\})', cleaned_text)
    try:
        json_string = re_match.group(1)
        return json.loads(json_string)
    except:
        return None

def generate_crt_strategy(target_dir: str, strategy_num: int, model_name: str):
    generate_general_strategy(CRT_STRATEGY_PROMPT, target_dir, strategy_num, model_name)

def generate_crt_solution(question: str, strategy: str | None, answer_model: str) -> str:
    """Takes a CRT `question`, `strategy` and `answer_model` (all str).
    
    Returns `solution` string.
    """
    client = OpenAI(api_key = os.getenv('OPENAI_API_KEY_LAB')) # replace with however you store your key
    messages = [{'role': 'user', 'content': [{'text': get_crt_task_prompt(question, strategy), 'type': 'text'}]}]
    response = get_response(client, messages, answer_model)

    return response.choices[0].message.content

def summarise_crt_solution(solution_text: str, summary_model: str) -> dict | None:
    """Summarises the solution text into a json dict with A and B values for AY - BX"""
    client = OpenAI(api_key = os.getenv('OPENAI_API_KEY_LAB')) # replace with however you store your key
    solution_formula = extract_crt_formula(solution_text)

    messages = [
        {"role": "assistant", "content": [{"text": solution_formula, "type": "text"}]},
        {'role': 'user', 'content': [{'text': CRT_SUMMARY_PROMPT, 'type': 'text'}]}
    ]
    response = get_response(client, messages, summary_model)
    json_text = response.choices[0].message.content
    return parse_crt_formula(json_text)





