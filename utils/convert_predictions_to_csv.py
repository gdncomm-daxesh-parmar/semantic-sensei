"""
Convert model_predictions.txt to CSV format
"""

import csv
import re


def parse_predictions_file(input_file, output_file):
    """
    Parse the predictions text file and convert to CSV format.
    
    Format: Term, CategoryCode, Score, CategoryName
    """
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse the data
    results = []
    current_term = None
    current_predictions = []
    current_names = []
    
    lines = content.strip().split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for term
        if line.startswith('- term:'):
            # Save previous term if exists
            if current_term and current_predictions:
                # Match predictions with names
                for idx, pred in enumerate(current_predictions):
                    name = current_names[idx] if idx < len(current_names) else ''
                    results.append({
                        'term': current_term,
                        'category_code': pred['code'],
                        'score': pred['score'],
                        'category_name': name
                    })
            
            # Start new term
            current_term = line.split('term:')[1].strip()
            current_predictions = []
            current_names = []
        
        # Check for predictions
        elif line.startswith('- ') and ':' in line and 'term:' not in line and 'names:' not in line:
            # Parse prediction like "- SE-1000019: 95"
            match = re.match(r'-\s+([A-Z]+-\d+):\s+(\d+)', line)
            if match:
                current_predictions.append({
                    'code': match.group(1),
                    'score': int(match.group(2))
                })
        
        # Check for names
        elif 'names:' in line:
            names_str = line.split('names:')[1].strip()
            current_names = [name.strip() for name in names_str.split(',')]
        
        i += 1
    
    # Save last term
    if current_term and current_predictions:
        for idx, pred in enumerate(current_predictions):
            name = current_names[idx] if idx < len(current_names) else ''
            results.append({
                'term': current_term,
                'category_code': pred['code'],
                'score': pred['score'],
                'category_name': name
            })
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Term', 'CategoryCode', 'Score', 'CategoryName']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in results:
            writer.writerow({
                'Term': row['term'],
                'CategoryCode': row['category_code'],
                'Score': row['score'],
                'CategoryName': row['category_name']
            })
    
    print(f"✓ Converted {len(results)} predictions from {len(set(r['term'] for r in results))} terms")
    print(f"✓ Saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    input_file = "/Users/daxeshparmar/PycharmProjects/semantic-sensei/data/model_predictions.txt"
    output_file = "/Users/daxeshparmar/PycharmProjects/semantic-sensei/data/model_predictions.csv"
    
    parse_predictions_file(input_file, output_file)

