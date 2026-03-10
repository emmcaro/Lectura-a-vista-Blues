import streamlit as st
import streamlit.components.v1 as components
import json
import os
import random
import copy
from music21 import *

# --- CONFIGURACIÓ DE L'APP ---
st.set_page_config(page_title="Generador de Blues", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-left: 1.5rem; padding-right: 1.5rem; }
    iframe { background-color: white; border: 1px solid #ddd; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎹 Generador de Lectura de Blues")

# Inicialitzem la sessió sempre com a string
if 'xml_data' not in st.session_state:
    st.session_state.xml_data = ""

def mostrar_partitura(xml_str):
    if not xml_str:
        return
    
    xml_escapat = json.dumps(xml_str)
    
    html_code = f"""
    <div id="osmdCanvas" style="width: 100%; background-color: white;"></div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
      var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("osmdCanvas", {{
        autoResize: true,
        backend: "svg",
        drawTitle: false,
        drawPartNames: false,
        newSystemFromXML: true,
        stretchLastSystemLine: true
      }});
      
      // CONFIGURACIÓ PER CONNECTAR LES BARRES DE COMPÀS
      osmd.EngravingRules.RenderBarLinesAcrossStaves = true;
      osmd.EngravingRules.StavesConnectorsSpacingAcrossStaves = true;
      osmd.EngravingRules.ManageReversedGroupBracketSystemLines = true;

      osmd.load({xml_escapat}).then(function() {{
        osmd.zoom = 0.9;
        osmd.render();
      }}).catch(function(err) {{
        document.getElementById("osmdCanvas").innerHTML = "<p style='color:red;'>Error carregant partitura: " + err + "</p>";
      }});
    </script>
    """
    components.html(html_code, height=900, scrolling=True)

def generar_blues():
    arxiu = 'motius_nets.musicxml'
    if not os.path.exists(arxiu):
        st.error(f"No trobo l'arxiu {arxiu}")
        return ""

    # Carregar i processar motius
    score_motius = converter.parse(arxiu)
    motius_raw = []
    temp = []
    for c in score_motius.parts[0].getElementsByClass(stream.Measure):
        if all(e.isRest for e in c.notesAndRests) if c.notesAndRests else True:
            if temp: motius_raw.append(temp); temp = []
        else: temp.append(c)
    if temp: motius_raw.append(temp)

    m1 = [m for m in motius_raw if len(m) == 1]
    m2 = [m for m in motius_raw if len(m) == 2]

    # Construcció de la partitura
    s = stream.Score()
    md = stream.Part(id='P1')
    me = stream.Part(id='P2')

    # Generar 12 compassos (simplificat per estabilitat)
    m_preg = random.choice(m1)
    m_resp = random.choice(m1)
    
    for i in range(12):
        # Mà Dreta
        if i in [0, 1, 4, 5]: c_font = m_preg[0]
        elif i in [2, 3, 6, 7]: c_font = m_resp[0]
        else: c_font = random.choice(m1)[0]
        
        c_md = copy.deepcopy(c_font)
        c_md.number = i + 1
        for el in c_md.getElementsByClass(['Clef', 'TimeSignature', 'KeySignature']): c_md.remove(el)
        if i in [4, 8]: c_md.insert(0, layout.SystemLayout(isNew=True))
        md.append(c_md)

        # Mà Esquerra (Walking Bass bàsic)
        c_me = stream.Measure(number=i+1)
        acord = ['C', 'C', 'C', 'C', 'F', 'F', 'C', 'C', 'G', 'F', 'C', 'C'][i]
        pitches = {'C':['C3', 'E3', 'G3', 'A3'], 'F':['F2', 'A2', 'C3', 'D3'], 'G':['G2', 'B2', 'D3', 'E3']}[acord]
        for p in pitches: c_me.append(note.Note(p, quarterLength=1.0))
        if i in [4, 8]: c_me.insert(0, layout.SystemLayout(isNew=True))
        me.append(c_me)

    # Info inicial
    md[0].insert(0, clef.TrebleClef()); md[0].insert(0, meter.TimeSignature('4/4'))
    me[0].insert(0, clef.BassClef()); me[0].insert(0, meter.TimeSignature('4/4'))
    md[-1].rightBarline = me[-1].rightBarline = bar.Barline('final')

    s.insert(0, md)
    s.insert(0, me)

    # Agrupament Piano
    staff_group = layout.StaffGroup([md, me], symbol='brace', barTogether='yes')
    s.insert(0, staff_group)

    # Transposició i exportació a string
    ton = random.choice(['C', 'G', 'F', 'D'])
    s_final = s.transpose({'C':0, 'G':7, 'F':5, 'D':2}[ton])
    
    # Convertir a MusicXML (text)
    return s_final.write('musicxml').decode('utf-8') if isinstance(s_final.write('musicxml'), bytes) else open(s_final.write('musicxml')).read()

# --- INTERFÍCIE ---
col1, col2 = st.columns(2)
with col1:
    if st.button('🔄 Generar Blues', use_container_width=True):
        xml_result = generar_blues()
        st.session_state.xml_data = xml_result

with col2:
    if st.session_state.xml_data:
        st.download_button("📥 Descarregar", st.session_state.xml_data, "blues.musicxml", use_container_width=True)

if st.session_state.xml_data:
    st.divider()
    mostrar_partitura(st.session_state.xml_data)
