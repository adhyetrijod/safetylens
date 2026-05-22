with open('app.py') as f:
    code = f.read()

# Replace the nav columns block with a radio-based nav
old = '''show_pages = PAGES if st.session_state.loaded else ["Home"]
nav_cols = st.columns(len(show_pages))
for col, p in zip(nav_cols, show_pages):
    with col:
        t = "primary" if st.session_state.page==p else "secondary"
        if st.button(p, key=f"nav_{p}", use_container_width=True, type=t):
            go(p)'''

new = '''show_pages = PAGES if st.session_state.loaded else ["Home"]
# Use radio for clean horizontal nav — no overlap
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"]{display:none}
.stRadio>div{display:flex!important;flex-direction:row!important;gap:0!important;
  border-bottom:2px solid #e2e8f0;flex-wrap:nowrap!important;overflow-x:auto}
.stRadio>div>label{
  padding:.65rem 1rem!important;border-radius:0!important;
  font-size:.82rem!important;font-weight:600!important;
  color:#64748b!important;cursor:pointer;white-space:nowrap!important;
  border-bottom:2px solid transparent!important;margin-bottom:-2px!important;
  background:transparent!important;
}
.stRadio>div>label:has(input:checked){
  color:#1e90ff!important;border-bottom:2px solid #1e90ff!important;
}
.stRadio label span{display:none}
</style>
""", unsafe_allow_html=True)
sel = st.radio("nav", show_pages, index=show_pages.index(st.session_state.page) if st.session_state.page in show_pages else 0,
               horizontal=True, label_visibility="collapsed")
if sel != st.session_state.page:
    go(sel)'''

if old in code:
    code = code.replace(old, new)
    print("Replaced nav with radio")
else:
    # Try partial match
    print("Old not found - checking what's there...")
    idx = code.find("nav_cols = st.columns")
    print(repr(code[idx-200:idx+300]))

with open('app.py', 'w') as f:
    f.write(code)
