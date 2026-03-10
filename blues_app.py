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
    iframe { background-color: white; border: 1px solid #eee; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎹 Generador de Lectura de Blues")

if 'xml_data' not in st.session_state:
    st.session_state.xml_data = ""

def mostrar_partitura(xml_str):
    if not xml_str:
        return
    
    xml_escapat = json.dumps(xml_str)
    
    html_code = f"""
    <div id="osmdCanvas" style="width: 100%;"></div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
      var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("osmdCanvas", {{
        autoResize: true,
        backend: "svg",
        drawTitle: false,
        drawPartNames: false,
        newSystemFromXML: true,
        stretchLastSystemLine: true,
        drawMeasureNumbers: true
      }});
      
      // FORÇAR CONNEXIÓ DE LÍNIES DE COMPÀS
      osmd.EngravingRules.RenderBarLinesAcrossStaves = true;
      osmd.EngravingRules.StavesConnectorsSpacingAcrossStaves = true;
      
      osmd.load({xml_escapat}).then(function() {{
        osmd.zoom = 1.0;
        osmd.render();
      }}).catch(function(e) {{
        console.error(e);
      }});
    </script>
    """
    components.html(html_code, height=1000, scrolling=True)

def generar_blues():
    arxiu = 'motius_nets.musicxml'
    if not os.path.exists(arxiu):
        st.error(f"No s'ha trobat l'arxiu {arxiu}")
        return ""

    # 1. Carregar motius
    motius_score = converter.parse(arxiu)
    motius_llista = []
    temp = []
    for m in motius_score.parts[0].getElementsByClass(stream.Measure):
        if all(n.isRest for n in m.notesAndRests) if m.notesAndRests else True:
            if temp: motius_llista.append(temp); temp = []
        else: temp.append(m)
    if temp: motius_llista.append(temp)
    
    m1 = [m for m in motius_llista if len(m) == 1]

    # 2. Crear Partitura
    score = stream.Score()
    # Importat: IDs P1 i P2 per a compatibilitat piano
    md = stream.Part(id='P1')
    me = stream.Part(id='P2')

    for i in range(12):
        # Dreta
        font = random.choice(m1)[0]
        c_md = copy.deepcopy(font)
        c_md.number = i + 1
        for el in c_md.getElementsByClass(['Clef', 'TimeSignature', 'KeySignature']): c_md.remove(el)
        if i in [4, 8]: c_md.insert(0, layout.SystemLayout(isNew=True))
        md.append(c_md)

        # Esquerra
        c_me = stream.Measure(number=i+1)
        acord = ['C', 'C', 'C', 'C', 'F', 'F', 'C', 'C', 'G', 'F', 'C', 'C'][i]
        notes_bass = {'C':['C3','G3','A3','G3'], 'F':['F2','C3','D3','C3'], 'G':['G2','D3','E3','D3']}[acord]
        for n_p in notes_bass:
            c_me.append(note.Note(n_p, quarterLength=1.0))
        if i in [4, 8]: c_me.insert(0, layout.SystemLayout(isNew=True))
        me.append(c_me)

    # 3. Configuració Piano
    md[0].insert(0, clef.TrebleClef())
    me[0].insert(0, clef.BassClef())
    md[0].insert(0, meter.TimeSignature('4/4'))
    me[0].insert(0, meter.TimeSignature('4/4'))
    md[-1].rightBarline = bar.Barline('final')
    me[-1].rightBarline = bar.Barline('final')

    score.insert(0, md)
    score.insert(0, me)
    
    # Afegir el grup de piano amb la propietat barTogether
    piano_group = layout.StaffGroup([md, me], symbol='brace', name='Piano', barTogether='yes')
    score.insert(0, piano_group)

    # 4. Exportar a String netejant l'XML
    xml_data = score.write('musicxml')
    with open(xml_data, 'r', encoding='utf-8') as f:
        xml_str = f.read()
    
    # Hack manual de seguretat per forçar el group-barline si music21 l'oblida
    if '<group-barline>' not in xml_str:
        xml_str = xml_str.replace('<group-symbol>brace</group-symbol>', 
                                  '<group-symbol>brace</group-symbol>\n      <group-barline>yes</group-barline>')
    
    return xml_str

# --- UI ---
c1, c2 = st.columns(2)
with c1:
    if st.button('🔄 Generar Nou Blues', use_container_width=True):
        st.session_state.xml_data = generar_blues()

with c2:
    if st.session_state.xml_data:
        st.download_button("📥 Descarregar MusicXML", st.session_state.xml_data, "blues.musicxml", use_container_width=True)

if st.session_state.xml_data:
    st.divider()
    mostrar_partitura(st.session_state.xml_data)
