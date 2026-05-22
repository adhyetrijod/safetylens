with open('app.py') as f:
    code = f.read()

# Remove ALL padding/margin from the radio nav container
# so it sits flush against the topbar with no gap

old_radio_css = '''.stRadio>div{margin-top:-1rem!important;display:flex!important;flex-direction:row!important;
  gap:0!important;background:#fff;flex-wrap:nowrap;overflow-x:auto;
  border-bottom:2px solid #e2e8f0;margin-bottom:0!important;padding:0 1.5rem}'''

new_radio_css = '''.stRadio>div{margin-top:0!important;display:flex!important;flex-direction:row!important;
  gap:0!important;background:#fff;flex-wrap:nowrap;overflow-x:auto;
  border-bottom:2px solid #e2e8f0;margin-bottom:0!important;padding:0 0.5rem}'''

if old_radio_css in code:
    code = code.replace(old_radio_css, new_radio_css)
    print("Radio CSS updated")
else:
    # Try partial
    code = code.replace('padding:0 1.5rem}', 'padding:0 0.5rem}')
    print("Partial fix applied")

# Fix body gap
code = code.replace('.body{padding:0.5rem 2.5rem 4rem}', '.body{padding:0.25rem 2.5rem 4rem}')
code = code.replace('.body{padding:0.75rem 2.5rem 4rem}', '.body{padding:0.25rem 2.5rem 4rem}')
code = code.replace('.body{padding:1.75rem 2.5rem 4rem}', '.body{padding:0.25rem 2.5rem 4rem}')

# Fix the nav showing all 8 items — remove left padding cutting off HOME/DASHBOARD
# The radio nav needs overflow-x scroll and padding-left 0
code = code.replace(
    '[data-testid="stVerticalBlock"]>[data-testid="stVerticalBlock"]{gap:0!important}',
    '[data-testid="stVerticalBlock"]>[data-testid="stVerticalBlock"]{gap:0!important;padding:0!important}'
)

with open('app.py', 'w') as f:
    f.write(code)

print("All fixed")
