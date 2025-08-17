import sys
import json
import yaml
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python json2yml.py <json_file>")
        sys.exit(1)
    json_file = sys.argv[1]
    yml_file = os.path.splitext(json_file)[0] + '.yml'
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(yml_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)
    print(f"Converted {json_file} to {yml_file}")

if __name__ == "__main__":
    main()
