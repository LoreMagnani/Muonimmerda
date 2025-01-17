import numpy as np
import ROOT
import matplotlib.pyplot as plt
import argparse


# Dimensioni: 80 x 30 x 4 cm (80 x 30 x 2 cm per Circe) distanti 3cm e 7cm
# 1 muone per cm^2 al minuto
# Distribuzione angolare azimutale segue cos^2

# Generatore casuale
def rand ():
    return ROOT.TRandom()

# Generatore casuale uniforme
def rand_unif (min , max):
    return ROOT.TRandom.Uniform(min , max)

def MUONtecarlo (N , altezza_tot, lungo, largo , eff_C , eff_P , eff_A):
    for i in range(N):
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
        x_fondo = x - altezza_tot*np.sin(polar)*np.cos(azimut)
        y_fondo = y - altezza_tot*np.sin(polar)*np.sin(azimut)
        z_fondo = 20*np.cos(azimut)

        if x_fondo < 0 or x_fondo > lungo or y_fondo < 0 or y_fondo > largo:
            continue

        if rand_unif(0 , 1) > eff_P:
            continue

        if rand_unif(0 , 1) > eff_C:
            continue

        if rand_unif(0 , 1) > eff_A:
            continue

        

if __name__ == "__main__":
    # Prendo in ingresso le variabili - momento dinamismo (?)
    parser = argparse.ArgumentParser(description="Simulazione MonteCarlo di 3 scintillatori plastici per muoni")
    parser.add_argument("N_Muon", type=int, help="Numero di gmuoni che passano")
    parser.add_argument("--lungo", type=int, default=80, help="Lunghezza rivelatore (default: 80)")
    parser.add_argument("--largo", type=int, default=30, help="Larghezza rivelatore (default: 30)")
    parser.add_argument("--spesso", type=int, default=4, help="Spessore rivelatore (default: 80)")
    parser.add_argument("--spesso_circe", type=int, default=2, help="Spessore rivelatore Circe (default: 2)")
    parser.add_argument("--buco_1", type=int, default=7, help="Spessore buco sopra rivelatore Circe (default: 7)")
    parser.add_argument("--buco_2", type=int, default=3, help="Spessore buco sotto rivelatore Circe (default: 3)")
    parser.add_argument("--tempo", type=int, default=3600, help="Tempo di misura Circe in secondi (default: 3600 secondi)")
    parser.add_argument("--eff_C", type=int, default=99, help="Efficienza percentuale di Circe (default: 99%")
    parser.add_argument("--eff_P", type=int, default=99, help="Efficienza percentuale di Partenope (default: 99%)")
    parser.add_argument("--eff_A", type=int, default=99, help="Efficienza percentuale di Atena (default: 99%)")

    args = parser.parse_args()

    largo = args.largo
    lungo = args.lungo
    spesso = args.spesso
    spesso_circe = args.spesso_circe
    buco_1 = args.buco_1
    buco_2 = args.buco_2
    tempo = args.tempo
    eff_A = args.eff_a
    eff_P = args.eff_P
    eff_C = args.eff_C

    altezza_tot = 2*spesso + spesso_circe + buco_1 + buco_2
    N = lungo * largo * tempo / 60 #passa (1/60) muoni per cm^2 al secondo

    MUONtecarlo(N , altezza_tot , lungo , largo , eff_C , eff_P , eff_A)
        