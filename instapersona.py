import re

from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login
import torch

from setup import HF_READ_TOKEN, MODEL_NAME, TARGET_NAME

# Authenticate with Hugging Face
login(token=HF_READ_TOKEN)

# Load the model and tokenizer
model_name = MODEL_NAME
model = AutoModelForCausalLM.from_pretrained(model_name, token=True)
tokenizer = AutoTokenizer.from_pretrained(model_name, token=True)

alpaca_prompt = '''Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.
### Instructions:
{}

### Input:
{}

### Response:
'''

target_name = TARGET_NAME
INSTRUCTION = "Write a response as {target_name} for the given context (past conversation) in the input. The response must be what {target_name} would potentialy respond to the given context. The input is formatted as the following: <username> (time past since sent): message"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def format_prompts(input):
    return alpaca_prompt.format(INSTRUCTION.format(target_name=target_name), input)

def model_response(input_text):
    # Prepare the input text
    input_text = format_prompts(input_text)

    # Tokenize the input
    inputs = tokenizer(input_text, return_tensors="pt")

    # Load to GPU
    model.to(device)
    inputs = {key: value.to(device) for key, value in inputs.items()}

    # Generate a response
    output = model.generate(**inputs, max_length=4096, num_return_sequences=1)

    # Decode and print the response
    prediction = tokenizer.decode(output[0], skip_special_tokens=True)
    
    # Extract the response from the prediction "### Response:"
    response = re.search(r"### Response:\n(.+)", prediction, re.DOTALL)
    return response.group(1).strip()
    


