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

# CSS per eliminar marges superiors i APROFITAR L'AMPLADA als laterals
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    .stButton { margin-top: 0px; }
    iframe { background-color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎹 Generador de Lectura de Blues")

# --- ESTAT DE LA SESSIÓ ---
if 'xml_data' not in st.session_state:
    st.session_state.xml_data = None

# --- VISUALITZADOR OSMD AMB ZOOM FORÇAT AL 90% ---
def mostrar_partitura(xml_bytes):
    xml_str = xml_bytes.decode('utf-8')
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
        stretchLastSystemLine: true,
        coloringMode: 0,
        defaultColorNotehead: "#000000",
        defaultColorStem: "#000000"
      }});
      osmd.load({xml_escapat}).then(function() {{
        osmd.zoom = 0.9;
        osmd.render();
      }});
    </script>
    """
    components.html(html_code, height=850, scrolling=True)

# --- FUNCIÓ PRINCIPAL ---
def generar_blues_inteligent():
    arxiu_motius_nets = 'motius_nets.musicxml'
    
    if not os.path.exists(arxiu_motius_nets):
        st.error(f"❌ No s'ha trobat el fitxer '{arxiu_motius_nets}'")
        return None

    partitura_motius = converter.parse(arxiu_motius_nets)
    part_dreta_motius = partitura_motius.getElementsByClass(stream.Part)[0]
    
    motius = []
    motiu_actual = []

    for compas in part_dreta_motius.getElementsByClass(stream.Measure):
        notes_i_silencis = compas.notesAndRests
        es_buit = all(e.isRest for e in notes_i_silencis) if notes_i_silencis else True
        if es_buit:
            if motiu_actual:
                motius.append(motiu_actual)
                motiu_actual = [] 
        else:
            motiu_actual.append(compas)
    if motiu_actual: motius.append(motiu_actual)
        
    motius_1_compas = [m for m in motius if len(m) == 1]
    motius_2_compassos = [m for m in motius if len(m) == 2]
    
    if not motius_1_compas:
        return None

    def te_mi_natural(compas):
        for n in compas.flatten().notes:
            if (n.isNote and n.pitch.name == 'E') or (n.isChord and any(p.name == 'E' for p in n.pitches)):
                return True
        return False

    motius_1_segurs_F = [m for m in motius_1_compas if not te_mi_natural(m[0])]
    motius_2_segurs_F = [m for m in motius_2_compassos if len(m) > 1 and not te_mi_natural(m[1])]

    partitura = stream.Score()
    
    ma_dreta = stream.Part(id='Part1')
    ma_esquerra = stream.Part(id='Part2')

    compassos_md = [None] * 12
    motiu_pregunta = random.choice(motius_1_segurs_F if motius_1_segurs_F else motius_1_compas)
    motius_possibles_res = [m for m in motius_1_compas if m != motiu_pregunta]
    motiu_resposta = random.choice(motius_possibles_res if motius_possibles_res else motius_1_compas)

    compassos_md[0] = motiu_pregunta[0] 
    compassos_md[4] = motiu_pregunta[0] 
    compassos_md[2] = motiu_resposta[0] 
    compassos_md[6] = motiu_resposta[0] 

    if motius_2_segurs_F:
        m_llarg = random.choice(motius_2_segurs_F)
        compassos_md[8], compassos_md[9] = m_llarg[0], m_llarg[1]
    else:
        compassos_md[8] = random.choice(motius_1_compas)[0]
        compassos_md[9] = random.choice(motius_1_segurs_F if motius_1_segurs_F else motius_1_compas)[0]

    for i in range(12):
        if compassos_md[i] is None:
            if i in [4, 5, 9]:
                compassos_md[i] = random.choice(motius_1_segurs_F if motius_1_segurs_F else motius_1_compas)[0]
            else:
                compassos_md[i] = random.choice(motius_1_compas)[0]

    for i in range(12):
        c_clon = copy.deepcopy(compassos_md[i])
        c_clon.number = i + 1
        for el in c_clon.getElementsByClass(['Clef', 'TimeSignature', 'KeySignature', 'Barline']):
            c_clon.remove(el)
        
        # Inserir salt de línia al principi del 5è i 9è compàs
        if i in [4, 8]:
            c_clon.insert(0, layout.SystemLayout(isNew=True))
        ma_dreta.append(c_clon)

    comptador_semi = sum(1 for n in ma_dreta.flatten().notes if n.quarterLength <= 0.25)
    acords = ['C', 'C', 'C', 'C', 'F', 'F', 'C', 'C', 'G', 'F', 'C', 'C']
    estil = random.choice(['sense_7a', 'amb_7a'])
    durada = 1.0 if comptador_semi > 16 else 0.5
    
    patrons = {
        'sense_7a': {
            'C': ['C3 G3', 'C3 A3'], 
            'F': ['F2 C3', 'F2 D3'], 
            'G': ['G2 D3', 'G2 E3']
        },
        'amb_7a': {
            'C': ['C3 G3', 'C3 A3', 'C3 B-3', 'C3 A3'], 
            'F': ['F2 C3', 'F2 D3', 'F2 E-3', 'F2 D3'], 
            'G': ['G2 D3', 'G2 E3', 'G2 F3', 'G2 E3']
        }
    }

    for i, ac in enumerate(acords):
        m_esq = stream.Measure(number=i+1)
        p = patrons[estil][ac]
        while m_esq.quarterLength < 4.0:
            for n_txt in p:
                if m_esq.quarterLength >= 4.0: break
                ch = chord.Chord(n_txt.split(), quarterLength=durada)
                m_esq.append(ch)
        
        # Inserir salt de línia també a la mà esquerra
        if i in [4, 8]:
            m_esq.insert(0, layout.SystemLayout(isNew=True))
        ma_esquerra.append(m_esq)

    # Neteja de compassos i afegit de claus, compàs i armadura
    ma_dreta[0].insert(0, clef.TrebleClef()); ma_dreta[0].insert(0, key.Key('C')); ma_dreta[0].insert(0, meter.TimeSignature('4/4'))
    ma_esquerra[0].insert(0, clef.BassClef()); ma_esquerra[0].insert(0, key.Key('C')); ma_esquerra[0].insert(0, meter.TimeSignature('4/4'))
    
    # Afegir doble barra de final
    ma_dreta.getElementsByClass(stream.Measure)[-1].rightBarline = bar.Barline('final')
    ma_esquerra.getElementsByClass(stream.Measure)[-1].rightBarline = bar.Barline('final')

    partitura.insert(0, ma_dreta)
    partitura.insert(0, ma_esquerra)

    # Transposar
    mapa_ints = {'C': 'P1', 'G': 'P-4', 'D': 'M2', 'A': 'm-3', 'F': 'P4'}
    ton = random.choice(list(mapa_ints.keys()))
    score_final = partitura.transpose(mapa_ints[ton])
    score_final.metadata = metadata.Metadata(title='', composer='')
    
    # Encara que injectarem el codi manualment després, deixem l'agrupament de music21 per si de cas
    parts_final = list(score_final.getElementsByClass(stream.Part))
    grup_piano = layout.StaffGroup(parts_final, name='', symbol='brace', barTogether='yes')
    score_final.insert(0, grup_piano)

    return score_final

# --- UI STREAMLIT ---
col1, col2 = st.columns([1, 1])
with col1:
    if st.button('🔄 Generar Nou Blues', use_container_width=True):
        res = generar_blues_inteligent()
        if res:
            xml_p = res.write('musicxml')
            
            # --- HACK DEFINITIU AL CODI FONT DEL MUSICXML ---
            with open(xml_p, 'r', encoding='utf-8') as f:
                xml_str = f.read()
                
            # Agafem els IDs de les dues parts generades
            parts_ids = re.findall(r'<score-part id="([^"]+)">', xml_str)
            if len(parts_ids) >= 2:
                id1, id2 = parts_ids[0], parts_ids[1]
                
                # Reescriptura radical i forçada del bloc de llista de parts
                nova_part_list = f"""  <part-list>
    <part-group type="start" number="1">
      <group-symbol>brace</group-symbol>
      <group-barline>yes</group-barline>
    </part-group>
    <score-part id="{id1}"><part-name></part-name></score-part>
    <score-part id="{id2}"><part-name></part-name></score-part>
    <part-group type="stop" number="1"/>
  </part-list>"""
                
                # Substituïm la configuració nativa per la nostra forçada
                xml_str = re.sub(r'<part-list>.*?</part-list>', nova_part_list, xml_str, flags=re.DOTALL)
            
            # Ho guardem a la sessió (afectarà tant al visualitzador com al botó de descàrrega)
            st.session_state.xml_data = xml_str.encode('utf-8')

with col2:
    if st.session_state.xml_data:
        st.download_button("📥 Descarregar MusicXML", data=st.session_state.xml_data, file_name="blues.musicxml", use_container_width=True)

if st.session_state.xml_data:
    st.divider()
    mostrar_partitura(st.session_state.xml_data)
