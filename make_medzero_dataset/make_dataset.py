#!/usr/bin/env python3
import os
import json
import argparse
import pandas as pd
from datasets import Dataset


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Convert Rare Arena dataset to conversation format")
    parser.add_argument("--input_json", required=True, help="Path to rare arena JSON file")
    parser.add_argument("--output_dir", required=True, help="Output directory for processed datasets")
    return parser.parse_args()


def load_json_data(filepath):
    """Load JSONL formatted data"""
    with open(filepath, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def create_reward_model(row):
    """Construct reward model data structure"""
    return {
        "ground_truth": {
            "diagnosis": list({row["diagnosis"], row["Orpha_name"]}),  # Use set for deduplication
            "orpha_id": row["Orpha_id"]
        }
    }


def generate_case_text(row):
    """Generate medical case text, combining case report and test results (if available)"""
    base_text = row["case_report"]
    return f"{base_text} {row.get('test_results', '')}".strip()


def create_conversation_prompt(example, idx, split_type):
    """Create conversation-formatted prompt"""

    prompt_template = """You are a medical assistant designed to assist users in providing medical diagnoses. When the user shares a case report, your task is to analyze the information, reason through the details, and deliver an accurate diagnosis.
Based on the following case report, provide a diagnosis. Explain your reasoning process in the <think> </think> tags, and return the final diagnosis in the <answer> </answer> tags. For example, <answer> Migraine </answer>.
The case report is: {case_text}."""
    
    return {
        "prompt": [{
            "role": "user",
            "content": prompt_template.format(case_text=example["case_text"])
        }],
        "extra_info": {
            "split": split_type,
            "index": idx
        }
    }


def process_raw_data(raw_data):
    """Process raw data and return DataFrame"""
    df = pd.DataFrame(raw_data)
    
    # Add processed columns
    df["reward_model"] = df.apply(create_reward_model, axis=1)
    df["case_text"] = df.apply(generate_case_text, axis=1)
    df["ability"] = "medical"
    df["data_source"] = "rare_arena"
    
    return df[["_id", "case_text", "reward_model", "ability", "data_source"]]


def split_dataset(dataset, train_ratio=0.7):
    """Split dataset into training and test sets"""
    split_index = int(len(dataset) * train_ratio)
    return dataset.select(range(split_index)), dataset.select(range(split_index, len(dataset)))


def save_dataset(dataset, output_dir, filename):
    """Save dataset to specified directory"""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    dataset.to_parquet(filepath)
    return filepath


def main():
    args = parse_args()
    
    # Data loading and processing
    raw_data = load_json_data(args.input_json)
    processed_df = process_raw_data(raw_data)
    full_dataset = Dataset.from_pandas(processed_df)
    
    # Dataset splitting
    train_set, test_set = split_dataset(full_dataset)
    
    # Format conversion
    train_conversation = train_set.map(
        lambda ex, idx: create_conversation_prompt(ex, idx, "train"),
        with_indices=True
    )
    test_conversation = test_set.map(
        lambda ex, idx: create_conversation_prompt(ex, idx, "test"),
        with_indices=True
    )
    
    json_name = os.path.basename(args.input_json).split(".")[0]
    
    # Save results
    train_path = save_dataset(train_conversation, args.output_dir, f"train_{json_name}_conversation.parquet")
    test_path = save_dataset(test_conversation, args.output_dir, f"test_{json_name}_conversation.parquet")
    
    print(f"Processing complete!\nTraining set: {train_path}\nTest set: {test_path}")


if __name__ == "__main__":
    main()