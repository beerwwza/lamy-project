import re
import sys

with open(r'd:\lamy\lamy-project\myapp\templates\myapp\equipment_data.html', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to parse all if and endif tags precisely from the token list.
from django.template.base import Lexer

lexer = Lexer(text)
tokens = lexer.tokenize()

stack = []
for t in tokens:
    if t.token_type.name == 'BLOCK':
        content = t.contents.strip()
        parts = content.split()
        if not parts: continue
        tag = parts[0]
        if tag == 'if':
            stack.append(t.lineno)
        elif tag == 'endif':
            if stack:
                stack.pop()
            else:
                print(f"Extra endif at line {t.lineno}")

if stack:
    print(f"Unclosed if at lines: {stack}")
else:
    print("All balanced")
