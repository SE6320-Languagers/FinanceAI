import hashlib
import re
import time
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Callable, Optional
import os
import spacy
from typing import List, Tuple
import neuralcoref
from textblob import TextBlob
from transformers import pipeline
import json
from transformers import BertTokenizer, BertForSequenceClassification
import torch

nlp = spacy.load("en_core_web_sm")
neuralcoref.add_to_pipe(nlp)

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=5)

def get_json_file_path():
    json_file_path = os.path.join(os.path.dirname(__file__), '../../../../../training/dataset/dataset-classification.json')
    json_file_path = os.path.abspath(json_file_path)
    return json_file_path

def get_unique_tokens(text: str) -> Set[str]:
    doc = nlp(text)
    return set([token.pos_ for token in doc])

def calculate_uni_and_bi_grams(text: str) -> Tuple[Dict[str, int], Dict[str, int]]:
    doc = nlp(text)
    tokens = [token.pos_ for token in doc]
    
    unigram = dict()
    bigram = dict()
    prev = ""

    # Count each token
    for token in tokens:
        # If we've already counted add 1
        if (token in unigram):
            unigram[token] += 1
        # Otherwise make a new entry
        else:
            unigram[token] = 1

        # Bigram count
        if (prev != ""):
            # If we've already counted add 1
            if (prev + " " + token in bigram):
                bigram[prev + " " + token] += 1
            # Otherwise make a new entry
            else:
                bigram[prev + " " + token] = 1
        
        # Update the previous token
        prev = token
        
    return unigram, bigram

def calculate_n_gram(text: str, n: int) -> Dict[str, int]:
    doc = nlp(text)
    tokens = [token.pos_ for token in doc]
    
    ngram = dict()
    prev = []

    # Count each token
    for token in tokens:

        # Bigram count
        if (len(prev) == n-1):
            substring = ' '.join(prev) + " " + token
            # If we've already counted add 1
            if (prev + " " + token in bigram):
                bigram[substring] += 1
            # Otherwise make a new entry
            else:
                bigram[substring] = 1

            # Remove oldest token
            prev.pop(0)
        
        # Update the previous token list
        prev.append(token)
        
    return ngram

def tokenize(text: str, remove_punctuation: bool = False) -> List[str]:
    doc = nlp(text)
    if remove_punctuation:
        return [token.text for token in doc if not token.is_punct]
    else:
        return [token.text for token in doc]

def lemmatize(text: str) -> List[str]:
    doc = nlp(text)
    return [token.lemma_ for token in doc if not token.is_stop]

def named_entity_recognition(text: str) -> List[tuple]:
    doc = nlp(text)
    return [(ent.text, ent.label_) for ent in doc.ents]

def resolve_coreferences(text: str) -> str:
    doc = nlp(text)
    return doc._.coref_resolved

def analyze_emotion(text: str) -> str:
    emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
    result = emotion_classifier(text)
    predicted_emotion = result[0]['label']
    
    # we mapped Hugging Face labels to desired emotion categories
    emotion_mapping = {
        "joy": "joy",
        "anger": "fear",      
        "fear": "fear",
        "surprise": "surprise",
        "sadness": "sadness",
        "disgust": "sadness", 
        "neutral": "curious", 
        "anticipation": "curious",
        "fear": "worried",
    }

    return emotion_mapping.get(predicted_emotion, "curious")

def classify_category(text: str) -> str:    
    categories = ["savings", "spending", "achievement", "unexpected_loss", "unexpected_income", "debt", "personal finance"]
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    
    with torch.no_grad():
        logits = model(**inputs).logits
    
    # predicted category = index with highest score
    predicted_class_idx = torch.argmax(logits, dim=1).item()
    predicted_category = categories[predicted_class_idx]
    
    return predicted_category

def retrieve_information(query: str) -> List[Dict]:
    json_file_path = get_json_file_path()
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    retrieved_info = [entry for entry in data if query.lower() in entry.get('phrase', '').lower()]
    return retrieved_info

def process_message_content(message: Dict) -> str:
    json_file_path = get_json_file_path()
    text = message.get('content', '')
    
    tokens = tokenize(text)

    unique_tokens = get_unique_tokens(text)
    
    lemmatized_tokens = lemmatize(text)
    
    named_entities = named_entity_recognition(text)
    
    # Coreference Resolution
    resolved_text = resolve_coreferences(text)
    
    sentiment = analyze_sentiment(text)

    unigram, bigram = calculate_uni_and_bi_grams(text)

    trigram = calculate_n_gram(text, 3)

    # Information Retrieval
    retrieved_info = retrieve_information(resolved_text)
    retrieved_info_str = '\n'.join([f"Advice: {entry['advice']}" for entry in retrieved_info])

    category = classify_category(text)
    # Final user input after processing
    processed_message = f"Resolved Text: {resolved_text}\nSentiment: {sentiment}\nCategory: {category}\nNamed Entities: {named_entities}\n"
    processed_message += f"Retrieved Info:\n{retrieved_info_str}\n"
    
    return processed_message

def get_messages_content(messages: List[Dict]) -> str:
    json_file_path = get_json_file_path()
    messages_content = []
    for message in messages:
        role = message['role'].upper()
        content = process_message_content(message, json_file_path)
        messages_content.append(f"{role}: {content}")
    return "\n".join(messages_content)

def get_last_user_message_item(messages: list[dict]) -> Optional[dict]:
    for message in reversed(messages):
        if message["role"] == "user":
            return message
    return None


def get_content_from_message(message: dict) -> Optional[str]:
    if isinstance(message["content"], list):
        for item in message["content"]:
            if item["type"] == "text":
                return item["text"]
    else:
        return message["content"]
    return None


def get_last_user_message(messages: list[dict]) -> Optional[str]:
    message = get_last_user_message_item(messages)
    if message is None:
        return None
    return get_content_from_message(message)


def get_last_assistant_message(messages: list[dict]) -> Optional[str]:
    for message in reversed(messages):
        if message["role"] == "assistant":
            return get_content_from_message(message)
    return None


def get_system_message(messages: list[dict]) -> Optional[dict]:
    for message in messages:
        if message["role"] == "system":
            return message
    return None


def remove_system_message(messages: list[dict]) -> list[dict]:
    return [message for message in messages if message["role"] != "system"]


def pop_system_message(messages: list[dict]) -> tuple[Optional[dict], list[dict]]:
    return get_system_message(messages), remove_system_message(messages)


def prepend_to_first_user_message_content(
    content: str, messages: list[dict]
) -> list[dict]:
    for message in messages:
        if message["role"] == "user":
            if isinstance(message["content"], list):
                for item in message["content"]:
                    if item["type"] == "text":
                        item["text"] = f"{content}\n{item['text']}"
            else:
                message["content"] = f"{content}\n{message['content']}"
            break
    return messages


def add_or_update_system_message(content: str, messages: list[dict]):
    """
    Adds a new system message at the beginning of the messages list
    or updates the existing system message at the beginning.

    :param msg: The message to be added or appended.
    :param messages: The list of message dictionaries.
    :return: The updated list of message dictionaries.
    """

    if messages and messages[0].get("role") == "system":
        messages[0]["content"] = f"{content}\n{messages[0]['content']}"
    else:
        # Insert at the beginning
        messages.insert(0, {"role": "system", "content": content})

    return messages


def openai_chat_message_template(model: str):
    return {
        "id": f"{model}-{str(uuid.uuid4())}",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "logprobs": None, "finish_reason": None}],
    }


def openai_chat_chunk_message_template(
    model: str, message: Optional[str] = None
) -> dict:
    template = openai_chat_message_template(model)
    template["object"] = "chat.completion.chunk"
    if message:
        template["choices"][0]["delta"] = {"content": message}
    else:
        template["choices"][0]["finish_reason"] = "stop"
    return template


def openai_chat_completion_message_template(
    model: str, message: Optional[str] = None
) -> dict:
    template = openai_chat_message_template(model)
    template["object"] = "chat.completion"
    if message:
        template["choices"][0]["message"] = {"content": message, "role": "assistant"}
    template["choices"][0]["finish_reason"] = "stop"
    return template


def get_gravatar_url(email):
    # Trim leading and trailing whitespace from
    # an email address and force all characters
    # to lower case
    address = str(email).strip().lower()

    # Create a SHA256 hash of the final string
    hash_object = hashlib.sha256(address.encode())
    hash_hex = hash_object.hexdigest()

    # Grab the actual image URL
    return f"https://www.gravatar.com/avatar/{hash_hex}?d=mp"


def calculate_sha256(file):
    sha256 = hashlib.sha256()
    # Read the file in chunks to efficiently handle large files
    for chunk in iter(lambda: file.read(8192), b""):
        sha256.update(chunk)
    return sha256.hexdigest()


def calculate_sha256_string(string):
    # Create a new SHA-256 hash object
    sha256_hash = hashlib.sha256()
    # Update the hash object with the bytes of the input string
    sha256_hash.update(string.encode("utf-8"))
    # Get the hexadecimal representation of the hash
    hashed_string = sha256_hash.hexdigest()
    return hashed_string


def validate_email_format(email: str) -> bool:
    if email.endswith("@localhost"):
        return True

    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def sanitize_filename(file_name):
    # Convert to lowercase
    lower_case_file_name = file_name.lower()

    # Remove special characters using regular expression
    sanitized_file_name = re.sub(r"[^\w\s]", "", lower_case_file_name)

    # Replace spaces with dashes
    final_file_name = re.sub(r"\s+", "-", sanitized_file_name)

    return final_file_name


def extract_folders_after_data_docs(path):
    # Convert the path to a Path object if it's not already
    path = Path(path)

    # Extract parts of the path
    parts = path.parts

    # Find the index of '/data/docs' in the path
    try:
        index_data_docs = parts.index("data") + 1
        index_docs = parts.index("docs", index_data_docs) + 1
    except ValueError:
        return []

    # Exclude the filename and accumulate folder names
    tags = []

    folders = parts[index_docs:-1]
    for idx, _ in enumerate(folders):
        tags.append("/".join(folders[: idx + 1]))

    return tags


def parse_duration(duration: str) -> Optional[timedelta]:
    if duration == "-1" or duration == "0":
        return None

    # Regular expression to find number and unit pairs
    pattern = r"(-?\d+(\.\d+)?)(ms|s|m|h|d|w)"
    matches = re.findall(pattern, duration)

    if not matches:
        raise ValueError("Invalid duration string")

    total_duration = timedelta()

    for number, _, unit in matches:
        number = float(number)
        if unit == "ms":
            total_duration += timedelta(milliseconds=number)
        elif unit == "s":
            total_duration += timedelta(seconds=number)
        elif unit == "m":
            total_duration += timedelta(minutes=number)
        elif unit == "h":
            total_duration += timedelta(hours=number)
        elif unit == "d":
            total_duration += timedelta(days=number)
        elif unit == "w":
            total_duration += timedelta(weeks=number)

    return total_duration


def parse_ollama_modelfile(model_text):
    parameters_meta = {
        "mirostat": int,
        "mirostat_eta": float,
        "mirostat_tau": float,
        "num_ctx": int,
        "repeat_last_n": int,
        "repeat_penalty": float,
        "temperature": float,
        "seed": int,
        "tfs_z": float,
        "num_predict": int,
        "top_k": int,
        "top_p": float,
        "num_keep": int,
        "typical_p": float,
        "presence_penalty": float,
        "frequency_penalty": float,
        "penalize_newline": bool,
        "numa": bool,
        "num_batch": int,
        "num_gpu": int,
        "main_gpu": int,
        "low_vram": bool,
        "f16_kv": bool,
        "vocab_only": bool,
        "use_mmap": bool,
        "use_mlock": bool,
        "num_thread": int,
    }

    data = {"base_model_id": None, "params": {}}

    # Parse base model
    base_model_match = re.search(
        r"^FROM\s+(\w+)", model_text, re.MULTILINE | re.IGNORECASE
    )
    if base_model_match:
        data["base_model_id"] = base_model_match.group(1)

    # Parse template
    template_match = re.search(
        r'TEMPLATE\s+"""(.+?)"""', model_text, re.DOTALL | re.IGNORECASE
    )
    if template_match:
        data["params"] = {"template": template_match.group(1).strip()}

    # Parse stops
    stops = re.findall(r'PARAMETER stop "(.*?)"', model_text, re.IGNORECASE)
    if stops:
        data["params"]["stop"] = stops

    # Parse other parameters from the provided list
    for param, param_type in parameters_meta.items():
        param_match = re.search(rf"PARAMETER {param} (.+)", model_text, re.IGNORECASE)
        if param_match:
            value = param_match.group(1)

            try:
                if param_type is int:
                    value = int(value)
                elif param_type is float:
                    value = float(value)
                elif param_type is bool:
                    value = value.lower() == "true"
            except Exception as e:
                print(e)
                continue

            data["params"][param] = value

    # Parse adapter
    adapter_match = re.search(r"ADAPTER (.+)", model_text, re.IGNORECASE)
    if adapter_match:
        data["params"]["adapter"] = adapter_match.group(1)

    # Parse system description
    system_desc_match = re.search(
        r'SYSTEM\s+"""(.+?)"""', model_text, re.DOTALL | re.IGNORECASE
    )
    system_desc_match_single = re.search(
        r"SYSTEM\s+([^\n]+)", model_text, re.IGNORECASE
    )

    if system_desc_match:
        data["params"]["system"] = system_desc_match.group(1).strip()
    elif system_desc_match_single:
        data["params"]["system"] = system_desc_match_single.group(1).strip()

    # Parse messages
    messages = []
    message_matches = re.findall(r"MESSAGE (\w+) (.+)", model_text, re.IGNORECASE)
    for role, content in message_matches:
        messages.append({"role": role, "content": content})

    if messages:
        data["params"]["messages"] = messages

    return data
