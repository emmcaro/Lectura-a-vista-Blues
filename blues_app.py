from music21 import *
import random
import copy

def generar_blues_inteligent():
    arxiu_motius_nets = '/Users/caro/Desktop/motius_nets.musicxml'
    arxiu_sortida = '/Users/caro/Desktop/blues_generat.musicxml'

    print("Llegint la teva biblioteca de motius...")
    partitura_motius = converter.parse(arxiu_motius_nets)
    part_dreta_motius = partitura_motius.getElementsByClass(stream.Part)[0]
    
    motius = []
    motiu_actual = []

    # 1. Detecció de motius per silencis
    for compas in part_dreta_motius.getElementsByClass(stream.Measure):
        notes_i_silencis = compas.notesAndRests
        es_buit = True
        if len(notes_i_silencis) > 0:
            for element in notes_i_silencis:
                if not element.isRest: 
                    es_buit = False
                    break
        if es_buit:
            if len(motiu_actual) > 0:
                motius.append(motiu_actual)
                motiu_actual = [] 
        else:
            motiu_actual.append(compas)

    if len(motiu_actual) > 0:
        motius.append(motiu_actual)
        
    motius_1_compas = [m for m in motius if len(m) == 1]
    motius_2_compassos = [m for m in motius if len(m) == 2]
    
    if len(motius_1_compas) == 0:
        print("ERROR: Necessito motius d'1 compàs per funcionar!")
        return

    # Filtre de Mi natural a prova d'acords
    def te_mi_natural(compas):
        for n in compas.flatten().notes:
            if n.isNote and n.pitch.name == 'E':
                return True
            elif n.isChord:
                if any(p.name == 'E' for p in n.pitches):
                    return True
        return False

    motius_1_segurs_F = [m for m in motius_1_compas if not te_mi_natural(m[0])]
    motius_2_segurs_F = [m for m in motius_2_compassos if not te_mi_natural(m[1])]
    
    print(f"S'han detectat {len(motius_1_compas)} motius d'1 compàs ({len(motius_1_segurs_F)} són segurs pel F).")

    partitura = stream.Score()
    ma_dreta = stream.Part()
    ma_esquerra = stream.Part()

    # --- FASE 1: CONSTRUIR LA MÀ DRETA (EN DO MAJOR) ---
    compassos_md = [None] * 12

    if motius_1_segurs_F:
        motiu_pregunta = random.choice(motius_1_segurs_F)
    else:
        motiu_pregunta = random.choice(motius_1_compas)
        
    motius_possibles_resposta = [m for m in motius_1_compas if m != motiu_pregunta]
    if motius_possibles_resposta:
        motiu_resposta = random.choice(motius_possibles_resposta)
    else:
        motiu_resposta = random.choice(motius_1_compas)

    compassos_md[0] = motiu_pregunta[0] 
    compassos_md[4] = motiu_pregunta[0] 
    compassos_md[2] = motiu_resposta[0] 
    compassos_md[6] = motiu_resposta[0] 

    if motius_2_segurs_F:
        motiu_llarg = random.choice(motius_2_segurs_F)
        compassos_md[8] = motiu_llarg[0] 
        compassos_md[9] = motiu_llarg[1] 
    else:
        compassos_md[8] = random.choice(motius_1_compas)[0]
        compassos_md[9] = random.choice(motius_1_segurs_F)[0] if motius_1_segurs_F else random.choice(motius_1_compas)[0]

    for i in range(12):
        if compassos_md[i] is None:
            if i in [4, 5, 9]: 
                compassos_md[i] = random.choice(motius_1_segurs_F)[0] if motius_1_segurs_F else random.choice(motius_1_compas)[0]
            else:
                compassos_md[i] = random.choice(motius_1_compas)[0]

    # --- FASE 4: ABOCAR, NETEJAR I CREAR RESPIRACIONS ---
    compassos_clonats_md = []
    
    for i in range(12):
        compas_clonat = copy.deepcopy(compassos_md[i])
        compas_clonat.number = i + 1
        
        if compas_clonat.rightBarline is not None:
            compas_clonat.rightBarline = None
        for b in compas_clonat.getElementsByClass('Barline'):
            compas_clonat.remove(b)
            
        elements_esborrar = compas_clonat.getElementsByClass(['Clef', 'TimeSignature', 'KeySignature'])
        for element in elements_esborrar:
            compas_clonat.remove(element)
            
        compassos_clonats_md.append(compas_clonat)

    def obtenir_signatura_temps(c, num_temps):
        elements = []
        for e in c.flatten().notesAndRests:
            if num_temps <= float(e.offset) < num_temps + 1:
                offset_rel = round(float(e.offset) - num_temps, 3)
                if e.isNote: nom = e.pitch.name
                elif e.isChord: nom = "Chord"
                else: nom = "Rest"
                elements.append(f"{offset_rel}_{nom}")
        return "|".join(elements)

    def es_compas_repetitiu(c):
        t0 = obtenir_signatura_temps(c, 0)
        t1 = obtenir_signatura_temps(c, 1)
        t2 = obtenir_signatura_temps(c, 2)
        t3 = obtenir_signatura_temps(c, 3)
        if not t0 or t0 == "0.0_Rest": return False 
        return t0 == t1 == t2 == t3

    def comenca_amb_nota(c):
        for e in c.flatten().notesAndRests:
            if float(e.offset) == 0.0 and not e.isRest:
                return True
        return False

    for i in range(11): 
        compas_actual = compassos_clonats_md[i]
        compas_seguent = compassos_clonats_md[i+1]
        
        if es_compas_repetitiu(compas_actual) and comenca_amb_nota(compas_seguent):
            if random.random() < 0.90: 
                nou_compas = stream.Measure()
                nou_compas.number = compas_actual.number
                for e in compas_actual.flatten().notesAndRests:
                    if float(e.offset) < 3.0:
                        nou_compas.insert(float(e.offset), copy.deepcopy(e))
                nou_compas.insert(3.0, note.Rest(quarterLength=1.0))
                compassos_clonats_md[i] = nou_compas

    # Inserim explícitament l'armadura de Do Major a l'inici
    compassos_clonats_md[0].insert(0, clef.TrebleClef())
    compassos_clonats_md[0].insert(0, key.Key('C')) 
    compassos_clonats_md[0].insert(0, meter.TimeSignature('4/4'))
    
    for c in compassos_clonats_md:
        ma_dreta.append(c)

    # --- FASE 2: AUDITORIA RÍTMICA ---
    comptador_semicorxeres = 0
    for nota in ma_dreta.flatten().notes:
        if nota.quarterLength <= 0.25:
            comptador_semicorxeres += 1

    # --- FASE 3: CONSTRUIR LA MÀ ESQUERRA (DUAL, EN DO MAJOR) ---
    progressio_acords = ['C', 'C', 'C', 'C', 'F', 'F', 'C', 'C', 'G', 'F', 'C', 'C']
    
    estil_baix = random.choice(['sense_7a', 'amb_7a'])
    print(f"-> L'estil de baix triat: {estil_baix}")

    if comptador_semicorxeres > 16:
        durada_base = 1.0
        if estil_baix == 'sense_7a':
            patrons = {'C': ['C3 G3', 'C3 A3', 'C3 G3', 'C3 A3'], 'F': ['F2 C3', 'F2 D3', 'F2 C3', 'F2 D3'], 'G': ['G2 D3', 'G2 E3', 'G2 D3', 'G2 E3']}
        else:
            patrons = {'C': ['C3 G3', 'C3 A3', 'C3 B-3', 'C3 A3'], 'F': ['F2 C3', 'F2 D3', 'F2 E-3', 'F2 D3'], 'G': ['G2 D3', 'G2 E3', 'G2 F3', 'G2 E3']}
    else:
        durada_base = 0.5
        if estil_baix == 'sense_7a':
            patrons = {'C': ['C3 G3', 'C3 G3', 'C3 A3', 'C3 A3', 'C3 G3', 'C3 G3', 'C3 A3', 'C3 A3'], 'F': ['F2 C3', 'F2 C3', 'F2 D3', 'F2 D3', 'F2 C3', 'F2 C3', 'F2 D3', 'F2 D3'], 'G': ['G2 D3', 'G2 D3', 'G2 E3', 'G2 E3', 'G2 D3', 'G2 D3', 'G2 E3', 'G2 E3']}
        else:
            patrons = {'C': ['C3 G3', 'C3 G3', 'C3 A3', 'C3 A3', 'C3 B-3', 'C3 B-3', 'C3 A3', 'C3 A3'], 'F': ['F2 C3', 'F2 C3', 'F2 D3', 'F2 D3', 'F2 E-3', 'F2 E-3', 'F2 D3', 'F2 D3'], 'G': ['G2 D3', 'G2 D3', 'G2 E3', 'G2 E3', 'G2 F3', 'G2 F3', 'G2 E3', 'G2 E3']}

    for i in range(12):
        compas_esq = stream.Measure()
        compas_esq.number = i + 1
        
        if i == 0:
            compas_esq.insert(0, clef.BassClef())
            compas_esq.insert(0, key.Key('C')) 
            compas_esq.insert(0, meter.TimeSignature('4/4'))
            
        acord_actual = progressio_acords[i]
        notes_patro = patrons[acord_actual]
        
        for text_notes in notes_patro:
            notes_acord = text_notes.split()
            c = chord.Chord(notes_acord)
            c.quarterLength = durada_base
            compas_esq.append(c)
            
        ma_esquerra.append(compas_esq)

    ma_dreta.getElementsByClass(stream.Measure)[-1].rightBarline = bar.Barline('light-heavy')
    ma_esquerra.getElementsByClass(stream.Measure)[-1].rightBarline = bar.Barline('light-heavy')

    partitura.insert(0, ma_dreta)
    partitura.insert(0, ma_esquerra)

    # --- FASE 5: TRANSPOSICIÓ MÀGICA ---
    mapa_intervals = {
        'C': 'P1',   
        'G': 'P-4',  
        'D': 'M2',   
        'A': 'm-3',  
        'E': 'M3',   
        'F': 'P4'    
    }
    
    tonalitat_escollida = random.choice(list(mapa_intervals.keys()))
    print(f"-> 🎶 Tonalitat escollida per l'exercici: {tonalitat_escollida} Major")
    
    inter = interval.Interval(mapa_intervals[tonalitat_escollida])
    partitura_final = partitura.transpose(inter)

    # --- FASE 6: NETEJA DE METADADES (Sense títol ni autor) ---
    partitura_final.metadata = metadata.Metadata()
    partitura_final.metadata.title = ""
    partitura_final.metadata.composer = ""

    # Guardem el fitxer
    partitura_final.write('musicxml', arxiu_sortida)
    
    print(f"Partitura FINAL generada amb èxit a: {arxiu_sortida}")

generar_blues_inteligent()
