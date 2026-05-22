import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as gobj

from src.data_loader import load_demo, load_user_data, INDUSTRY_DEMOS, get_template_csv
from src.risk_engine import score_chemicals, score_parameters, get_deviation_status, compute_plant_risk_index
from src.simulation import run_scenario_simulation, SCENARIOS, generate_drift_series

st.set_page_config(
    page_title="SafetyLens — Process Safety Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar */
[data-testid="stSidebar"]{background:#0f2340!important;min-width:240px!important}
[data-testid="stSidebar"] *{color:#c9d6e3!important}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:#ffffff!important}
[data-testid="stSidebarContent"] .stRadio label{color:#c9d6e3!important;font-size:.88rem!important}
[data-testid="stSidebarContent"] .stSelectbox label{color:#90b4d4!important;font-size:.75rem!important;text-transform:uppercase!important;letter-spacing:.06em!important}

/* Main area */
[data-testid="stAppViewContainer"]{background:#f5f7fa!important}
.block-container{padding:2rem 2.5rem!important;max-width:100%!important}
#MainMenu,footer,header,[data-testid="stToolbar"]{display:none!important}

/* Typography — force dark text everywhere */
h1,h2,h3,h4,h5,h6{color:#0f2340!important;font-weight:700!important}
p,li,span,div{color:#1a2e45!important}
.stMarkdown p{color:#1a2e45!important;font-size:.92rem!important}
label{color:#4b6080!important;font-weight:600!important}
[data-testid="stMetricLabel"]{color:#4b6080!important;font-size:.72rem!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.06em!important}
[data-testid="stMetricValue"]{color:#0f2340!important;font-size:2rem!important;font-weight:800!important}

/* Buttons */
div.stButton>button{border-radius:6px!important;font-weight:600!important;font-size:.84rem!important}
div.stButton>button[kind="primary"]{background:#1e90ff!important;color:#fff!important;border:none!important}
div.stButton>button[kind="secondary"]{background:#f1f5f9!important;color:#0f2340!important;border:1px solid #e2e8f0!important}

/* Cards */
[data-testid="stVerticalBlock"] [data-testid="stVerticalBlock"]{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:.75rem}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{gap:0;border-bottom:2px solid #e2e8f0!important}
.stTabs [data-baseweb="tab"]{background:transparent!important;border:none!important;font-size:.84rem!important;font-weight:600!important;color:#64748b!important;padding:.6rem 1.2rem!important}
.stTabs [aria-selected="true"]{color:#1e90ff!important;border-bottom:2px solid #1e90ff!important}

/* Dataframe */
.stDataFrame{border:1px solid #e2e8f0!important;border-radius:8px!important}

/* Alert boxes keep readable text */
.stAlert p{color:#1a1a1a!important}
</style>
""", unsafe_allow_html=True)

# ── Session ───────────────────────────────────────────────────────
for k,v in {
    "loaded":False,"plant":"","ind":"",
    "chem":pd.DataFrame(),"param":pd.DataFrame(),
    "proc":pd.DataFrame(),"cim":pd.DataFrame(),
    "page":"Home","sim":None,"smeta":None
}.items():
    if k not in st.session_state: st.session_state[k]=v

def nav(p): st.session_state.page=p; st.rerun()

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## SafetyLens")
    st.markdown("<div style='font-size:.75rem;color:#90b4d4;letter-spacing:.08em;text-transform:uppercase;margin-bottom:1rem'>Process Safety Platform</div>", unsafe_allow_html=True)

    if st.session_state.loaded:
        st.markdown(f"<div style='background:rgba(30,144,255,.15);border:1px solid rgba(30,144,255,.4);border-radius:8px;padding:.6rem .9rem;margin-bottom:1rem'>"
                    f"<div style='font-size:.68rem;color:#90b4d4;text-transform:uppercase;letter-spacing:.06em'>Active facility</div>"
                    f"<div style='font-size:.88rem;font-weight:700;color:#fff'>{st.session_state.plant}</div>"
                    f"</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='font-size:.7rem;color:#90b4d4;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.5rem'>Navigation</div>", unsafe_allow_html=True)

    PAGES = ["Home","Dashboard","Chemical Hazards","Process Parameters",
             "Parameter Playground","Simulation","Risk Matrix","PSM Report"]

    for p in PAGES:
        active = st.session_state.page == p
        bg = "rgba(30,144,255,.2)" if active else "transparent"
        border = "1px solid rgba(30,144,255,.5)" if active else "1px solid transparent"
        color = "#ffffff" if active else "#a0b4c8"
        st.markdown(
            f"<div style='background:{bg};border:{border};border-radius:6px;"
            f"padding:.45rem .9rem;margin:.15rem 0;cursor:pointer;font-size:.85rem;"
            f"font-weight:{'700' if active else '500'};color:{color}'>{p}</div>",
            unsafe_allow_html=True
        )
        if st.button(p, key=f"snav_{p}", use_container_width=True,
                     type="primary" if active else "secondary"):
            nav(p)

    st.markdown("---")
    st.markdown("<div style='font-size:.7rem;color:#90b4d4;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.5rem'>Load facility</div>", unsafe_allow_html=True)

    FACILITIES = [
        ("Steel / Tin Plating (ETL-1)", "ETL-1 Tin Plating"),
        ("JSW Steel (Galvanising)",     "JSW Galvanising"),
        ("Nippon Steel (Tin Mill)",     "Nippon Tin Mill"),
        ("Tata Steel (Integrated)",     "Tata Steel"),
        ("Pharmaceuticals",             "API Manufacturing"),
        ("Oil & Gas",                   "Petroleum Refinery"),
        ("Food Processing",             "Food Plant"),
        ("Chlor-Alkali",                "Chlor-Alkali Plant"),
    ]

    sel = st.selectbox("Select industry", [f[1] for f in FACILITIES], label_visibility="collapsed")
    if st.button("Load facility", type="primary", use_container_width=True):
        key = next(f[0] for f in FACILITIES if f[1]==sel)
        d = load_demo(key)
        st.session_state.update({
            "loaded":True,"ind":key,"plant":sel,
            "chem":d["chemicals"],"param":d["parameters"],
            "proc":d["processes"],"cim":d["cim"]
        })
        nav("Dashboard")

    if st.session_state.loaded:
        if st.button("Change facility", use_container_width=True):
            nav("Home")

# ── Helpers ────────────────────────────────────────────────────────
def rc(s): return "#dc2626" if s>=70 else "#f59e0b" if s>=45 else "#16a34a"
def cfg(): return {"displayModeBar":False}
def bl(h=300,**kw):
    base=dict(plot_bgcolor="#ffffff",paper_bgcolor="#ffffff",
        font=dict(size=11,color="#0f2340"),height=h,
        margin=dict(l=0,r=40,t=25,b=0))
    base.update(kw); return base

# ═══════════════════════════════════════════════════════════════════
# HOME
# ═══════════════════════════════════════════════════════════════════
if st.session_state.page == "Home":
    st.title("Process Safety Intelligence Platform")
    st.markdown("Select a facility from the sidebar to begin monitoring. All data is based on real PSI/PSM documentation.")
    st.markdown("---")

    FACILITY_INFO = [
        ("Steel / Tin Plating (ETL-1)", "ETL-1 Tin Plating",     "Steel",     "4 HHO | 6 chemicals | Cr-VI passivation"),
        ("JSW Steel (Galvanising)",     "JSW Galvanising",         "Steel",     "3 HHO | 6 chemicals | Zinc bath explosion"),
        ("Nippon Steel (Tin Mill)",     "Nippon Tin Mill",         "Steel",     "4 HHO | 5 chemicals | HF & Cr-VI"),
        ("Tata Steel (Integrated)",     "Tata Steel Integrated",   "Steel",     "5 HHO | 6 chemicals | CO & HCN critical"),
        ("Pharmaceuticals",             "API Manufacturing",       "Pharma",    "3 HHO | 5 chemicals | Reactor runaway"),
        ("Oil & Gas",                   "Petroleum Refinery",      "Oil & Gas", "5 HHO | 7 chemicals | H2S & BLEVE"),
        ("Food Processing",             "Food Plant",              "Food",      "2 HHO | 4 chemicals | NH3 refrigeration"),
        ("Chlor-Alkali",                "Chlor-Alkali Plant",      "Chemical",  "5 HHO | 6 chemicals | Cl2 toxic release"),
    ]

    for i in range(0, 8, 2):
        c1, c2 = st.columns(2, gap="large")
        for col, (key, name, sector, summary) in zip([c1,c2], FACILITY_INFO[i:i+2]):
            with col:
                with st.container(border=True):
                    st.markdown(f"### {name}")
                    st.markdown(f"**Sector:** {sector}")
                    st.markdown(f"*{summary}*")
                    if st.button(f"Open {name}", key=f"hbtn_{key}", use_container_width=True, type="primary"):
                        d = load_demo(key)
                        st.session_state.update({
                            "loaded":True,"ind":key,"plant":name,
                            "chem":d["chemicals"],"param":d["parameters"],
                            "proc":d["processes"],"cim":d["cim"]
                        })
                        nav("Dashboard")
                st.markdown("")

elif not st.session_state.loaded:
    st.info("Select a facility from the sidebar to begin.")

else:
    C  = score_chemicals(st.session_state.chem.copy())
    P  = score_parameters(st.session_state.param.copy())
    PR = st.session_state.proc.copy()
    CI = st.session_state.cim.copy()
    RK = compute_plant_risk_index(PR, P)

    # ═══════════════════════════════════════════════════════════════
    # DASHBOARD
    # ═══════════════════════════════════════════════════════════════
    if st.session_state.page == "Dashboard":
        st.title(st.session_state.plant)
        st.caption(f"Industry: {st.session_state.ind}")
        hho = len(PR[PR.get("classification",pd.Series()).eq("HHO")]) if "classification" in PR.columns else 0
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Plant Risk Index", f"{int(RK)}/100")
        c2.metric("Processes", len(PR))
        c3.metric("High Hazard (HHO)", hho)
        c4.metric("Chemicals", len(C))
        c5.metric("PSM Parameters", len(P))
        st.markdown("---")

        if not P.empty:
            st.markdown("#### Active risk alerts")
            for _, r in P.nlargest(3,"risk_score").iterrows():
                if r["risk_score"] >= 80:
                    st.error(f"CRITICAL — {r['parameter']} ({r['process']}) | Risk {int(r['risk_score'])}/100 | {r.get('consequence','')}")
                else:
                    st.warning(f"ELEVATED — {r['parameter']} ({r['process']}) | Risk {int(r['risk_score'])}/100")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Process risk ranking")
            if not PR.empty and "risk_score" in PR.columns:
                df=PR.sort_values("risk_score")
                fig=gobj.Figure(gobj.Bar(x=df["risk_score"],y=df["process"],orientation="h",
                    marker_color=[rc(s) for s in df["risk_score"]],
                    text=df["risk_score"].astype(int),textposition="outside"))
                fig.update_layout(**bl(280,xaxis=dict(range=[0,115],title="Risk index",showgrid=True,gridcolor="#f1f5f9"),yaxis=dict(title="")))
                st.plotly_chart(fig,use_container_width=True,config=cfg())
        with col2:
            st.markdown("#### Chemical risk ranking")
            if not C.empty and "risk_score" in C.columns:
                df=C.sort_values("risk_score",ascending=True)
                fig=gobj.Figure(gobj.Bar(x=df["risk_score"],y=df["name"].str[:26],orientation="h",
                    marker_color=[rc(s) for s in df["risk_score"]],
                    text=df["risk_score"].astype(int),textposition="outside"))
                fig.update_layout(**bl(280,xaxis=dict(range=[0,115],title="Risk index",showgrid=True,gridcolor="#f1f5f9"),yaxis=dict(title="")))
                st.plotly_chart(fig,use_container_width=True,config=cfg())

        st.markdown("#### Top 10 highest-risk parameters")
        if not P.empty:
            top=P.nlargest(10,"risk_score")[["process","parameter","uom","soc_min","soc_max","sol_min","sol_max","consequence","risk_score"]]
            top.columns=["Process","Parameter","Unit","SOC Min","SOC Max","SOL Min","SOL Max","Consequence","Risk"]
            st.dataframe(top,use_container_width=True,hide_index=True,height=330)

    # ═══════════════════════════════════════════════════════════════
    # CHEMICAL HAZARDS
    # ═══════════════════════════════════════════════════════════════
    elif st.session_state.page == "Chemical Hazards":
        st.title("Chemical Hazard Analysis")
        t1, t2 = st.tabs(["Hazard Profiles", "Interaction Matrix"])
        with t1:
            if not C.empty:
                sel = st.selectbox("Select chemical", C["name"].tolist())
                row = C[C["name"]==sel].iloc[0]
                rs = int(row.get("risk_score",0))
                a,b,c,d = st.columns(4)
                a.metric("Risk Score", f"{rs}/100")
                b.metric("NFPA Code", row.get("nfpa_code","—"))
                c.metric("TLV-TWA", row.get("tlv_twa","—"))
                d.metric("Flash Point", row.get("flash_point","—"))
                if rs>=80: st.error(f"CRITICAL — {row.get('other_hazards','Review SDS.')}")
                elif rs>=50: st.warning(f"ELEVATED — {row.get('other_hazards','Apply PPE.')}")
                else: st.success(f"LOW RISK — {row.get('other_hazards','Standard handling.')}")
                st.markdown(f"**LD50/LC50:** {row.get('ld50_lc50','—')}  |  **Reactivity:** {row.get('reactivity','—')}")
                st.markdown("---")
                st.markdown("#### Full chemical inventory")
                st.dataframe(C[["name","nfpa_code","tlv_twa","flash_point","ld50_lc50","risk_score"]].rename(
                    columns={"name":"Chemical","nfpa_code":"NFPA","tlv_twa":"TLV-TWA","flash_point":"Flash pt","ld50_lc50":"LD50/LC50","risk_score":"Risk"}),
                    use_container_width=True,hide_index=True)
        with t2:
            if not CI.empty:
                st.info("Y = Reactive pair — segregated storage required  |  N = Non-reactive  |  X = Same substance")
                z=CI.applymap(lambda v:2 if v=="Y" else 0 if v=="N" else 1)
                fig=gobj.Figure(gobj.Heatmap(z=z.values,x=CI.columns.tolist(),y=CI.index.tolist(),
                    colorscale=[[0,"#dcfce7"],[0.5,"#fef3c7"],[1,"#fee2e2"]],
                    text=CI.values,texttemplate="%{text}",showscale=False,xgap=3,ygap=3))
                fig.update_layout(**bl(320))
                st.plotly_chart(fig,use_container_width=True,config=cfg())
            else: st.info("No interaction matrix for this dataset.")

    # ═══════════════════════════════════════════════════════════════
    # PROCESS PARAMETERS
    # ═══════════════════════════════════════════════════════════════
    elif st.session_state.page == "Process Parameters":
        st.title("Process Design Basis")
        st.caption("Standard Operating Conditions and Safe Operating Limits for all PSM-critical parameters")
        if not P.empty:
            f1,f2 = st.columns(2)
            ps=f1.selectbox("Process",["All"]+sorted(P["process"].unique().tolist()))
            rs=f2.selectbox("Risk level",["All","Critical (≥70)","Elevated (40-69)","Low (<40)"])
            df=P.copy()
            if ps!="All": df=df[df["process"]==ps]
            if rs=="Critical (≥70)": df=df[df["risk_score"]>=70]
            elif rs=="Elevated (40-69)": df=df[(df["risk_score"]>=40)&(df["risk_score"]<70)]
            elif rs=="Low (<40)": df=df[df["risk_score"]<40]
            df=df.sort_values("risk_score",ascending=False)
            nc=len(df[df["risk_score"]>=70]); ne=len(df[(df["risk_score"]>=40)&(df["risk_score"]<70)]); nl=len(df[df["risk_score"]<40])
            x1,x2,x3,x4=st.columns(4)
            x1.metric("Showing",len(df)); x2.metric("Critical (≥70)",nc)
            x3.metric("Elevated",ne); x4.metric("Low (<40)",nl)
            st.dataframe(df[["process","parameter","uom","soc_min","soc_max","sol_min","sol_max","consequence","risk_score"]].rename(
                columns={"process":"Process","parameter":"Parameter","uom":"Unit","soc_min":"SOC Min",
                         "soc_max":"SOC Max","sol_min":"SOL Min","sol_max":"SOL Max","consequence":"Consequence","risk_score":"Risk"}),
                use_container_width=True,hide_index=True,height=500)

    # ═══════════════════════════════════════════════════════════════
    # PARAMETER PLAYGROUND
    # ═══════════════════════════════════════════════════════════════
    elif st.session_state.page == "Parameter Playground":
        st.title("Parameter Playground")
        st.caption("Adjust any parameter — observe SOC/SOL status, operating range, and control chart in real time")
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
            if "SOL" in status: st.error(f"SOL BREACH — {status}  |  Consequence: {pr.get('consequence','—')}")
            elif "SOC" in status: st.warning(f"SOC BREACH — {status}")
            else: st.success("NORMAL — within safe operating conditions")
            m1,m2,m3,m4,m5=st.columns(5)
            m1.metric("SOC min",sc); m2.metric("SOC max",sch)
            m3.metric("SOL min",sl); m4.metric("SOL max",sh)
            m5.metric("Current",f"{round(cur,2)} {pr.get('uom','')}")
            st.markdown("---")
            cc,cv=st.columns([1,1.5])
            with cc:
                st.markdown("#### Operating range")
                fig=gobj.Figure()
                fig.add_shape(type="rect",x0=sl,x1=sh,y0=0,y1=1,fillcolor="rgba(254,243,199,.5)",line_width=0,layer="below")
                fig.add_shape(type="rect",x0=sc,x1=sch,y0=0,y1=1,fillcolor="rgba(220,252,231,.7)",line_width=0,layer="below")
                for x,c2,d in [(sl,"#d97706","dash"),(sh,"#d97706","dash"),(sc,"#16a34a","dot"),(sch,"#16a34a","dot")]:
                    fig.add_shape(type="line",x0=x,x1=x,y0=0,y1=1,line=dict(color=c2,width=1.5,dash=d))
                nc2="#dc2626" if "SOL" in status else "#f59e0b" if "SOC" in status else "#1e90ff"
                fig.add_shape(type="line",x0=cur,x1=cur,y0=0,y1=1,line=dict(color=nc2,width=3))
                fig.add_annotation(x=cur,y=1.1,text=f"{round(cur,2)}",showarrow=False,font=dict(size=11,color=nc2,family="monospace"))
                fig.update_layout(plot_bgcolor="#fff",paper_bgcolor="#fff",height=200,
                    margin=dict(l=20,r=20,t=30,b=10),
                    xaxis=dict(range=[round(sl-pad,2),round(sh+pad,2)],title=pr.get("uom","")),
                    yaxis=dict(visible=False,range=[-0.3,1.25]))
                st.plotly_chart(fig,use_container_width=True,config=cfg())
            with cv:
                st.markdown("#### Control chart — 30 readings")
                ser=generate_drift_series(cur,span,steps=30,noise_pct=0.03)
                pc=["#dc2626" if not(sl<=v<=sh) else "#f59e0b" if not(sc<=v<=sch) else "#1e90ff" for v in ser]
                fig2=gobj.Figure()
                fig2.add_hrect(y0=sl,y1=sh,fillcolor="rgba(254,243,199,.35)",line_width=0)
                fig2.add_hrect(y0=sc,y1=sch,fillcolor="rgba(220,252,231,.45)",line_width=0)
                fig2.add_trace(gobj.Scatter(x=list(range(30)),y=ser,mode="lines+markers",
                    line=dict(color="#94a3b8",width=2),marker=dict(color=pc,size=7),showlegend=False))
                for y,lb,c2 in [(sl,"SOL min","#d97706"),(sh,"SOL max","#d97706"),(sc,"SOC min","#16a34a"),(sch,"SOC max","#16a34a")]:
                    fig2.add_hline(y=y,line_dash="dot",line_color=c2,annotation_text=lb,annotation_position="right",annotation_font_size=9)
                fig2.update_layout(plot_bgcolor="#fff",paper_bgcolor="#fff",height=280,
                    margin=dict(l=0,r=70,t=10,b=0),
                    xaxis=dict(title="Reading #",showgrid=True,gridcolor="#f1f5f9"),
                    yaxis=dict(title=pr.get("uom",""),showgrid=True,gridcolor="#f1f5f9"))
                st.plotly_chart(fig2,use_container_width=True,config=cfg())

    # ═══════════════════════════════════════════════════════════════
    # SIMULATION
    # ═══════════════════════════════════════════════════════════════
    elif st.session_state.page == "Simulation":
        st.title("Scenario Simulation")
        st.caption("Model sensor drift, thermal runaway, pressure loss — observe exact breach timing before it occurs")
        if not P.empty:
            c1,c2=st.columns([1,1.8],gap="medium")
            with c1:
                sn=st.selectbox("Scenario type",list(SCENARIOS.keys()))
                sc2=SCENARIOS[sn]
                st.info(sc2["description"])
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
                    result=run_scenario_simulation(sc3,sch2,sl2,sh2,dur,noi/100,dri/100,sc2["direction"])
                    st.session_state.sim=result
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
                    elif soc_b: st.warning(f"SOC breach at step {soc_b}. Corrective action required.")
                    else: st.success("Parameter remained within safe limits throughout simulation.")
                    steps=list(range(len(res)))
                    fig=gobj.Figure()
                    fig.add_hrect(y0=s_sl,y1=s_oh,fillcolor="rgba(254,243,199,.4)",line_width=0)
                    fig.add_hrect(y0=s_sc,y1=s_sh,fillcolor="rgba(220,252,231,.5)",line_width=0)
                    for i in range(len(res)-1):
                        v=res[i]; lc="#dc2626" if not(s_sl<=v<=s_oh) else "#f59e0b" if not(s_sc<=v<=s_sh) else "#1e90ff"
                        fig.add_trace(gobj.Scatter(x=[steps[i],steps[i+1]],y=[res[i],res[i+1]],mode="lines",line=dict(color=lc,width=2.5),showlegend=False))
                    for y,lb,lc in [(s_sl,"SOL min","#d97706"),(s_oh,"SOL max","#d97706"),(s_sc,"SOC min","#16a34a"),(s_sh,"SOC max","#16a34a")]:
                        fig.add_hline(y=y,line_dash="dot",line_color=lc,annotation_text=lb,annotation_position="right",annotation_font_size=9)
                    if sol_b: fig.add_vline(x=sol_b,line_dash="dash",line_color="#dc2626",line_width=2,annotation_text="SOL breach")
                    if soc_b: fig.add_vline(x=soc_b,line_dash="dash",line_color="#f59e0b",line_width=1.5,annotation_text="SOC breach")
                    fig.update_layout(plot_bgcolor="#fff",paper_bgcolor="#fff",title=f"{pm} — {snm}",height=400,
                        margin=dict(l=0,r=85,t=45,b=0),
                        xaxis=dict(title="Time step",showgrid=True,gridcolor="#f1f5f9"),
                        yaxis=dict(title=pu,showgrid=True,gridcolor="#f1f5f9"))
                    st.plotly_chart(fig,use_container_width=True,config=cfg())
                else: st.info("Configure a scenario on the left and click Run simulation.")

    # ═══════════════════════════════════════════════════════════════
    # RISK MATRIX
    # ═══════════════════════════════════════════════════════════════
    elif st.session_state.page == "Risk Matrix":
        st.title("Risk Matrix")
        st.caption("Aggregated risk score per process and hazard type combination")
        st.info("Dark red ≥80: engineering controls required. Orange 50-79: administrative controls. Green <50: standard monitoring.")
        if not PR.empty and not P.empty:
            ht=["Toxic","Corrosive","Flammable","Pressure/Temp","Environmental"]
            pn=PR["process"].tolist()
            mat=np.zeros((len(pn),len(ht)))
            for i,proc in enumerate(pn):
                ps3=P[P["process"]==proc]; b=ps3["risk_score"].mean() if not ps3.empty else 30
                mat[i]=[min(b*.95,100),min(b*.85,100),min(b*.5,100),min(b*.8,100),min(b*.7,100)]
            fig=gobj.Figure(gobj.Heatmap(z=mat,x=ht,y=pn,
                colorscale=[[0,"#dcfce7"],[0.4,"#fef9c3"],[0.7,"#fde68a"],[1,"#dc2626"]],
                text=np.round(mat,0).astype(int),texttemplate="%{text}",
                colorbar=dict(title="Risk"),zmin=0,zmax=100,xgap=3,ygap=3))
            fig.update_layout(plot_bgcolor="#fff",paper_bgcolor="#fff",height=max(320,len(pn)*55),margin=dict(l=0,r=60,t=20,b=0))
            st.plotly_chart(fig,use_container_width=True,config=cfg())

    # ═══════════════════════════════════════════════════════════════
    # PSM REPORT
    # ═══════════════════════════════════════════════════════════════
    elif st.session_state.page == "PSM Report":
        st.title("PSM Risk Report")
        st.caption("Auto-generated process safety management summary and recommended action plan")
        hho=PR[PR.get("classification",pd.Series())=="HHO"] if "classification" in PR.columns else pd.DataFrame()
        cc2=C[C.get("risk_score",pd.Series(0))>=80] if not C.empty else pd.DataFrame()
        col1,col2=st.columns(2)
        with col1:
            st.markdown("#### Executive Summary")
            rk_col="🔴" if RK>=70 else "🟡" if RK>=45 else "🟢"
            st.markdown(f"""
| Field | Value |
|---|---|
| Facility | {st.session_state.plant} |
| Industry | {st.session_state.ind} |
| Processes | {len(PR)} |
| High Hazard (HHO) | {len(hho)} |
| Chemicals | {len(C)} |
| Critical chemicals | {len(cc2)} |
| PSM parameters | {len(P)} |
| **Plant risk index** | **{rk_col} {RK}/100** |
""")
        with col2:
            st.markdown("#### High-priority findings")
            for _,ch in cc2.iterrows():
                st.error(f"CRITICAL CHEMICAL: {ch['name']} — Risk {int(ch.get('risk_score',0))}/100")
            for _,pp in P.nlargest(4,"risk_score").iterrows():
                msg=f"{'CRITICAL' if pp['risk_score']>=70 else 'ELEVATED'}: {pp['parameter']} ({pp['process']}) — Risk {int(pp['risk_score'])}/100 — {pp.get('consequence','')}"
                if pp["risk_score"]>=70: st.error(msg)
                else: st.warning(msg)
        st.markdown("---")
        st.markdown("#### Recommended actions")
        rec=pd.DataFrame({
            "Priority":["P1","P1","P2","P2","P3"],
            "Action":[
                "Continuous air monitoring at highest-risk process",
                "Segregated storage for reactive pairs (CIM)",
                "Inline sensors for top 3 PSM-critical parameters",
                "Auto line-stop interlock on SOL breach",
                "Quarterly PHA review for all HHO processes",
            ],
            "Owner":["EHS Manager","Maintenance","Instrumentation","Automation","Process Engg"],
            "Target":["Immediate","30 days","60 days","60 days","Quarterly"],
        })
        st.dataframe(rec,use_container_width=True,hide_index=True)
        d1,d2=st.columns(2)
        d1.download_button("Export parameters (CSV)",P.to_csv(index=False).encode(),
            f"{st.session_state.plant}_parameters.csv","text/csv",use_container_width=True)
        d2.download_button("Export action plan (CSV)",rec.to_csv(index=False).encode(),
            f"{st.session_state.plant}_action_plan.csv","text/csv",use_container_width=True)
