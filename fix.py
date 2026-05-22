with open('app.py') as f:
    code = f.read()

# Brighter sidebar text
code = code.replace(
    '[data-testid="stSidebar"] *{color:#b8ccd8!important}',
    '[data-testid="stSidebar"] *{color:#e8f1f8!important}'
)

# Fix metric fill color (webkit override)
code = code.replace(
    'font-weight:800!important}',
    'font-weight:800!important;-webkit-text-fill-color:#0d1b2a!important}',
    1
)

# Uniform buttons - no text wrap
code = code.replace(
    'font-size:.84rem!important}',
    'font-size:.84rem!important;min-height:56px!important;white-space:normal!important;line-height:1.3!important}',
    1
)

with open('app.py', 'w') as f:
    f.write(code)

print("Fixed. Lines:", len(code.splitlines()))
