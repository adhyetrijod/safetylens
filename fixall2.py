# Fix 1: config.toml — light secondary background so dropdowns are readable
config = """[theme]
base="light"
primaryColor="#1e90ff"
backgroundColor="#f0f4f8"
secondaryBackgroundColor="#e8edf3"
textColor="#0f2340"
font="sans serif"
"""

with open('.streamlit/config.toml', 'w') as f:
    f.write(config)
print("config.toml fixed — dropdowns now readable")

# Fix 2: app.py — remove white gap and make nav background match topbar flow
with open('app.py') as f:
    code = f.read()

# Make nav row background transparent/seamless
code = code.replace(
    '.stRadio>div{margin-top:0!important;display:flex!important;flex-direction:row!important;\n  gap:0!important;background:#fff;flex-wrap:nowrap;overflow-x:auto;\n  border-bottom:2px solid #e2e8f0;margin-bottom:0!important;padding:0 0.5rem}',
    '.stRadio>div{margin-top:0!important;display:flex!important;flex-direction:row!important;\n  gap:0!important;background:#ffffff;flex-wrap:nowrap;overflow-x:auto;\n  border-bottom:2px solid #e2e8f0;margin-bottom:0!important;padding:0 1rem}'
)

# Make nav labels dark and readable
code = code.replace(
    '.stRadio>div label{\n  padding:.65rem .95rem!important;border-radius:0!important;\n  font-size:.82rem!important;font-weight:600!important;\n  color:#64748b!important;cursor:pointer;white-space:nowrap!important;\n  border-bottom:2px solid transparent;margin-bottom:-2px;background:transparent!important}',
    '.stRadio>div label{\n  padding:.65rem .95rem!important;border-radius:0!important;\n  font-size:.82rem!important;font-weight:700!important;\n  color:#1e2d3d!important;cursor:pointer;white-space:nowrap!important;\n  border-bottom:2px solid transparent;margin-bottom:-2px;background:transparent!important}'
)

# Fix selectbox text color
code = code.replace(
    'label{color:#4b6080!important;font-weight:600!important;font-size:.75rem!important;text-transform:uppercase!important;letter-spacing:.06em!important}',
    'label{color:#4b6080!important;font-weight:600!important;font-size:.75rem!important;text-transform:uppercase!important;letter-spacing:.06em!important}\n[data-testid="stSelectbox"] div[data-baseweb="select"] div{color:#0f2340!important;background:#ffffff!important}'
)

with open('app.py', 'w') as f:
    f.write(code)

print("app.py fixed — nav text dark, dropdowns readable")
