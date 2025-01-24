import numpy as np
import ROOT
import matplotlib.pyplot as plt
import argparse
import subprocess


# Dimensioni: 80 x 30 x 4 cm (80 x 30 x 2 cm per Circe) distanti 3cm e 7cm
# 1 muone per cm^2 al minuto
# Distribuzione angolare azimutale segue cos^2


# Generatore casuale
rand = ROOT.TRandom()

# Generatore casuale uniforme
def rand_unif (min , max):
    return rand.Uniform(min , max)

def draw_detectors_3d(lungo, largo, spesso, buco_1, buco_2, spesso_centro, centro):
    ROOT.gROOT.SetBatch(False)  # Disabilita la modalità batch per abilitare il rendering grafico

    # Crea il gestore della geometria
    geom = ROOT.TGeoManager("geom", "Geometria dei Rivelatori")

    mat_vuoto = ROOT.TGeoMaterial("Vuoto", 1, 1, 0.0001785)  # Nome, Z, A, densità
    vuoto = ROOT.TGeoMedium("Aria", 1, mat_vuoto)

    # Crea il volume madre
    world = geom.MakeBox("World", vuoto, lungo, largo, buco_1 + buco_2 + spesso + 10)
    geom.SetTopVolume(world)

    # Aggiungi un altro volume per il test
    atena = geom.MakeBox("Atena", vuoto, lungo / 2, largo / 2, spesso / 2)
    world.AddNode(atena, 1, ROOT.TGeoTranslation(0, 0, 0))  # Posiziona Atena

    # Costruzione della geometria
    geom.CloseGeometry()  # Chiude la geometria

    # Impostazione del livello di visibilità
    geom.SetVisLevel(1)

    # Crea un canvas e disegna
    canvas = ROOT.TCanvas("canvas", "Simulazione Geometria Rivelatori 3D", 800, 600)
    canvas.Divide(1, 1)  # Separa il canvas in una divisione

    # Usa OpenGL per il rendering 3D
    geom.Draw("ogl")  # Questo dovrebbe aprire una finestra grafica interattiva


def MUONtecarlo (N , altezza, lungo, largo , eff_C , eff_P , eff_A , centro):
    Singole_C = 0
    Singole_P = 0
    Singole_A = 0
    doppie = 0
    triple = 0

    i = 0
    while (i < N):
        i += 1
        # Genera 2 numeri per le coordinate sul piano del primo scintillatore
        x = rand_unif(0 , lungo)
        y = rand_unif(0 , largo) 

        # Genera 2 numeri per gli angoli polari e azimutali
        polar = rand_unif(0, 2 * ROOT.TMath.Pi())  # Angolo polare
        azimut = np.arccos(np.sqrt(rand_unif(0, 1)))  # Angolo azimutale

        # Correzione
        while rand_unif(0, 1) >= np.exp(-0.14 / np.cos(azimut)):  # Condizione per applicare correzione
            polar = rand_unif(0, 2 * ROOT.TMath.Pi())  # Riprova a generare un nuovo angolo polare
            azimut = np.arccos(np.sqrt(rand_unif(0, 1)))  # Riprova a generare un nuovo angolo azimutale

        # Verifica che questa traiettoria intersechi tutti e 3 i rivelatori (profondità 20cm, sommando spessori e spazi)
        x_fondo = x - altezza*np.sin(polar)*np.cos(azimut)
        y_fondo = y - altezza*np.sin(polar)*np.sin(azimut)
        z_fondo = altezza*np.cos(azimut)

        if x_fondo < 0 or x_fondo > lungo or y_fondo < 0 or y_fondo > largo:
            continue

        # Verifica che i rivelatori vedano la particella
        C_vede = False
        P_vede = False
        A_vede = False

        if rand_unif(0 , 1) < eff_P:
            P_vede = True
            Singole_P += 1

        if rand_unif(0 , 1) < eff_C:
            C_vede = True
            Singole_C += 1

        if rand_unif(0 , 1) < eff_A:
            A_vede = True
            Singole_A += 1
    
        # Conteggia le doppie e le triple
        if centro == "Circe":
            if P_vede and A_vede and not C_vede:
                doppie += 1
            if P_vede and A_vede and C_vede:
                doppie += 1
                triple += 1
        
        if centro == "Partenope":
            if not P_vede and A_vede and C_vede:
                doppie += 1
            if P_vede and A_vede and C_vede:
                doppie += 1
                triple += 1

        if centro == "Atena":
            if P_vede and not A_vede and C_vede:
                doppie += 1
            if P_vede and A_vede and C_vede:
                doppie += 1
                triple += 1
    
    print(f" ---- Conteggi dei singoli rivelatori ---- \n \
---- Atena   |  Partenope  |   Circe ---- \n \
---- {Singole_A}  |    {Singole_P}   |  {Singole_C} ---- \n \
----------------------------------------- \n \
-------- Conteggi doppi e tripli -------- \n \
---- Doppie : {doppie} \n \
---- Triple : {triple} \n \
----------------------------------------- \n \
---- Efficienza di {centro} : {triple / doppie}")

if __name__ == "__main__":
    # Prendo in ingresso le variabili - momento dinamismo (?)
    parser = argparse.ArgumentParser(description="Simulazione MonteCarlo di 3 scintillatori plastici per muoni")
    parser.add_argument("Centro", type=str, help="Nome rivelatore centrale")
    parser.add_argument("--lungo", type=int, default=80, help="Lunghezza rivelatore (default: 80)")
    parser.add_argument("--largo", type=int, default=30, help="Larghezza rivelatore (default: 30)")
    parser.add_argument("--spesso", type=int, default=4, help="Spessore rivelatore (default: 80)")
    parser.add_argument("--spesso_circe", type=int, default=2, help="Spessore rivelatore Circe (default: 2)")
    parser.add_argument("--buco_1", type=int, default=7, help="Spessore buco sopra rivelatore Circe (default: 7)")
    parser.add_argument("--buco_2", type=int, default=3, help="Spessore buco sotto rivelatore Circe (default: 3)")
    parser.add_argument("--tempo", type=int, default=3600, help="Tempo di misura Circe in secondi (default: 3600 secondi)")
    parser.add_argument("--eff_C", type=float, default=0.99, help="Efficienza percentuale di Circe (default: 0.99")
    parser.add_argument("--eff_P", type=float, default=0.99, help="Efficienza percentuale di Partenope (default: 0.99)")
    parser.add_argument("--eff_A", type=float, default=0.99, help="Efficienza percentuale di Atena (default: 0.99)")
    parser.add_argument("--disegna", action="store_true", help="Impostare se si vuole disegnare la geometria") 

    args = parser.parse_args()

    largo = args.largo
    lungo = args.lungo
    spesso = args.spesso
    spesso_circe = args.spesso_circe
    buco_1 = args.buco_1
    buco_2 = args.buco_2
    tempo = args.tempo
    eff_A = args.eff_A
    eff_P = args.eff_P
    eff_C = args.eff_C
    centro = args.Centro
    disegna = args.disegna

    if centro == "Circe":
        spesso_centro = spesso_circe
    else: spesso_centro = spesso
    altezza = buco_1 + buco_2 + spesso_centro #dal fondo del più alto al sopra dell'ultimo --> 2 buchi e spessore rivelatore centrale
    N = lungo * largo * tempo / 60 #passa (1/60) muoni per cm^2 al secondo

    MUONtecarlo(N , altezza , lungo , largo , eff_C , eff_P , eff_A , centro)

    if disegna:
        x2, y2 = map(float, input("Inserire le coordinate (x,y) del rivelatore centrale: ").split(","))
        ang2 = input("Inserire l'angolo di rotazione del rivelatore centrale: ")
        x3, y3 = map(float, input("Inserire le coordinate (x,y) dell'ultimo rivelatore: ").split(","))
        ang3 = input("Inserire l'angolo di rotazione dell'ultimo rivelatore: ")

        if centro == "Circe":
            spesso1 = spesso
            spesso2 = spesso_circe
            spesso3 = spesso
        else:
            spesso = spesso_circe
            spesso2 = spesso
            spesso3 = spesso

        args = [
                "./draw_geom",
                str(largo), str(lungo),
                str(spesso1), str(spesso2), str(spesso3),
                str(buco_1), str(buco_2),
                str(x2), str(y2), str(x3), str(y3),
                str(ang2), str(ang3)
            ]

        # Esegui il programma C++
        subprocess.run(args)