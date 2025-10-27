import sys
import os

input_file = ".txt"
output_file = "emails.txt"

if not os.path.exists(input_file):
    print(f"Error: {input_file} not found.")
    sys.exit(1)

emails = set()

with open(input_file, 'r', encoding='latin-1') as f:
    for line in f:
        line = line.strip()
        if ':' in line:
            email = line.split(':')[0].strip()
            if email:  # Ensure email is not empty
                emails.add(email)

with open(output_file, 'w') as f:
    for email in sorted(emails):  # Sort for consistency
        f.write(email + '\n')

print(f"Extracted {len(emails)} unique emails to {output_file}")