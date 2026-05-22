"""
SafetyLens — Dark topbar + horizontal nav, like image reference.
Clean horizontal navigation. Full drill-down plant hierarchy.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as gobj

from src.data_loader import load_demo, get_template_csv, load_user_data
from src.risk_engine import score_chemicals, score_parameters, get_deviation_status, compute_plant_risk_index
from src.simulation import run_scenario_simulation, SCENARIOS, generate_drift_series

st.set_page_config(page_title="SafetyLens", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* hide all default chrome */
#MainMenu,footer,header,[data-testid="stToolbar"],
[data-testid="collapsedControl"],[data-testid="stSidebar"]{display:none!important}
.block-container{padding:0!important;max-width:100%!important}
section[data-testid="stMain"]>div{padding:0!important}
[data-testid="stAppViewContainer"]{background:#f0f4f8!important}

/* ── TOP BAR ── */
.tb{
  background:#0f2340;height:54px;display:flex;align-items:center;
  justify-content:space-between;padding:0 2rem;
  border-bottom:2px solid #1e90ff;
  box-shadow:0 2px 8px rgba(0,0,0,.25);
}
.tb-brand{font-size:1.1rem;font-weight:800;color:#fff;letter-spacing:.04em}
.tb-brand span{color:#1e90ff}
.tb-sub{font-size:.68rem;color:#7a9ab8;margin-left:10px;
  text-transform:uppercase;letter-spacing:.09em}
.tb-pill{
  background:rgba(30,144,255,.18);border:1px solid rgba(30,144,255,.45);
  color:#60b4ff;font-size:.72rem;padding:5px 16px;border-radius:20px;font-weight:600;
}

/* ── NAV ROW ── */
.navrow{
  background:#ffffff;border-bottom:1px solid #e2e8f0;
  padding:0 1.5rem;display:flex;gap:0;
  box-shadow:0 1px 4px rgba(0,0,0,.06);
}

/* override streamlit button inside navrow */
[data-testid="stHorizontalBlock"] div.stButton>button{
  border-radius:0!important;border:none!important;
  background:transparent!important;
  color:#64748b!important;font-weight:600!important;
  font-size:.82rem!important;padding:.75rem 1.1rem!important;
  border-bottom:2px solid transparent!important;
  white-space:nowrap!important;
  transition:all .15s!important;
}
[data-testid="stHorizontalBlock"] div.stButton>button:hover{
  color:#0f2340!important;background:rgba(30,144,255,.06)!important;
}
[data-testid="stHorizontalBlock"] div.stButton>button[kind="primary"]{
  color:#1e90ff!important;border-bottom:2px solid #1e90ff!important;
  background:rgba(30,144,255,.07)!important;
}

/* ── MAIN BODY ── */
.body{padding:1.75rem 2.5rem 4rem}

/* ── KPI CARDS ── */
[data-testid="stMetricLabel"]{
  color:#4b6080!important;font-size:.68rem!important;
  font-weight:700!important;text-transform:uppercase!important;
  letter-spacing:.07em!important;
}
[data-testid="stMetricValue"]{
  color:#0f2340!important;font-size:1.85rem!important;
  font-weight:800!important;
}

/* ── CONTENT BUTTONS ── */
.body div.stButton>button{
  border-radius:7px!important;font-weight:600!important;
  font-size:.85rem!important;min-height:46px!important;
}
.body div.stButton>button[kind="primary"]{
  background:#1e90ff!important;color:#fff!important;border:none!important;
}
.body div.stButton>button[kind="secondary"]{
  background:#fff!important;color:#1e2d3d!important;
  border:1px solid #d1dce6!important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"]{border-bottom:2px solid #e2e8f0!important;gap:0}
.stTabs [data-baseweb="tab"]{background:transparent!important;border:none!important;
  color:#64748b!important;font-weight:600!important;font-size:.83rem!important;padding:.6rem 1.2rem!important}
.stTabs [aria-selected="true"]{color:#1e90ff!important;border-bottom:2px solid #1e90ff!important}

/* ── ALERTS ── */
.stAlert p{color:#1e2d3d!important;font-size:.84rem!important}

/* ── HEADINGS ── */
h1,h2,h3{color:#0f2340!important;font-weight:700!important}
.stMarkdown p{color:#1e2d3d!important;font-size:.88rem!important}
label{color:#4b6080!important;font-weight:600!important;font-size:.75rem!important;
  text-transform:uppercase!important;letter-spacing:.06em!important}
</style>
""", unsafe_allow_html=True)

# ── Hierarchy ─────────────────────────────────────────────────────
HIERARCHY = {
    "Steel & Metal": {
        "Tata Steel — Jamshedpur Works": {
            "Iron Making": {
                "Coke Plant": "Tata Steel (Integrated)",
                "By Product Plant": "Tata Steel (Integrated)",
                "Haldia Met Coke Plant": "Tata Steel (Integrated)",
                "Sinter Plant #1": "Tata Steel (Integrated)",
                "Sinter Plant #2": "Tata Steel (Integrated)",
                "Sinter Plant #3": "Tata Steel (Integrated)",
                "Sinter Plant #4": "Tata Steel (Integrated)",
                "Raw Material Bedding & Blending": "Tata Steel (Integrated)",
                "Pellet Plant": "Tata Steel (Integrated)",
                "A-F Blast Furnace": "Tata Steel (Integrated)",
                "G Blast Furnace": "Tata Steel (Integrated)",
                "H Blast Furnace": "Tata Steel (Integrated)",
                "I Blast Furnace": "Tata Steel (Integrated)",
            },
            "Long Products": {
                "LD#1 & Continuous Caster": "Tata Steel (Integrated)",
                "Lime Plant": "Tata Steel (Integrated)",
                "New Bar Mill": "Tata Steel (Integrated)",
                "Wire and Rod Mill": "Tata Steel (Integrated)",
                "Merchant Mill": "Tata Steel (Integrated)",
            },
            "Flat Products": {
                "LD#2 & Slab Caster": "Tata Steel (Integrated)",
                "Hot Strip Mill": "Tata Steel (Integrated)",
                "LD#3 TSCR": "Tata Steel (Integrated)",
                "Cold Rolling Mill": "Steel / Tin Plating (ETL-1)",
                "Tubes Division": "Tata Steel (Integrated)",
            },
        },
        "Tata Steel — Tinplate (TCIL), Golmuri": {
            "Tinplate Operations": {
                "ETL-1 — Electrolytic Tinning Line 1": "Steel / Tin Plating (ETL-1)",
                "ETL-2 — Electrolytic Tinning Line 2": "Steel / Tin Plating (ETL-1)",
                "CRM — Cold Rolling Mill": "Steel / Tin Plating (ETL-1)",
                "Printing & Lacquering Lines": "Steel / Tin Plating (ETL-1)",
                "Continuous Annealing Line (CAL)": "Steel / Tin Plating (ETL-1)",
            },
        },
        "Tata Steel — Kalinganagar": {
            "Kalinganagar Plant": {
                "Raw Material Handling": "Tata Steel (Integrated)",
                "Coke Plant": "Tata Steel (Integrated)",
                "Sinter Plant": "Tata Steel (Integrated)",
                "Blast Furnace": "Tata Steel (Integrated)",
                "Steel Melting Shop (BOF)": "Tata Steel (Integrated)",
                "Hot Strip Mill": "Tata Steel (Integrated)",
            },
        },
        "Tata Steel — Meramandali": {
            "Meramandali Plant": {
                "Inbound Logistics": "Tata Steel (Integrated)",
                "Coke Oven": "Tata Steel (Integrated)",
                "Sinter Plant": "Tata Steel (Integrated)",
                "Direct Reduced Iron (DRI)": "Tata Steel (Integrated)",
                "Blast Furnace-1": "Tata Steel (Integrated)",
                "Blast Furnace-2": "Tata Steel (Integrated)",
                "Steel Melting Shop-2": "Tata Steel (Integrated)",
                "Hot Strip Mill": "Tata Steel (Integrated)",
                "Cold Rolling Mill": "Steel / Tin Plating (ETL-1)",
            },
        },
        "JSW Steel — Vijayanagar": {
            "Vijayanagar Works": {
                "Blast Furnace Complex (BF1-BF5)": "Tata Steel (Integrated)",
                "BOF Steelmaking": "Tata Steel (Integrated)",
                "Hot Strip Mill": "Tata Steel (Integrated)",
                "Cold Rolling Mill": "Steel / Tin Plating (ETL-1)",
                "Hot-Dip Galvanising Lines": "JSW Steel (Galvanising)",
                "Colour Coating Line": "JSW Steel (Galvanising)",
            },
        },
        "JSW Steel — Dolvi": {
            "Dolvi Works": {
                "Blast Furnace & BOS": "Tata Steel (Integrated)",
                "Hot Strip Mill": "Tata Steel (Integrated)",
                "Galvanising & CRCA": "JSW Steel (Galvanising)",
            },
        },
        "AM/NS India — Hazira": {
            "Hazira Works": {
                "Blast Furnace (BF1 & BF2)": "Tata Steel (Integrated)",
                "BOF & Slab Caster": "Tata Steel (Integrated)",
                "Hot Strip Mill": "Tata Steel (Integrated)",
                "Cold Rolling Complex": "Steel / Tin Plating (ETL-1)",
                "Galvanising & Colour Coat": "JSW Steel (Galvanising)",
                "ETP / Tin Mill": "Nippon Steel (Tin Mill)",
            },
        },
        "SAIL — Rourkela": {
            "Rourkela Plant": {
                "Blast Furnace": "Tata Steel (Integrated)",
                "BOF & Plate Mill": "Tata Steel (Integrated)",
                "Tinplate Plant": "Steel / Tin Plating (ETL-1)",
            },
        },
    },
    "Pharma": {
        "API Manufacturing": {"Units": {
            "Reactor Block — API Synthesis": "Pharmaceuticals",
            "Solvent Recovery Unit": "Pharmaceuticals",
        }},
    },
    "Oil & Gas": {
        "Petroleum Refinery": {"Units": {
            "Crude Distillation Unit (CDU)": "Oil & Gas",
            "H2S Stripping & Amine Unit": "Oil & Gas",
            "LPG Storage & Dispatch": "Oil & Gas",
        }},
    },
    "Food & Beverage": {
        "Food Processing Plant": {"Units": {
            "Ammonia Refrigeration System": "Food Processing",
            "Pasteurisation & UHT Unit": "Food Processing",
        }},
    },
    "Chemicals": {
        "Chlor-Alkali Plant": {"Units": {
            "Chlorine Liquefaction Plant": "Chlor-Alkali",
            "Hydrogen Handling": "Chlor-Alkali",
            "Caustic Evaporation Unit": "Chlor-Alkali",
        }},
    },
}

PAGES = ["Home","Dashboard","Chemical Hazards","Process Parameters",
         "Parameter Playground","Simulation","Risk Matrix","PSM Report"]

for k,v in {
    "sec":None,"comp":None,"area":None,"div":None,"dkey":None,
    "loaded":False,"pdisplay":"","sec_display":"",
    "chem":pd.DataFrame(),"param":pd.DataFrame(),
    "proc":pd.DataFrame(),"cim":pd.DataFrame(),
    "page":"Home","sim":None,"smeta":None,
}.items():
    if k not in st.session_state: st.session_state[k]=v

def go(p): st.session_state.page=p; st.rerun()
def rst():
    for k in ["sec","comp","area","div","dkey","loaded","pdisplay","sec_display",
              "sim","smeta"]:
        st.session_state[k]=None if k not in ["loaded"] else False
    for k in ["chem","param","proc","cim"]:
        st.session_state[k]=pd.DataFrame()
    st.session_state.page="Home"
    st.rerun()

def rc(s): return "#dc2626" if s>=70 else "#f59e0b" if s>=45 else "#16a34a"
def cfg(): return {"displayModeBar":False}
def bl(**kw):
    b=dict(plot_bgcolor="#fff",paper_bgcolor="#fff",
           font=dict(size=11,color="#0f2340"),margin=dict(l=0,r=40,t=25,b=0))
    b.update(kw); return b

# ── TOP BAR ───────────────────────────────────────────────────────
pill = st.session_state.pdisplay if st.session_state.loaded else "No facility selected"
st.markdown(f"""
<div class="tb">
  <div style="display:flex;align-items:center">
    <span class="tb-brand">Safety<span>Lens</span></span>
    <span class="tb-sub">Process Safety Platform</span>
  </div>
  <span class="tb-pill">{pill}</span>
</div>
""", unsafe_allow_html=True)

# ── NAV ROW ───────────────────────────────────────────────────────
show_pages = PAGES if st.session_state.loaded else ["Home"]
nav_cols = st.columns(len(show_pages))
for col, p in zip(nav_cols, show_pages):
    with col:
        t = "primary" if st.session_state.page==p else "secondary"
        if st.button(p, key=f"nav_{p}", use_container_width=True, type=t):
            go(p)

st.markdown('<div class="body">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# HOME — drill-down plant selector
# ═══════════════════════════════════════════════════════════════════
if st.session_state.page == "Home":
    st.title("Process Safety Intelligence")
    st.caption("Tata Steel · JSW Steel · AM/NS India · SAIL — Real PSI/PSM plant hierarchy")
    st.divider()

    # Step 1 — Sector
    st.markdown("#### Step 1 — Industry sector")
    sc = st.columns(len(HIERARCHY))
    for col,(s,_) in zip(sc,HIERARCHY.items()):
        with col:
            active = st.session_state.sec==s
            if st.button(s, key=f"s_{s}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.update({"sec":s,"comp":None,"area":None,"div":None})
                st.rerun()

    if st.session_state.sec:
        st.divider()
        comps = list(HIERARCHY[st.session_state.sec].keys())
        st.markdown(f"#### Step 2 — Company  ·  *{st.session_state.sec}*")
        cc = st.columns(min(len(comps),3))
        for col,c in zip(cc,comps):
            with col:
                if st.button(c, key=f"c_{c}", use_container_width=True,
                             type="primary" if st.session_state.comp==c else "secondary"):
                    st.session_state.update({"comp":c,"area":None,"div":None})
                    st.rerun()

    if st.session_state.comp:
        st.divider()
        areas = list(HIERARCHY[st.session_state.sec][st.session_state.comp].keys())
        st.markdown(f"#### Step 3 — Area  ·  *{st.session_state.comp}*")
        ac = st.columns(min(len(areas),4))
        for col,a in zip(ac,areas):
            with col:
                if st.button(a, key=f"a_{a}", use_container_width=True,
                             type="primary" if st.session_state.area==a else "secondary"):
                    st.session_state.update({"area":a,"div":None})
                    st.rerun()

    if st.session_state.area:
        st.divider()
        divs = HIERARCHY[st.session_state.sec][st.session_state.comp][st.session_state.area]
        st.markdown(f"#### Step 4 — Division / process line  ·  *{st.session_state.area}*")
        dc = st.columns(min(len(divs),3))
        for col,(d,dk) in zip(dc,divs.items()):
            with col:
                if st.button(d, key=f"d_{d}", use_container_width=True,
                             type="primary" if st.session_state.div==d else "secondary"):
                    st.session_state.update({"div":d,"dkey":dk})
                    st.rerun()

    if st.session_state.div:
        st.divider()
        disp = f"{st.session_state.comp}  ›  {st.session_state.div}"
        st.success(f"**Selected:** {disp}")
        if st.button("Open facility dashboard →", type="primary"):
            d = load_demo(st.session_state.dkey)
            st.session_state.update({
                "loaded":True, "pdisplay":st.session_state.div,
                "sec_display":st.session_state.sec,
                "chem":d["chemicals"],"param":d["parameters"],
                "proc":d["processes"],"cim":d["cim"],"page":"Dashboard"
            })
            st.rerun()

    st.divider()
    with st.expander("Upload your own PSI data"):
        u1,u2,u3 = st.columns([2,1,1])
        with u1:
            pn=st.text_input("Plant name"); ind=st.text_input("Industry")
        with u2:
            st.download_button("Chemicals template",get_template_csv("chemicals"),"chem.csv",use_container_width=True)
            cf=st.file_uploader("Chemicals CSV",type="csv",label_visibility="collapsed")
        with u3:
            st.download_button("Parameters template",get_template_csv("parameters"),"param.csv",use_container_width=True)
            pf=st.file_uploader("Parameters CSV",type="csv",label_visibility="collapsed")
        if st.button("Load custom plant",type="primary"):
            if cf and pf:
                d=load_user_data(cf,pf,pn,ind)
                st.session_state.update({"loaded":True,"pdisplay":pn or "Custom Plant",
                    "chem":d["chemicals"],"param":d["parameters"],"proc":d["processes"],
                    "cim":d["cim"],"page":"Dashboard"})
                st.rerun()
            else: st.error("Upload both CSV files.")

elif not st.session_state.loaded:
    st.info("Go to Home and select a facility to begin.")
    if st.button("Go to Home", type="primary"): go("Home")

else:
    # ── data ────────────────────────────────────────────────────────
    C  = score_chemicals(st.session_state.chem.copy())
    P  = score_parameters(st.session_state.param.copy())
    PR = st.session_state.proc.copy()
    CI = st.session_state.cim.copy()
    RK = compute_plant_risk_index(PR,P)

    # ── DASHBOARD ──────────────────────────────────────────────────
    if st.session_state.page=="Dashboard":
        st.title(st.session_state.pdisplay)
        parts=[x for x in [st.session_state.sec,st.session_state.comp,st.session_state.div] if x]
        if parts: st.caption("  ›  ".join(parts))
        hho=len(PR[PR.get("classification",pd.Series()).eq("HHO")]) if "classification" in PR.columns else 0
        c1,c2,c3,c4,c5=st.columns(5)
        c1.metric("Risk Index",f"{int(RK)}/100")
        c2.metric("Processes",len(PR))
        c3.metric("High Hazard",hho)
        c4.metric("Chemicals",len(C))
        c5.metric("Parameters",len(P))
        st.divider()
        if not P.empty:
            st.markdown("#### Active risk alerts")
            for _,r in P.nlargest(3,"risk_score").iterrows():
                if r["risk_score"]>=80: st.error(f"CRITICAL — {r['parameter']} ({r['process']}) | Risk {int(r['risk_score'])}/100 | {r.get('consequence','')}")
                else: st.warning(f"ELEVATED — {r['parameter']} ({r['process']}) | Risk {int(r['risk_score'])}/100")
        st.divider()
        cl,cr=st.columns(2)
        with cl:
            st.markdown("**Process risk ranking**")
            if not PR.empty and "risk_score" in PR.columns:
                df=PR.sort_values("risk_score")
                fig=gobj.Figure(gobj.Bar(x=df["risk_score"],y=df["process"],orientation="h",
                    marker_color=[rc(s) for s in df["risk_score"]],
                    text=df["risk_score"].astype(int),textposition="outside"))
                fig.update_layout(**bl(height=280,
                    xaxis=dict(range=[0,115],showgrid=True,gridcolor="#f1f5f9",zeroline=False),
                    yaxis=dict(title="")))
                st.plotly_chart(fig,use_container_width=True,config=cfg())
        with cr:
            st.markdown("**Chemical risk ranking**")
            if not C.empty and "risk_score" in C.columns:
                df=C.sort_values("risk_score",ascending=True)
                fig=gobj.Figure(gobj.Bar(x=df["risk_score"],y=df["name"].str[:24],orientation="h",
                    marker_color=[rc(s) for s in df["risk_score"]],
                    text=df["risk_score"].astype(int),textposition="outside"))
                fig.update_layout(**bl(height=280,
                    xaxis=dict(range=[0,115],showgrid=True,gridcolor="#f1f5f9",zeroline=False),
                    yaxis=dict(title="")))
                st.plotly_chart(fig,use_container_width=True,config=cfg())
        st.divider()
        st.markdown("**Top 10 highest-risk parameters**")
        if not P.empty:
            top=P.nlargest(10,"risk_score")[["process","parameter","uom","soc_min","soc_max","sol_min","sol_max","consequence","risk_score"]]
            top.columns=["Process","Parameter","Unit","SOC Min","SOC Max","SOL Min","SOL Max","Consequence","Risk"]
            st.dataframe(top,use_container_width=True,hide_index=True,height=330)
        if st.button("Change facility",use_container_width=False): rst()

    # ── CHEMICAL HAZARDS ───────────────────────────────────────────
    elif st.session_state.page=="Chemical Hazards":
        st.title("Chemical Hazard Analysis")
        t1,t2=st.tabs(["Hazard Profiles","Interaction Matrix"])
        with t1:
            if not C.empty:
                sel=st.selectbox("Select chemical",C["name"].tolist())
                row=C[C["name"]==sel].iloc[0]; rs=int(row.get("risk_score",0))
                a,b,c,d=st.columns(4)
                a.metric("Risk Score",f"{rs}/100"); b.metric("NFPA",row.get("nfpa_code","—"))
                c.metric("TLV-TWA",row.get("tlv_twa","—")); d.metric("Flash pt",row.get("flash_point","—"))
                if rs>=80: st.error(f"CRITICAL — {row.get('other_hazards','Review SDS.')}")
                elif rs>=50: st.warning(f"ELEVATED — {row.get('other_hazards','Apply PPE.')}")
                else: st.success(f"LOW RISK — {row.get('other_hazards','Standard handling.')}")
                st.markdown(f"**LD50/LC50:** {row.get('ld50_lc50','—')}  |  **Reactivity:** {row.get('reactivity','—')}")
                st.divider()
                st.dataframe(C[["name","nfpa_code","tlv_twa","flash_point","ld50_lc50","risk_score"]].rename(
                    columns={"name":"Chemical","nfpa_code":"NFPA","tlv_twa":"TLV-TWA",
                             "flash_point":"Flash pt","ld50_lc50":"LD50/LC50","risk_score":"Risk"}),
                    use_container_width=True,hide_index=True)
        with t2:
            if not CI.empty:
                st.info("Y = Reactive pair — segregated storage required  |  N = Non-reactive  |  X = Same substance")
                z=CI.applymap(lambda v:2 if v=="Y" else 0 if v=="N" else 1)
                fig=gobj.Figure(gobj.Heatmap(z=z.values,x=CI.columns.tolist(),y=CI.index.tolist(),
                    colorscale=[[0,"#dcfce7"],[0.5,"#fef3c7"],[1,"#fee2e2"]],
                    text=CI.values,texttemplate="%{text}",showscale=False,xgap=3,ygap=3))
                fig.update_layout(**bl(height=320))
                st.plotly_chart(fig,use_container_width=True,config=cfg())

    # ── PROCESS PARAMETERS ─────────────────────────────────────────
    elif st.session_state.page=="Process Parameters":
        st.title("Process Design Basis")
        st.caption("Standard Operating Conditions and Safe Operating Limits — all PSM-critical parameters")
        if not P.empty:
            f1,f2=st.columns(2)
            ps=f1.selectbox("Process",["All"]+sorted(P["process"].unique().tolist()))
            rs=f2.selectbox("Risk level",["All","Critical (≥70)","Elevated (40-69)","Low (<40)"])
            df=P.copy()
            if ps!="All": df=df[df["process"]==ps]
            if rs=="Critical (≥70)": df=df[df["risk_score"]>=70]
            elif rs=="Elevated (40-69)": df=df[(df["risk_score"]>=40)&(df["risk_score"]<70)]
            elif rs=="Low (<40)": df=df[df["risk_score"]<40]
            df=df.sort_values("risk_score",ascending=False)
            x1,x2,x3,x4=st.columns(4)
            x1.metric("Showing",len(df)); x2.metric("Critical (≥70)",len(df[df["risk_score"]>=70]))
            x3.metric("Elevated",len(df[(df["risk_score"]>=40)&(df["risk_score"]<70)]))
            x4.metric("Low (<40)",len(df[df["risk_score"]<40]))
            st.dataframe(df[["process","parameter","uom","soc_min","soc_max","sol_min","sol_max","consequence","risk_score"]].rename(
                columns={"process":"Process","parameter":"Parameter","uom":"Unit","soc_min":"SOC Min",
                         "soc_max":"SOC Max","sol_min":"SOL Min","sol_max":"SOL Max",
                         "consequence":"Consequence","risk_score":"Risk"}),
                use_container_width=True,hide_index=True,height=500)

    # ── PARAMETER PLAYGROUND ───────────────────────────────────────
    elif st.session_state.page=="Parameter Playground":
        st.title("Parameter Playground")
        st.caption("Adjust any parameter — SOC/SOL status and control chart update live")
        if not P.empty:
            s1,s2=st.columns(2)
            sp=s1.selectbox("Process",sorted(P["process"].unique().tolist()))
            pm=s2.selectbox("Parameter",P[P["process"]==sp]["parameter"].tolist())
            pr=P[(P["process"]==sp)&(P["parameter"]==pm)].iloc[0]
            sl=float(pr.get("sol_min",0)); sh=float(pr.get("sol_max",100))
            sc=float(pr.get("soc_min",0)); sch=float(pr.get("soc_max",100))
            span=sh-sl if sh>sl else 100; pad=span*.15
            cur=st.slider(f"{pr['parameter']} ({pr.get('uom','')})",
                round(sl-pad,2),round(sh+pad,2),round((sc+sch)/2,2),
                step=round(span/200,3) if span>0 else 0.1)
            status,_=get_deviation_status(cur,(sc,sch),(sl,sh))
            if "SOL" in status: st.error(f"SOL BREACH — {status} | {pr.get('consequence','')}")
            elif "SOC" in status: st.warning(f"SOC BREACH — {status}")
            else: st.success("NORMAL — within safe operating conditions")
            m1,m2,m3,m4,m5=st.columns(5)
            m1.metric("SOC min",sc); m2.metric("SOC max",sch)
            m3.metric("SOL min",sl); m4.metric("SOL max",sh)
            m5.metric("Current",f"{round(cur,2)} {pr.get('uom','')}")
            st.divider()
            ser=generate_drift_series(cur,span,steps=30,noise_pct=0.03)
            pc=["#dc2626" if not(sl<=v<=sh) else "#f59e0b" if not(sc<=v<=sch) else "#1e90ff" for v in ser]
            fig=gobj.Figure()
            fig.add_hrect(y0=sl,y1=sh,fillcolor="rgba(254,243,199,0.35)",line_width=0)
            fig.add_hrect(y0=sc,y1=sch,fillcolor="rgba(220,252,231,0.45)",line_width=0)
            fig.add_trace(gobj.Scatter(x=list(range(30)),y=ser,mode="lines+markers",
                line=dict(color="#94a3b8",width=2),marker=dict(color=pc,size=7),showlegend=False))
            for y,lb,c2 in [(sl,"SOL min","#d97706"),(sh,"SOL max","#d97706"),(sc,"SOC min","#16a34a"),(sch,"SOC max","#16a34a")]:
                fig.add_hline(y=y,line_dash="dot",line_color=c2,annotation_text=lb,annotation_position="right",annotation_font_size=9)
            fig.update_layout(**bl(height=300,
                xaxis=dict(title="Reading #",showgrid=True,gridcolor="#f1f5f9"),
                yaxis=dict(title=pr.get("uom",""),showgrid=True,gridcolor="#f1f5f9")))
            st.markdown("**Statistical process control chart — 30 readings**")
            st.plotly_chart(fig,use_container_width=True,config=cfg())

    # ── SIMULATION ─────────────────────────────────────────────────
    elif st.session_state.page=="Simulation":
        st.title("Scenario Simulation")
        st.caption("Model sensor drift, thermal runaway, pressure loss — observe exact breach timing")
        if not P.empty:
            c1,c2=st.columns([1,1.8],gap="medium")
            with c1:
                sn=st.selectbox("Scenario type",list(SCENARIOS.keys()))
                sc2=SCENARIOS[sn]; st.info(sc2["description"])
                sp2=st.selectbox("Process",sorted(P["process"].unique().tolist()))
                spm=st.selectbox("Parameter",P[P["process"]==sp2]["parameter"].tolist())
                pr2=P[(P["process"]==sp2)&(P["parameter"]==spm)].iloc[0]
                sl2=float(pr2.get("sol_min",0)); sh2=float(pr2.get("sol_max",100))
                sc3=float(pr2.get("soc_min",0)); sch2=float(pr2.get("soc_max",100))
                dur=st.slider("Duration (steps)",20,150,60)
                noi=st.slider("Noise level (%)",0,25,5)
                dri=st.slider("Drift rate (%/step)",0.0,5.0,float(sc2["default_drift"]),step=0.1)
                run=st.button("Run simulation",type="primary",use_container_width=True)
            with c2:
                if run:
                    res=run_scenario_simulation(sc3,sch2,sl2,sh2,dur,noi/100,dri/100,sc2["direction"])
                    st.session_state.sim=res
                    st.session_state.smeta=(spm,pr2.get("uom",""),sc3,sch2,sl2,sh2,pr2.get("consequence",""),sn)
                if st.session_state.sim:
                    res=st.session_state.sim
                    pm,pu,s_sc,s_sh,s_sl,s_oh,csq,snm=st.session_state.smeta
                    sol_b=next((i for i,v in enumerate(res) if not(s_sl<=v<=s_oh)),None)
                    soc_b=next((i for i,v in enumerate(res) if not(s_sc<=v<=s_sh)),None)
                    a,b,c,d=st.columns(4)
                    a.metric("Final value",f"{round(res[-1],2)} {pu}")
                    b.metric("SOC breach",f"Step {soc_b}" if soc_b else "None")
                    c.metric("SOL breach",f"Step {sol_b}" if sol_b else "None")
                    d.metric("Steps",len(res))
                    if sol_b: st.error(f"SOL BREACH at step {sol_b}: {csq}")
                    elif soc_b: st.warning(f"SOC breach at step {soc_b}. Take corrective action.")
                    else: st.success("Parameter within safe limits throughout simulation.")
                    steps=list(range(len(res)))
                    fig=gobj.Figure()
                    fig.add_hrect(y0=s_sl,y1=s_oh,fillcolor="rgba(254,243,199,0.4)",line_width=0)
                    fig.add_hrect(y0=s_sc,y1=s_sh,fillcolor="rgba(220,252,231,0.5)",line_width=0)
                    for i in range(len(res)-1):
                        v=res[i]; lc="#dc2626" if not(s_sl<=v<=s_oh) else "#f59e0b" if not(s_sc<=v<=s_sh) else "#1e90ff"
                        fig.add_trace(gobj.Scatter(x=[steps[i],steps[i+1]],y=[res[i],res[i+1]],
                            mode="lines",line=dict(color=lc,width=2.5),showlegend=False))
                    for y,lb,lc in [(s_sl,"SOL min","#d97706"),(s_oh,"SOL max","#d97706"),(s_sc,"SOC min","#16a34a"),(s_sh,"SOC max","#16a34a")]:
                        fig.add_hline(y=y,line_dash="dot",line_color=lc,annotation_text=lb,annotation_position="right",annotation_font_size=9)
                    if sol_b: fig.add_vline(x=sol_b,line_dash="dash",line_color="#dc2626",line_width=2,annotation_text="SOL breach")
                    if soc_b: fig.add_vline(x=soc_b,line_dash="dash",line_color="#f59e0b",line_width=1.5,annotation_text="SOC breach")
                    fig.update_layout(**bl(height=380,title=f"{pm} — {snm}",
                        margin=dict(l=0,r=85,t=45,b=0),
                        xaxis=dict(title="Time step",showgrid=True,gridcolor="#f1f5f9"),
                        yaxis=dict(title=pu,showgrid=True,gridcolor="#f1f5f9")))
                    st.plotly_chart(fig,use_container_width=True,config=cfg())
                else:
                    st.info("Configure a scenario on the left and click Run simulation.")

    # ── RISK MATRIX ────────────────────────────────────────────────
    elif st.session_state.page=="Risk Matrix":
        st.title("Risk Matrix")
        st.info("Dark red ≥80: engineering controls required. Orange 50-79: admin controls. Green <50: standard monitoring.")
        if not PR.empty and not P.empty:
            ht=["Toxic","Corrosive","Flammable","Pressure/Temp","Environmental"]
            pn=PR["process"].tolist(); mat=np.zeros((len(pn),len(ht)))
            for i,proc in enumerate(pn):
                ps3=P[P["process"]==proc]; b=ps3["risk_score"].mean() if not ps3.empty else 30
                mat[i]=[min(b*0.95,100),min(b*0.85,100),min(b*0.5,100),min(b*0.8,100),min(b*0.7,100)]
            fig=gobj.Figure(gobj.Heatmap(z=mat,x=ht,y=pn,
                colorscale=[[0,"#dcfce7"],[0.4,"#fef9c3"],[0.7,"#fde68a"],[1,"#dc2626"]],
                text=np.round(mat,0).astype(int),texttemplate="%{text}",
                colorbar=dict(title="Risk"),zmin=0,zmax=100,xgap=3,ygap=3))
            fig.update_layout(**bl(height=max(320,len(pn)*55),margin=dict(l=0,r=60,t=20,b=0)))
            st.plotly_chart(fig,use_container_width=True,config=cfg())

    # ── PSM REPORT ─────────────────────────────────────────────────
    elif st.session_state.page=="PSM Report":
        st.title("PSM Risk Report")
        hho=PR[PR.get("classification",pd.Series())=="HHO"] if "classification" in PR.columns else pd.DataFrame()
        cc2=C[C.get("risk_score",pd.Series(0))>=80] if not C.empty else pd.DataFrame()
        col1,col2=st.columns(2)
        with col1:
            st.markdown("**Executive Summary**")
            rk_col="🔴" if RK>=70 else "🟡" if RK>=45 else "🟢"
            st.markdown(f"""
| Field | Value |
|---|---|
| Facility | {st.session_state.pdisplay} |
| Processes | {len(PR)} |
| HHO | {len(hho)} |
| Chemicals | {len(C)} |
| Critical chemicals | {len(cc2)} |
| Parameters | {len(P)} |
| **Risk index** | **{rk_col} {RK}/100** |
""")
        with col2:
            st.markdown("**High-priority findings**")
            for _,ch in cc2.iterrows():
                st.error(f"CRITICAL: {ch['name']} — Risk {int(ch.get('risk_score',0))}/100")
            for _,pp in P.nlargest(4,"risk_score").iterrows():
                msg=f"{'CRITICAL' if pp['risk_score']>=70 else 'ELEVATED'}: {pp['parameter']} ({pp['process']}) — Risk {int(pp['risk_score'])}/100"
                if pp["risk_score"]>=70: st.error(msg)
                else: st.warning(msg)
        st.divider()
        rec=pd.DataFrame({
            "Priority":["P1","P1","P2","P2","P3"],
            "Action":["Continuous air monitoring at highest-risk process",
                      "Segregated storage for CIM reactive pairs",
                      "Inline sensors for top 3 PSM parameters",
                      "Auto line-stop interlock on SOL breach",
                      "Quarterly PHA for all HHO processes"],
            "Owner":["EHS","Maintenance","Instrumentation","Automation","Process Engg"],
            "Target":["Immediate","30 days","60 days","60 days","Quarterly"],
        })
        st.dataframe(rec,use_container_width=True,hide_index=True)
        d1,d2=st.columns(2)
        d1.download_button("Export parameters",P.to_csv(index=False).encode(),"parameters.csv","text/csv",use_container_width=True)
        d2.download_button("Export action plan",rec.to_csv(index=False).encode(),"actions.csv","text/csv",use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
