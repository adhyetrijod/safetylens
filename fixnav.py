with open('app.py') as f:
    code = f.read()

# Shrink nav button font and padding so 8 items fit
code = code.replace(
    'white-space:nowrap!important;',
    'white-space:nowrap!important;font-size:0.72rem!important;padding:.6rem 0.45rem!important;letter-spacing:-.01em!important;'
)

# Also rename long page labels
code = code.replace(
    '"Chemical Hazards","Process Parameters","Parameter Playground"',
    '"Chemicals","Parameters","Playground"'
)

with open('app.py', 'w') as f:
    f.write(code)

print("Fixed nav labels and font size")
