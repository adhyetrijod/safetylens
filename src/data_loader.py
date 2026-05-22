"""
Data loader — 8 industry demo datasets including JSW, Nippon, Tata Steel.
"""
import pandas as pd
import numpy as np
import io

INDUSTRY_DEMOS = {
    "Steel / Tin Plating (ETL-1)": {"hho":4,"chems":6,"desc":"Electrolytic tin plating — chromic acid, H₂SO₄, reflow furnace, Cr-VI passivation."},
    "JSW Steel (Galvanising)":     {"hho":3,"chems":6,"desc":"Cold-rolled galvanising — pickling, zinc bath, hydrogen annealing, skin pass."},
    "Nippon Steel (Tin Mill)":     {"hho":4,"chems":5,"desc":"ETP line — Cr-VI treatment, reflow, HF pickling. Highest Cr-VI risk profile."},
    "Tata Steel (Integrated)":     {"hho":5,"chems":6,"desc":"Integrated plant — blast furnace, coke ovens, BOF. CO and HCN critical."},
    "Pharmaceuticals":             {"hho":3,"chems":5,"desc":"API synthesis — reactor runaway, solvent fire, distillation flood."},
    "Oil & Gas":                   {"hho":5,"chems":7,"desc":"Refinery — H₂S, BLEVE, HF alkylation, amine treating."},
    "Food Processing":             {"hho":2,"chems":4,"desc":"Ammonia refrigeration, CIP cleaning, pasteurisation."},
    "Chlor-Alkali":                {"hho":5,"chems":6,"desc":"Cl₂/NaOH plant — chlorine liquefaction, H₂ explosion, Cl₂ toxic release."},
    "Blank":                       {"hho":0,"chems":0,"desc":"Empty workspace — enter your own data."},
}

def load_demo(industry):
    return {
        "Steel / Tin Plating (ETL-1)": _steel_etl,
        "JSW Steel (Galvanising)":     _jsw,
        "Nippon Steel (Tin Mill)":     _nippon,
        "Tata Steel (Integrated)":     _tata,
        "Pharmaceuticals":             _pharma,
        "Oil & Gas":                   _oilgas,
        "Food Processing":             _food,
        "Chlor-Alkali":                _chloralkali,
        "Blank":                       _blank,
    }.get(industry, _blank)()

def load_user_data(cf,pf,plant_name,industry):
    chemicals=pd.read_csv(cf); parameters=pd.read_csv(pf)
    return {"plant_name":plant_name or "My Plant","chemicals":chemicals,
            "parameters":parameters,"processes":_infer_proc(parameters),"cim":_build_cim(chemicals)}

def get_template_csv(kind):
    if kind=="chemicals":
        df=pd.DataFrame(columns=["name","nfpa_code","tlv_twa","tlv_stel","ld50_lc50","flash_point","boiling_point","reactivity","other_hazards","risk_score"])
        df.loc[0]=["Sulphuric Acid","3-0-2(W)","1 mg/m3","3 mg/m3","LD50 2140 mg/kg","N/A","290C","Reacts with water","Corrosive; acid mist",85]
    else:
        df=pd.DataFrame(columns=["process","parameter","uom","soc_min","soc_max","sol_min","sol_max","consequence","psm_critical","risk_score"])
        df.loc[0]=["Cleaning","NaOH Temperature","C",80,90,75,95,"Patch marks / burning","Yes",75]
    return df.to_csv(index=False)

def _infer_proc(p):
    if "process" not in p.columns:
        return pd.DataFrame([{"process":"Default","classification":"LHO","risk_score":50}])
    agg=p.groupby("process")["risk_score"].mean().reset_index()
    agg["classification"]=agg["risk_score"].apply(lambda s:"HHO" if s>=65 else "LHO" if s>=35 else "Safe")
    return agg.rename(columns={"risk_score":"risk_score"})

def _build_cim(c):
    names=c["name"].tolist()[:8]; n=len(names)
    m=[["N"]*n for _ in range(n)]
    for i in range(n): m[i][i]="X"
    if n>=2: m[0][n-1]=m[n-1][0]="Y"
    if n>=3: m[1][n-1]=m[n-1][1]="Y"
    return pd.DataFrame(m,index=names,columns=names)

def _C(*rows): return pd.DataFrame(list(rows))
def _P(*rows): return pd.DataFrame(list(rows))
def _PR(*rows): return pd.DataFrame(list(rows))

def _chem(name,nfpa,tlv,fp,ld,rx,hz,rs):
    return {"name":name,"nfpa_code":nfpa,"tlv_twa":tlv,"flash_point":fp,"ld50_lc50":ld,"reactivity":rx,"other_hazards":hz,"risk_score":rs}

def _param(proc,param,uom,s0,s1,o0,o1,csq,rs):
    return {"process":proc,"parameter":param,"uom":uom,"soc_min":s0,"soc_max":s1,
            "sol_min":o0,"sol_max":o1,"consequence":csq,"psm_critical":"Yes","risk_score":rs}

def _proc(name,cls,rs):
    return {"process":name,"classification":cls,"risk_score":rs}

# ──────────────────────────────────────────────────────────────────
def _steel_etl():
    C=_C(
        _chem("Sulphuric Acid (H₂SO₄)","3-0-2(W)","1 mg/m³","N/A","LD50 2140 mg/kg","Reacts violently with water","Corrosive; acid mist; burns",85),
        _chem("Phenol Sulfonic Acid","3-1-0","N/E",">150°C","LD50 400-800 mg/kg","Reacts with strong bases","Corrosive; skin absorption",72),
        _chem("Dioctyl Sebacate (DOS)","1-1-0","N/E","190°C","LD50 900 mg/kg","Stable","Combustible liquid",30),
        _chem("ENSA Surfactant","2-1-1","N/E","~170°C","Not numeric","Incompatible with acids/alkalis","Eye/skin irritant",45),
        _chem("Sodium Dichromate","4-0-2","0.05 mg/m³","N/A","LD50 50 mg/kg","Strong oxidizer","Carcinogenic Cr-VI; genetic toxicity",95),
        _chem("Chromic Acid","3-0-1","0.05 mg/m³","N/A","Highly toxic","Powerful oxidizer","Carcinogenic; severe burns",92),
    )
    P=_P(
        _param("Cleaning","NaOH Temperature","°C",80,90,80,90,"Patch marks / burning",75),
        _param("Cleaning","Primary Cleaning Current","kA",2.5,3.5,2.5,3.5,"Strip burning / breakage",85),
        _param("Cleaning","H₂SO₄ Concentration","g/L",8,10,8,10,"Surface corrosion",70),
        _param("Tin Plating","Sn++ Concentration","g/L",26,32,24,34,"Improper / over coating",90),
        _param("Tin Plating","Free Acid Concentration","g/L",13,16,11,18,"Dull band / SCO",88),
        _param("Tin Plating","Sn:Acid Ratio","ratio",1.95,2.05,1.90,2.10,"Dull band / surface defect",85),
        _param("Reflow","Strip Exit Temperature","°C",232,270,232,270,"Strip burning / tin melt failure",92),
        _param("Reflow","Quench Temperature","°C",50,65,45,70,"Quench strain / degradation",80),
        _param("Chemical Treatment","Treatment Current","A",300,2000,300,3500,"Insufficient Cr coating",75),
        _param("Chemical Treatment","Cr-VI in air","mg/m³",0,0.03,0,0.05,"Carcinogenic exposure — shutdown",98),
        _param("Oiling","Repelling Plate Voltage","kV",-40,-10,-50,-10,"Excess coating / smudge",50),
    )
    PR=_PR(_proc("Coil Feeding","LHO",15),_proc("Cleaning","HHO",78),_proc("Tin Plating","HHO",82),
           _proc("Reflow","HHO",65),_proc("Chemical Treatment","HHO",60),_proc("Oiling","LHO",30))
    labels=["H₂SO₄","PSA","DOS","ENSA","Na₂Cr₂O₇","CrO₃"]
    m=[["X","N","N","N","Y","Y"],["N","X","N","N","Y","Y"],["N","N","X","N","Y","Y"],
       ["N","N","N","X","Y","Y"],["Y","Y","Y","Y","X","Y"],["Y","Y","Y","Y","Y","X"]]
    cim=pd.DataFrame(m,index=labels,columns=labels)
    return {"plant_name":"ETL-1 Tin Plating Line","chemicals":C,"parameters":P,"processes":PR,"cim":cim}

def _jsw():
    C=_C(
        _chem("Hydrochloric Acid (HCl)","3-0-1","1 ppm","N/A","LC50 3124 ppm/1h","Reacts with metals releasing H₂","Corrosive fumes; severe burns",82),
        _chem("Sulphuric Acid (H₂SO₄)","3-0-2(W)","1 mg/m³","N/A","LD50 2140 mg/kg","Reacts violently with water","Acid mist; burns",85),
        _chem("Zinc (molten)","1-3-2","2 mg/m³","N/A (molten)","LD50 >2000 mg/kg","Reacts with moisture when molten","Metal fume fever; splash burns",78),
        _chem("Aluminium alloy (molten)","1-3-1","1 mg/m³","N/A (molten)","Low acute toxicity","Reacts with moisture explosively","Molten metal explosion hazard",72),
        _chem("Sodium Hydroxide","3-0-1","2 mg/m³","N/A","LD50 500 mg/kg","Exothermic with acids","Severe burns; eye damage",68),
        _chem("Natural Gas","1-4-0","Asphyxiant","N/A (gas)","Asphyxiant","Flammable range 5-15%","Explosion/fire; asphyxiation",80),
    )
    P=_P(
        _param("Pickling","HCl Concentration","g/L",60,120,50,130,"Inadequate descaling / strip corrosion",80),
        _param("Pickling","Bath Temperature","°C",60,80,55,85,"Acid fume / HCl vapour generation",85),
        _param("Pickling","HCl in air","ppm",0,1,0,2,"Toxic inhalation — evacuate",90),
        _param("Galvanising","Zinc bath temperature","°C",440,465,435,475,"Ash / dross / bath explosion risk",88),
        _param("Galvanising","Strip entry temperature","°C",450,470,440,480,"Zinc splash / moisture explosion",92),
        _param("Galvanising","Aluminium content","% wt",0.18,0.22,0.15,0.25,"Poor alloy coating / bare spots",75),
        _param("Annealing","Furnace temperature","°C",720,820,700,850,"Over/under anneal — property failure",78),
        _param("Annealing","H₂ in furnace","% vol",3,20,2,25,"Explosive atmosphere",95),
        _param("Annealing","Dew point","°C",-40,-20,-50,-15,"Oxidation / poor surface",65),
        _param("Skin Pass","Strip tension","kN",50,200,30,250,"Strip breakage / cobble",80),
    )
    PR=_PR(_proc("Pickling","HHO",88),_proc("Galvanising","HHO",90),_proc("Annealing","HHO",82),
           _proc("Skin Pass Mill","LHO",50),_proc("Recoiling","LHO",25))
    return {"plant_name":"JSW Steel — CRCA/Galvanising Line","chemicals":C,"parameters":P,"processes":PR,"cim":_build_cim(C)}

def _nippon():
    C=_C(
        _chem("Chromic Acid (Cr-VI)","3-0-1","0.05 mg/m³","N/A","Highly toxic — carcinogenic","Powerful oxidizer","Carcinogenic; Cr-VI systemic toxicity",97),
        _chem("Tin (SnSO₄ solution)","1-1-0","2 mg/m³","N/A","LD50 >2000 mg/kg","Stable in solution","Mild irritant; acid bath",40),
        _chem("Phosphoric Acid","2-0-0","1 mg/m³","N/A","LD50 1530 mg/kg","Reacts with metals; bases","Corrosive; moderate burns",60),
        _chem("Hydrofluoric Acid (HF)","4-0-1","0.5 ppm","N/A","LC50 1276 ppm/1h","Reacts with glass; metals","Deep penetrating burns; fluoride toxicity",98),
        _chem("Sulphuric Acid (H₂SO₄)","3-0-2","1 mg/m³","N/A","LD50 2140 mg/kg","Reacts with water; metals","Acid burns; mist",85),
    )
    P=_P(
        _param("Tin Plating","Sn++ Concentration","g/L",26,32,24,34,"Improper coating weight",85),
        _param("Tin Plating","Free acid concentration","g/L",13,16,11,18,"Dull band / SCO",82),
        _param("Tin Plating","Bath temperature","°C",35,45,30,50,"Excess plating / burning",78),
        _param("Chromate Treatment","Cr-VI concentration","g/L",8,12,6,15,"Insufficient passivation / over-exposure",95),
        _param("Chromate Treatment","Cr-VI in air","mg/m³",0,0.03,0,0.05,"Carcinogenic exposure — shutdown",98),
        _param("Chromate Treatment","Treatment current","A",300,2000,300,3500,"Insufficient Cr coating",75),
        _param("Reflow","Strip exit temperature","°C",232,270,232,270,"Strip burning / tin melt failure",92),
        _param("Pickling","H₂SO₄ concentration","g/L",8,12,6,15,"Surface corrosion / oxide retention",80),
    )
    PR=_PR(_proc("Tin Plating","HHO",84),_proc("Chromate Treatment","HHO",97),
           _proc("Reflow","HHO",82),_proc("Pickling","HHO",80),_proc("Oiling","LHO",30))
    return {"plant_name":"Nippon Steel — Tin Mill ETP Line","chemicals":C,"parameters":P,"processes":PR,"cim":_build_cim(C)}

def _tata():
    C=_C(
        _chem("Coke Oven Gas","1-4-0","N/A (mixture)","N/A","CO IDLH 1200 ppm","Highly flammable; CO toxic","Explosion; CO poisoning; asphyxiation",95),
        _chem("Carbon Monoxide (CO)","2-4-0","20 ppm","N/A","LC50 1807 ppm/4h","Flammable; CO₂ on combustion","Silent killer; odourless; IDLH 1200 ppm",97),
        _chem("Benzene","3-3-0","0.5 ppm","-11°C","LD50 3306 mg/kg","Highly flammable","Carcinogen; bone marrow toxin",93),
        _chem("Sulphuric Acid","3-0-2","1 mg/m³","N/A","LD50 2140 mg/kg","Reacts with water; metals","Acid burns",82),
        _chem("Ammonia (NH₃)","3-1-0","25 ppm","N/A","LC50 2000 ppm/1h","Flammable 15-28%; reacts with acids","Toxic inhalation; severe eye damage",85),
        _chem("Hydrogen Cyanide (HCN)","4-4-2","4.7 ppm","-17.8°C","LC50 140 ppm/1h","Extremely flammable; explosive","HIGHLY TOXIC — lethal at low concentrations",99),
    )
    P=_P(
        _param("Blast Furnace","CO in cast house","ppm",0,20,0,50,"Toxic exposure — fatality risk",98),
        _param("Blast Furnace","Blast pressure","bar",3,5,2.5,6,"Furnace back-pressure / tuyere damage",88),
        _param("Blast Furnace","Hot metal temperature","°C",1480,1520,1460,1540,"Skull formation / tapping failure",85),
        _param("Coke Ovens","Oven temperature","°C",1150,1250,1100,1300,"Under-coking / green push; fire",82),
        _param("Coke Ovens","Benzene in air","ppm",0,0.5,0,1,"Carcinogenic exposure — shutdown",95),
        _param("Coke Ovens","HCN in by-product plant","ppm",0,2,0,4.7,"Lethal exposure — immediate evacuation",99),
        _param("BOF Steelmaking","Bath temperature","°C",1620,1660,1600,1680,"Slopping / skulling / refractory failure",88),
        _param("BOF Steelmaking","Lance height","mm",1200,1800,1000,2000,"Slopping / lance seizure",75),
        _param("Hot Strip Mill","Coiler temperature","°C",580,650,560,680,"Scale defects / mechanical failure",70),
        _param("Sinter Plant","CO in sinter strand","ppm",0,50,0,100,"Toxic exposure",78),
    )
    PR=_PR(_proc("Blast Furnace","HHO",92),_proc("Coke Ovens","HHO",96),_proc("BOF Steelmaking","HHO",88),
           _proc("Hot Strip Mill","HHO",70),_proc("Sinter Plant","HHO",75),_proc("Lime Kilns","LHO",45))
    return {"plant_name":"Tata Steel — Integrated Steel Plant","chemicals":C,"parameters":P,"processes":PR,"cim":_build_cim(C)}

def _pharma():
    C=_C(
        _chem("Ethanol (96%)","3-0-0","1000 ppm","13°C","LD50 7060 mg/kg","Flammable; incompatible oxidizers","Fire; narcotic",55),
        _chem("Dichloromethane","2-1-0","50 ppm","N/A","LD50 1600 mg/kg","Reacts with alkalis","Suspected carcinogen; CNS",72),
        _chem("Sodium Hydroxide","3-0-1","2 mg/m³","N/A","LD50 500 mg/kg","Exothermic with acids","Severe burns",68),
        _chem("Acetonitrile","3-3-0","40 ppm","2°C","LD50 2730 mg/kg","Flammable; oxidizers","CNS depressant; metabolises to HCN",70),
        _chem("Ammonia (anhydrous)","3-1-0","25 ppm","N/A","LC50 2000 ppm/1h","Flammable; reacts with acids","Toxic inhalation",80),
    )
    P=_P(
        _param("Reactor","Reaction Temperature","°C",20,35,10,50,"Runaway reaction",90),
        _param("Reactor","Reactor Pressure","bar",1,3,0.5,5,"Vessel failure / explosion",95),
        _param("Reactor","Stirrer Speed","RPM",200,400,100,500,"Poor mixing / hot spots",60),
        _param("Distillation","Column Top Temperature","°C",78,85,70,95,"Product contamination",65),
        _param("Distillation","Reboiler Temperature","°C",100,120,95,130,"Flooding / product loss",70),
        _param("CIP","NaOH Concentration","% w/v",1.5,2.5,1.0,3.0,"Inadequate cleaning",55),
    )
    PR=_PR(_proc("Reactor","HHO",90),_proc("Distillation","HHO",68),_proc("CIP","LHO",55),_proc("Filtration","LHO",30))
    return {"plant_name":"API Manufacturing Unit","chemicals":C,"parameters":P,"processes":PR,"cim":_build_cim(C)}

def _oilgas():
    C=_C(
        _chem("Hydrogen Sulphide (H₂S)","4-0-0","1 ppm","N/A","LC50 444 ppm/1h","Flammable; toxic","IDLH 100 ppm; silent killer",98),
        _chem("Crude Oil","2-3-0","—","<-18°C","Variable","Flammable","Hydrocarbon vapour; fire",70),
        _chem("LPG (Propane/Butane)","1-4-0","1000 ppm","N/A","Asphyxiant","Highly flammable; BLEVE risk","BLEVE; cold burn",88),
        _chem("Sulphuric Acid (Alkylation)","3-0-2","1 mg/m³","N/A","LD50 2140 mg/kg","Reacts with water","Corrosive; burns",82),
        _chem("DEA (Amine)","2-1-0","2 ppm","169°C","LD50 2000 mg/kg","Incompatible with acids","Skin sensitiser; corrosive",60),
        _chem("Hydrofluoric Acid (HF)","4-0-1","0.5 ppm","N/A","LC50 1276 ppm/1h","Reacts with metals; glass","Penetrating burns; systemic toxicity",97),
        _chem("Caustic Soda","3-0-1","2 mg/m³","N/A","LD50 500 mg/kg","Exothermic with acids","Corrosive burns",68),
    )
    P=_P(
        _param("Distillation","Column pressure","bar",1.5,2.5,1.0,3.5,"Flooding / column damage",88),
        _param("Distillation","Furnace outlet temp","°C",340,380,320,400,"Coking / tube rupture",90),
        _param("H₂S Stripping","H₂S in off-gas","ppm",0,50,0,100,"Toxic release — life-safety event",98),
        _param("LPG Storage","Vessel pressure","bar",8,16,6,20,"BLEVE risk",95),
        _param("Amine Treating","DEA concentration","% w/w",25,35,20,40,"H₂S breakthrough / corrosion",72),
    )
    PR=_PR(_proc("Crude Distillation","HHO",88),_proc("H₂S Stripping","HHO",98),
           _proc("LPG Storage","HHO",95),_proc("Amine Treating","HHO",72),
           _proc("Crude Transfer","HHO",65),_proc("Water Treatment","LHO",30))
    return {"plant_name":"Petroleum Refinery Unit","chemicals":C,"parameters":P,"processes":PR,"cim":_build_cim(C)}

def _food():
    C=_C(
        _chem("Ammonia (Refrigerant)","3-1-0","25 ppm","N/A","LC50 2000 ppm/1h","Reacts with acids; flammable","Toxic; suffocating; fire",82),
        _chem("Caustic Soda (CIP)","3-0-1","2 mg/m³","N/A","LD50 500 mg/kg","Exothermic with acids","Corrosive burns",60),
        _chem("Nitric Acid (CIP)","3-0-1","2 ppm","N/A","LD50 430 mg/kg","Strong oxidizer","Corrosive; fumes",72),
        _chem("Chlorine (Sanitation)","4-0-0","0.5 ppm","N/A","LC50 293 ppm/1h","Reacts with organic matter","Toxic gas; respiratory damage",85),
    )
    P=_P(
        _param("NH₃ Refrigeration","Suction pressure","bar",-0.3,1.5,-0.5,2.5,"Compressor damage / NH₃ release",85),
        _param("NH₃ Refrigeration","Discharge pressure","bar",10,14,8,16,"Vessel overpressure / rupture",90),
        _param("NH₃ Refrigeration","NH₃ in air","ppm",0,25,0,50,"Toxic exposure — evacuate",92),
        _param("CIP","Caustic temperature","°C",70,80,60,85,"Inadequate cleaning / burns",60),
        _param("Pasteurisation","Pasteurisation temp","°C",72,75,70,80,"Microbial risk / product recall",80),
    )
    PR=_PR(_proc("NH₃ Refrigeration","HHO",90),_proc("Pasteurisation","HHO",80),
           _proc("CIP","LHO",58),_proc("Packaging","LHO",20))
    return {"plant_name":"Food Processing Plant","chemicals":C,"parameters":P,"processes":PR,"cim":_build_cim(C)}

def _chloralkali():
    C=_C(
        _chem("Chlorine (Cl₂)","4-0-0","0.5 ppm","N/A","LC50 293 ppm/1h","Strong oxidizer","Toxic; IDLH 10 ppm; corrosive",97),
        _chem("Caustic Soda (50%)","3-0-1","2 mg/m³","N/A","LD50 500 mg/kg","Exothermic with acids","Severe burns",70),
        _chem("Hydrogen (H₂)","0-4-0","Asphyxiant","N/A","Asphyxiant","Flammable range 4-75%; BLEVE","Explosive; BLEVE risk",90),
        _chem("Hydrochloric Acid","3-0-1","1 ppm","N/A","LC50 3124 ppm/1h","Reacts with metals","Corrosive; toxic fumes",80),
        _chem("Brine (NaCl)","0-0-0","—","N/A","LD50 3000 mg/kg","Stable","Mild irritant",15),
        _chem("Sodium Hypochlorite","3-0-1","1 ppm","N/A","LD50 8910 mg/kg","Reacts with acids releasing Cl₂","Oxidizer; corrosive",72),
    )
    P=_P(
        _param("Electrolysis","Cell voltage","V",3.0,4.0,2.5,4.5,"Current inefficiency / membrane damage",75),
        _param("Electrolysis","Brine concentration","g/L",290,310,280,320,"Membrane damage / Cl₂ purity drop",80),
        _param("Cl₂ Liquefaction","Liquefaction temperature","°C",-35,-20,-40,-15,"Cl₂ vapour release",95),
        _param("Cl₂ Liquefaction","Cl₂ in area air","ppm",0,0.5,0,1,"Toxic exposure — evacuate",98),
        _param("H₂ Handling","H₂ in air","% LEL",0,10,0,25,"Explosion risk",92),
        _param("Caustic Evaporation","Steam pressure","bar",3,6,2,8,"Overconcentration / scaling",65),
    )
    PR=_PR(_proc("Electrolysis","HHO",80),_proc("Cl₂ Liquefaction","HHO",97),
           _proc("H₂ Handling","HHO",92),_proc("Caustic Evaporation","HHO",65),
           _proc("Brine Preparation","LHO",20),_proc("Cl₂ Compression","HHO",75))
    return {"plant_name":"Chlor-Alkali Plant","chemicals":C,"parameters":P,"processes":PR,"cim":_build_cim(C)}

def _blank():
    return {"plant_name":"My Plant",
        "chemicals":pd.DataFrame(columns=["name","nfpa_code","tlv_twa","flash_point","ld50_lc50","reactivity","other_hazards","risk_score"]),
        "parameters":pd.DataFrame(columns=["process","parameter","uom","soc_min","soc_max","sol_min","sol_max","consequence","psm_critical","risk_score"]),
        "processes":pd.DataFrame(columns=["process","classification","risk_score"]),
        "cim":pd.DataFrame()}
