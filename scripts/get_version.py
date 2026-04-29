import re

with open('app.py') as f:
    content = f.read()

m = re.search(r"'version':\s*'([^']+)'", content)
print(m.group(1) if m else '0.0.0')
