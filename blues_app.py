import streamlit as st
import streamlit.components.v1 as components
import json
import os
import random
import copy
import re
from music21 import *

# --- CONFIGURACIÓ DE L'APP ---
st.set_page_config(page_title="Generador de Blues", layout="wide")

st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    iframe { background-color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎹 Generador de Lectura de Blues")

if 'xml_data' not in st.session_state:
    st.session_state.xml_data = None

# --- VISUALITZADOR AMB EL "FORCE" DE LÍNIES DE COMPÀS ---
def mostrar_partitura(xml_str):
    xml_escapat = json.dumps(xml_str)
    
    html_code = f"""
    <div style="width: 100%; display: flex; justify-content: center;">
        <div id="osmdCanvas" style="background-color: white; padding: 10px; border-radius: 5px; transform: scale(0.9); transform-origin: top center; width: 111.11%;"></div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
      var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("osmdCanvas", {{
        autoResize: true,
        backend: "svg",
        drawTitle: false,
        drawComposer: false, 
        drawPartNames: false,
        newSystemFromXML: true,
        stretchLastSystemLine: true
      }});
      
      // EL TRUC DEFINITIU: Forçar les regles de gravat de l'OSMD
      osmd.EngravingRules.RenderBarLinesAcrossStaves = true;
      osmd.EngravingRules.SetStaffHeight(65);
      
      osmd.load({xml_escapat}).then(function() {{
        osmd.zoom = 0.9;
        osmd.render();
      }});
    </script>
    """
    components.html(html_code, height=850, scrolling=True)

def generar_blues_inteligent():
    arxiu_motius_nets = 'motius_nets.musicxml'
    if not os.path.exists(arxiu_motius_nets):
        st.error(f"❌ No s'ha trobat '{arxiu_motius_nets}'")
        return None

    partitura_motius = converter.parse(arxiu_motius_nets)
    part_dreta_motius = partitura_motius.getElementsByClass(stream.Part)[0]
    
    motius = []
    motiu_actual = []
    for compas in part_dreta_motius.getElementsByClass(stream.Measure):
        if all(e.isRest for e in compas.notesAndRests) if compas.notesAndRests else True:
            if motiu_actual: motius.append(motiu_actual); motiu_actual = []
        else: motiu_actual.append(compas)
    if motiu_actual: motius.append(motiu_actual)
        
    motius_1 = [m for m in motius if len(m) == 1]
    motius_2 = [m for m in motius if len(m) == 2]

    def te_mi(c):
        return any((n.isNote and n.pitch.name == 'E') or (n.isChord and any(p.name == 'E' for p in n.pitches)) for n in c.flatten().notes)

    m1_segurs = [m for m in motius_1 if not te_mi(m[0])]
    
    partitura = stream.Score()
    md = stream.Part(id='P1'); me = stream.Part(id='P2')

    c_md = [None] * 12
    preg = random.choice(m1_segurs if m1_segurs else motius_1)
    res = random.choice([m for m in motius_1 if m != preg])
    c_md[0] = c_md[4] = preg[0]
    c_md[2] = c_md[6] = res[0]
    
    if motius_2:
        m_ll = random.choice([m for m in motius_2 if not te_mi(m[1])])
        c_md[8], c_md[9] = m_ll[0], m_ll[1]

    for i in range(12):
        if c_md[i] is None:
            c_md[i] = random.choice(m1_segurs if i in [5, 9] else motius_1)[0]
        
        clon = copy.deepcopy(c_md[i])
        clon.number = i + 1
        for el in clon.getElementsByClass(['Clef', 'TimeSignature', 'KeySignature']): clon.remove(el)
        if i in [4, 8]: clon.insert(0, layout.SystemLayout(isNew=True))
        md.append(clon)

    acords = ['C', 'C', 'C', 'C', 'F', 'F', 'C', 'C', 'G', 'F', 'C', 'C']
    for i, ac in enumerate(acords):
        m = stream.Measure(number=i+1)
        p = {'C':['C3 G3','C3 A3'], 'F':['F2 C3','F2 D3'], 'G':['G2 D3','G2 E3']}[ac]
        for _ in range(4): m.append(chord.Chord(p[0].split(), quarterLength=0.5)); m.append(chord.Chord(p[1].split(), quarterLength=0.5))
        if i in [4, 8]: m.insert(0, layout.SystemLayout(isNew=True))
        me.append(m)

    md[0].insert(0, clef.TrebleClef()); md[0].insert(0, key.Key('C')); md[0].insert(0, meter.TimeSignature('4/4'))
    me[0].insert(0, clef.BassClef()); me[0].insert(0, key.Key('C')); me[0].insert(0, meter.TimeSignature('4/4'))
    md[-1].rightBarline = me[-1].rightBarline = bar.Barline('final')

    partitura.insert(0, md); partitura.insert(0, me)
    ton = random.choice(['C', 'G', 'D', 'F'])
    score_f = partitura.transpose({'C':'P1','G':'P-4','D':'M2','F':'P4'}[ton])
    
    # Agrupament per Music21
    grup = layout.StaffGroup(list(score_f.parts), symbol='brace', barTogether='yes')
    score_f.insert(0, grup)
    return score_f

# --- UI ---
c1, c2 = st.columns(2)
with c1:
    if st.button('🔄 Generar Nou Blues', use_container_width=True):
        res = generar_blues_inteligent()
        if res:
            xml_out = res.write('musicxml')
            with open(xml_out, 'r', encoding='utf-8') as f:
                content = f.read()
            # Netegem i forcem el MusicXML manualment per si Music21 s'equivoca
            content = re.sub(r'<part-list>.*?</part-list>', 
                r'<part-list><part-group type="start" number="1"><group-symbol>brace</group-symbol><group-barline>yes</group-barline></part-group><score-part id="P1"><part-name></part-name></score-part><score-part id="P2"><part-name></part-name></score-part><part-group type="stop" number="1"/></part-list>', 
                content, flags=re.DOTALL)
            st.session_state.xml_data = content

with c2:
    if st.session_state.xml_data:
        st.download_button("📥 Descarregar MusicXML", st.session_state.xml_data, "blues.musicxml", use_container_width=True)

if st.session_state.xml_data:
    st.divider()
    mostrar_partitura(st.session_state.xml_data)
