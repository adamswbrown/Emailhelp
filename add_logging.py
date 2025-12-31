import sys

with open('/Users/adambrown/Developer/Emailhelp/main_app.py', 'r') as f:
    lines = f.readlines()

# Find and add logging after the get_emails processes messages
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if 'emails = []' in line and i > 90 and i < 100:  # Around line 93
        new_lines.append('            print(f"[API] Processing {len(messages)} messages...", file=sys.stderr)\n')
    elif 'return json.dumps(emails)' in line and 'def get_emails' in ''.join(lines[max(0,i-50):i]):
        new_lines.insert(len(new_lines)-1, f'            print(f"[API] Returning {{len(emails)}} emails", file=sys.stderr)\n')

with open('/Users/adambrown/Developer/Emailhelp/main_app.py', 'w') as f:
    f.writelines(new_lines)
    
print("Added logging to main_app.py")
