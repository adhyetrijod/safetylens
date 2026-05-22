with open('app.py') as f:
    code = f.read()

# Fix 1: applymap -> map (pandas 2.1+)
code = code.replace(
    'z=CI.applymap(lambda v:2 if v=="Y" else 0 if v=="N" else 1)',
    'z=CI.apply(lambda col: col.map(lambda v:2 if v=="Y" else 0 if v=="N" else 1))'
)
print("Fix 1: applymap -> map done")

# Fix 2: slider step must be > 0 and min < max
old_slider = '''            cur=st.slider(f"{pr[\'parameter\']} ({pr.get(\'uom\',\'\')})",
                round(sl-pad,2),round(sh+pad,2),round((sc+sch)/2,2),
                step=round(span/200,3) if span>0 else 0.1)'''

new_slider = '''            _smin = round(sl-pad, 4)
            _smax = round(sh+pad, 4)
            _sdef = round((sc+sch)/2, 4)
            _step = round(span/200, 4) if span>0 else 0.1
            if _step <= 0: _step = 0.001
            if _smax <= _smin: _smax = _smin + 1.0
            _sdef = max(_smin, min(_smax, _sdef))
            cur=st.slider(f"{pr[\'parameter\']} ({pr.get(\'uom\',\'\')})",
                _smin, _smax, _sdef, step=_step)'''

if old_slider in code:
    code = code.replace(old_slider, new_slider)
    print("Fix 2: slider bounds fixed")
else:
    # Fallback fix
    code = code.replace(
        'step=round(span/200,3) if span>0 else 0.1)',
        'step=max(0.001, round(span/200,4)) if span>0 else 0.1)'
    )
    print("Fix 2: slider step fallback applied")

with open('app.py', 'w') as f:
    f.write(code)

print("All cloud errors fixed")
