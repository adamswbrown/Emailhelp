import sys
# Patch the get_emails method to add logging
original_file = '/Users/adambrown/Developer/Emailhelp/main_app.py'
with open(original_file, 'r') as f:
    content = f.read()

# Add print statement at start of get_emails
content = content.replace(
    '    def get_emails(self, account: str = None',
    '    def get_emails(self, account: str = None'
)
content = content.replace(
    '        try:\n            if account is None:',
    '        print(f"[API] get_emails called: account={account}, limit={limit}, since_days={since_days}", file=sys.stderr)\n        try:\n            if account is None:'
)

with open('/Users/adambrown/Developer/Emailhelp/main_app_logged.py', 'w') as f:
    f.write(content)
print("Created main_app_logged.py with debug logging")
