#!/bin/python3

from openai import OpenAI
import random
import argparse
import os
from dotenv import load_dotenv
import json
import shlex

# Load environment variables from the .env file
load_dotenv()

# Retrieve the API key from the environment
api_key = os.getenv("API_KEY")

if not api_key:
    print("API Key not defined. Finishing...")
    exit()

client = OpenAI(api_key=api_key)

question_answers = {}

language = None
while language not in ['e', 's']:
    language = input("Please choose your language: (E)nglish or (S)panish: ").strip().lower()


# Parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Script for storing and retrieving conversation history.")
    parser.add_argument('--history_file', type=str, help="The path to the conversation history file.")
    args = parser.parse_args()
    return args.history_file

# Define the HISTORY_FILE variable, either from the argument or default to an empty string
HISTORY_FILE = parse_arguments() if parse_arguments() else "history/default_history.str"

# Function to simulate an AI model response
def ai_response(model, prompt, role):
    messages=[
        {"role": role, "content": prompt},
    ]
    response = client.chat.completions.create(model=model,  # Ensure 'model' is used instead of 'engine'
    messages=messages,
    max_tokens=2150)
    return response.choices[0].message.content


def save_last_conversation(question, answer):
    """Save the last question and answer to a file"""
    if HISTORY_FILE:
        with open(HISTORY_FILE, "a") as f:
            f.write(question)
            f.write("\n\n")
            f.write('-' * 80)
            f.write("\n\n")
            f.write(answer)
            f.write("\n\n")
            f.write('-' * 80)
            f.write("\n\n")
        # print(f"Conversation saved to {HISTORY_FILE}.")
    else:
        print("No history file specified. Skipping save...")


def load_last_conversation():
    if HISTORY_FILE and os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            lines = f.readlines()  # Read the file line by line

        messages = []
        current_message = []
        is_in_separator = False

        for i, line in enumerate(lines):
            # Check for the separator pattern
            if (
                line.strip() == "" and 
                i + 1 < len(lines) and lines[i + 1].strip() == "-" * 80 and 
                i + 2 < len(lines) and lines[i + 2].strip() == ""
            ):
                # If we find a separator, save the current message
                if current_message:
                    messages.append("\n".join(current_message).strip())
                    current_message = []  # Reset for the next message
                is_in_separator = True  # Mark that we are in a separator
            elif is_in_separator:
                # Skip the next two lines of the separator
                is_in_separator = False
            else:
                # Add the current line to the ongoing message
                current_message.append(line.strip())

        # Add the last message if any
        if current_message:
            messages.append("\n".join(current_message).strip())

        # Remove the last message if it's empty
        if messages and not messages[-1].strip():
            messages.pop()

        return messages

    return []  # Return an empty list if no file or data found


def translate(prompt, lang = language):
    if lang == 'e':
        return prompt

    spanish = {
        "Input the topic of this conversation: ": "¿Cuál va a ser el tema para esta charla? ",
        'This is all about ': 'Todo esto está relacionado con ',
        "\nDo you want to control the conversation? (y/n): ": "\n¿Querés controlar la charla? (s/n): ",
        "Question: ": "Pregunta: ",
        "Answer: ": "Respuesta: ",
        "\nAre you satisfied with the answer you provided? (y/n): ": "\n¿Estás satisfecho con la respuesta que brindaste? (s/n): ",
        "Last answer was: ": "La última respuesta fue: ",
        "\nNow question is:": "\nAhora la pregunta es:",
        "\nDo you agree with/did you like last question and answer pair? (y/n): ": "\n¿Estás de acuerdo con el último par de pregunta y respuesta? (s/n): ",
        "Last question was: ": "La última pregunta fue: ",
        "\nAnswer is:": "\nLa respuesta es:",
    }

    return spanish[prompt]


# Simulate the interaction between the two participants
def simulate_conversation(participant1_model, participant2_model, turn_limit=1500):
    fixed_topic = input(translate("Input the topic of this conversation: "))
    if fixed_topic:
        fixed_topic = translate('This is all about ') + fixed_topic
    #import pdb; pdb.set_trace()
    turn_count = 0
    last_question = ""
    last_answer = ""
    last_response = ""
    skip_control = 0
    last_msg_was_manual = False
    first_input = True
    historic_conversation = load_last_conversation()
    assume_good_conversation = 0

    if skip_control > 100:
        skip_control = 100

    while turn_count < turn_limit:
        if len(historic_conversation):
            msg = historic_conversation.pop(0)
            print(msg)
            print()  # Empty line
            print("-" * 80)  # Line of dashes
            print()  # Empty line
            turn_count += 1
            # Dismiss last history line if it was a question
            handle_prompt(msg)
            if turn_count % 2 == 0:
                last_question = msg
            else:
                last_answer = msg
                question_answers[last_question] = last_answer

            if len(historic_conversation) == 1 and turn_count % 2 == 0:
                historic_conversation = []
            continue

        # Same question, same answer:
        if turn_count % 2 == 0 and last_question not in question_answers:
            question_answers[last_question] = last_answer

        if turn_count % 2 == 1 and last_question in question_answers:
            last_answer = question_answers[last_question]
            last_response = last_answer
            handle_prompt(last_response)
            skip_control = 0
            turn_count += 1
            continue

        handle_prompt(last_response)

        # Human decides whether to respond or let the AI respond
        if last_msg_was_manual:
            choice = "n"
        else:
            if not first_input:
                choice = input(translate("\nDo you want to control the conversation? (y/n): ")).strip().lower()
                if choice == 's':
                    choice = 'y'
            else:
                choice = "y"

        if choice == "y" and skip_control < 1:
            last_msg_was_manual = True
            if turn_count % 2 == 0:
                last_question = input(translate("Question: "))
                if last_question == "pdb":
                    import pdb; pdb.set_trace()
                    last_question = input("Started Python Debugger. Question: ")

                if last_question.isdigit():
                    skip_control = int(last_question)
                    if skip_control % 2 == 0:
                        skip_control -= 1
                        last_question = ''

                if last_question:
                    turn_count += 1
                    continue
                # else:
                #     import pdb; pdb.set_trace()
            else:
                last_answer = "redo_answer"
                while last_answer == "redo_answer":
                    last_answer = input(translate("Answer: "))
                    if last_answer == "pdb":
                        import pdb; pdb.set_trace()
                        last_answer = input("Answer: ")
                    print("\n\n")
                    if last_answer:
                        choice = None
                        while choice not in ["y", "n"]:
                            if assume_good_conversation:
                                assume_good_conversation -= 1
                                choice = 'y'
                            else:
                                choice = input(translate("\nAre you satisfied with the answer you provided? (y/n): ")).strip().lower()
                                if choice == "pdb":
                                    import pdb; pdb.set_trace()
                                if choice.isdigit():
                                    assume_good_conversation = int(choice)
                                    choice = 'y'
                        if choice == "y":
                            print("")
                            save_last_conversation(last_question, last_answer)
                            turn_count += 1
                            continue
                        else:
                            last_answer = "redo_answer"

        last_msg_was_manual = False
        if skip_control > 0:
            skip_control = skip_control - 1

        if turn_count % 2 == 0:  # Participant 1's turn (AI 1)
            first_part = translate("Last answer was: ")
            last_part = translate("\nNow question is:")
            prompt = f"{fixed_topic}{first_part}{last_answer}{last_part}"
            last_question = ai_response(participant1_model, prompt, "user")
            print(f"{last_question}")
            last_response = last_question

        else:  # Participant 2's turn (AI 2)
            first_part = translate("Last question was: ")
            last_part = translate("\nAnswer is:")
            prompt = f"{fixed_topic}{first_part}{last_question}{last_part}"
            last_answer = ai_response(participant2_model, prompt, "system")
            print(f"{last_answer}")

            choice = None
            while choice not in ['y', 'n']:
                if assume_good_conversation:
                    assume_good_conversation -= 1
                    choice = 'y'
                else:
                    choice = input(translate("\nDo you agree with/did you like last question and answer pair? (y/n): ")).strip().lower()
                    if choice == "s":
                        choice = "y"
                    if choice == "pdb":
                        import pdb; pdb.set_trace()
                    if choice.isdigit():
                        assume_good_conversation = int(choice)
                        choice = 'y'
            if choice == "y":
                save_last_conversation(last_question, last_answer)
                last_response = last_answer
            else:
                last_response = ''
            print("")

        turn_count += 1

    print("\nConversation Ended.")

import subprocess

# Function to ask for confirmation and then execute code
def confirm_execution(code_block):
    print("The following code block is about to be executed:")
    print(code_block)

    confirmation = None
    while confirmation not in ['y', 'n']:
        confirmation = input("\n\nDo you want to execute this batch of code? (y/n): ").strip().lower()
        if confirmation == "pdb":
            import pdb; pdb.set_trace()

    if confirmation == 'y':
        print("Executing code...\n\n")
        # Execute the Bash code
        execute_bash_code(code_block)
    else:
        print("Code execution skipped.")

# Function to execute the Bash code
def execute_bash_code(code_block):
    for command in code_block:
        print("\n\n" + command)

        confirmation = None
        while confirmation not in ['y', 'n']:
            confirmation = input("Do you want to execute this command? (y/n): ").strip().lower()
            if confirmation == "pdb":
                import pdb; pdb.set_trace()
        if confirmation != "y":
            print('Skipping...')
            continue
        try:
            run_command(command)
        except Exception as e:
            print(f"An error occurred: {e}")


def run_command(command):
    """
    Automatically detects and runs a command as interactive or non-interactive.

    Args:
        command (str): The Bash command to execute as a single string.

    """
    # Split the command string into arguments
    args = shlex.split(command)

    # Detect if the command is Docker interactive
    is_docker_interactive = "docker" in args and "-it" in args

    try:
        if is_docker_interactive:
            # Run the interactive Docker command

            process = subprocess.Popen(
                args,
                stdin=None,  # Directly connects to the parent's stdin
                stdout=None,  # Directly connects to the parent's stdout
                stderr=None,  # Directly connects to the parent's stderr
            )
            process.wait()  # Wait for the process to finish
        else:
            # Run non-interactive command

            result = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="")
            if result.returncode != 0:
                print(f"Command failed with return code: {result.returncode}")
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except FileNotFoundError:
        print("Command not found. Please check your input.")
    except Exception as e:
        print(f"An error occurred: {e}")


def extract_code_blocks(prompt, start_delims=("```", "```bash"), end_delim="```"):
    """
    Extract code blocks from a prompt using specified delimiters.
    
    Args:
        prompt (str): The input text containing code blocks.
        start_delims (tuple): Possible start delimiters.
        end_delim (str): The end delimiter.
    
    Returns:
        list: A list of extracted code blocks as strings.
    """
    lines = prompt.splitlines()  # Split the prompt into lines
    code_blocks = []
    is_collecting = False
    current_block = []

    for line in lines:
        if not is_collecting:
            # Check if the line contains any of the start delimiters
            if any(line.strip().startswith(delim) for delim in start_delims):
                is_collecting = True  # Start collecting code
                continue  # Skip the line with the start delimiter
        else:
            # Check if the line contains the end delimiter
            if line.strip() == end_delim:
                is_collecting = False  # Stop collecting code
                code_blocks.append('\n'.join(current_block).strip())  # Save the block
                current_block = []  # Reset for the next block
            else:
                current_block.append(line)  # Add the line to the current block

    return code_blocks


# Function to handle the prompt and code execution
def handle_prompt(prompt):
    # Extract the code block between delimiters
    code_to_execute = extract_code_blocks(prompt)

    if code_to_execute:
        # Ask for confirmation before executing the code
        confirm_execution(code_to_execute)
    else:
        pass
#        print("No code block found between delimiters.")


if __name__ == "__main__":
    # Specify different AI models for each participant (example: 'gpt-3.5-turbo' or 'gpt-4')
    participant1_model = "gpt-4"  # AI Model for Participant 1
    participant2_model = "gpt-4"         # AI Model for Participant 2

    # Start the conversation simulation
    simulate_conversation(participant1_model, participant2_model)

