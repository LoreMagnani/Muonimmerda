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

# Prendo in ingresso le variabili
parser = argparse.ArgumentParser(description="Simulazione MonteCarlo di 3 scintillatori plastici per muoni")
parser.add_argument("N_Muon", type=int, help="Numero di gmuoni che passano")
args = parser.parse_args()
N = args.N_Muon

for i in range(N):
    # Genera 2 numeri per le coordinate sul piano del primo scintillatore
    x = rand_unif(0 , 80)
    y = rand_unif(0 , 30) 

    # Genera 2 numeri per gli angoli polari e azimutali
    polar = rand_unif(0, 2 * ROOT.TMath.Pi())  # Angolo polare
    azimut = np.arccos(np.sqrt(rand_unif(0, 1)))  # Angolo azimutale

    # Correzione
    while rand_unif(0, 1) >= np.exp(-0.14 / np.cos(azimut)):  # Condizione per applicare correzione
        polar = rand_unif(0, 2 * ROOT.TMath.Pi())  # Riprova a generare un nuovo angolo polare
        azimut = np.arccos(np.sqrt(rand_unif(0, 1)))  # Riprova a generare un nuovo angolo azimutale

    # Verifica che questa traiettoria intersechi tutti e 3 i rivelatori (profondità 20cm, sommando spessori e spazi)
    x_fondo = x - 20*np.sin(polar)*np.cos(azimut)
    y_fondo = y - 20*np.sin(polar)*np.sin(azimut)
    z_fondo = z - 20*np.cos(azimut)

    if x_fondo < 0 or x_fondo > 80 or y_fondo < 0 or y_fondo > 30:
        continue

    