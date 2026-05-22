with open('app.py') as f:
    code = f.read()

# Remove gap between nav and content
code = code.replace(
    '.stRadio>div{display:flex!important;flex-direction:row!important;',
    '.stRadio>div{margin-top:-1rem!important;display:flex!important;flex-direction:row!important;'
)

# Remove gap between stacked elements
code = code.replace(
    '.body{padding:0.75rem 2.5rem 4rem}',
    '.body{padding:0.5rem 2.5rem 4rem}'
)

# Kill the gap Streamlit adds between components
old = '.stAlert p{color:#1e2d3d!important}'
new = '.stAlert p{color:#1e2d3d!important}\n[data-testid="stVerticalBlock"]>[data-testid="stVerticalBlock"]{gap:0!important}\n.stRadio{margin-bottom:0!important;margin-top:0!important}'
code = code.replace(old, new)

with open('app.py', 'w') as f:
    f.write(code)

print("Gap fixed")
