import requests
import yaml
import json
from pathlib import Path

# Load the YAML file
def load_yaml(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Fetch metrics from Cortex
def fetch_metrics(endpoint: str, headers: dict) -> list:
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching metrics: {e}")
        return []

# Validate metrics
def validate_metrics(defined_metrics: dict, available_metrics: list) -> dict:
    missing_metrics = {}
    for group, metrics in defined_metrics.items():
        missing = [metric for metric in metrics if metric not in available_metrics]
        if missing:
            missing_metrics[group] = missing
    return missing_metrics

# Save missing metrics to JSON file
def save_missing_metrics(missing_metrics: dict, output_file: str) -> None:
    with open(output_file, 'w') as file:
        json.dump(missing_metrics, file, indent=2)

# Main function
def main() -> None:
    yaml_file = 'metrics.yaml'
    output_file = 'missing_metrics.json'
    cortex_endpoint = 'https://<your-cortex-instance>/api/v1/label/__name__/values'
    headers = {
        'Authorization': 'Bearer <your-access-token>',
        'Content-Type': 'application/json'
    }

    # Load defined metrics from YAML
    defined_metrics = load_yaml(yaml_file)['department']

    # Fetch available metrics from Cortex
    available_metrics = fetch_metrics(cortex_endpoint, headers)

    # Validate metrics and find missing ones
    missing_metrics = validate_metrics(defined_metrics, available_metrics)

    # Save missing metrics to JSON file
    save_missing_metrics(missing_metrics, output_file)

    print(f"Missing metrics have been saved to {output_file}")

if __name__ == '__main__':
    main()
