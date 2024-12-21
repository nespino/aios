#!/bin/python3

import openai
import random

# Set up your OpenAI API key here
openai.api_key = "YOUR_API_KEY"

# Function to simulate an AI model response
def ai_response(model, prompt):
    response = openai.Completion.create(
        engine=model,
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()

# Simulate the interaction between the two participants
def simulate_conversation(participant1_model, participant2_model, turn_limit=5):
    print("Conversation Start:")
    turn_count = 0
    last_response = ""

    while turn_count < turn_limit:
        # Human decides whether to respond or let the AI respond
        choice = input("\nDo you want to control the conversation? (y/n): ").strip().lower()

        if choice == "y":
            # Human input
            human_input = input("Your message: ")
            print(f"You (Human): {human_input}")
            last_response = human_input

        else:
            # AI-controlled turn
            if turn_count % 2 == 0:  # Participant 1's turn (AI 1)
                prompt = f"Participant 1 asks: {last_response}\nParticipant 2 responds:"
                response = ai_response(participant1_model, prompt)
                print(f"Participant 1 (AI): {response}")
                last_response = response

            else:  # Participant 2's turn (AI 2)
                prompt = f"Participant 2 asks: {last_response}\nParticipant 1 responds:"
                response = ai_response(participant2_model, prompt)
                print(f"Participant 2 (AI): {response}")
                last_response = response

        turn_count += 1

    print("\nConversation Ended.")

if __name__ == "__main__":
    # Specify different AI models for each participant (example: 'gpt-3.5-turbo' or 'gpt-4')
    participant1_model = "gpt-3.5-turbo"  # AI Model for Participant 1
    participant2_model = "gpt-4"         # AI Model for Participant 2

    # Start the conversation simulation
    simulate_conversation(participant1_model, participant2_model)
