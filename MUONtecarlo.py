import numpy as np
import ROOT
import matplotlib.pyplot as plt
import argparse
import subprocess


# Dimensioni: 80 x 30 x 4 cm (80 x 30 x 2 cm per Circe) distanti 3cm e 7cm
# 1 muone per cm^2 al minuto
# Distribuzione angolare azimutale segue cos^2 -> asse z va verso il basso


# Generatore casuale
rand = ROOT.TRandom()

# Generatore casuale uniforme
def rand_unif (min , max):
    return rand.Uniform(min , max)

def MUONtecarlo2 (N , lungo , largo , eff_C , eff_P , eff_A , spesso1 , spesso2 , spesso3 , buco1 , buco2 , x2 , x3 , y2 , y3 , ang2 , ang3):
    #Per quando modifico la geometria
    Singole_C = 0
    Singole_P = 0
    Singole_A = 0
    doppie = 0
    triple = 0

    i = 0
    while i < N:
        i += 1

        # Genera 2 numeri per gli angoli polari e azimutali
        polar = rand_unif(0, 2 * ROOT.TMath.Pi())  # Angolo polare
        u = rand_unif(0, 1)
        azimut = np.arccos(np.sqrt(u))  # Angolo azimutale

        # Correzione
        while rand_unif(0, 1) >= np.exp(-0.14 / np.cos(azimut)):  # Condizione per applicare correzione
            polar = rand_unif(0, 2 * ROOT.TMath.Pi())  # Riprova a generare un nuovo angolo polare
            azimut = np.arccos(np.sqrt(rand_unif(0, 1)))  # Riprova a generare un nuovo angolo azimutale

        angxpiano = np.arctan((spesso1+buco1+spesso2+buco2)/(x3*np.cos(polar)-0.5*lungo))
        angypiano = np.arctan((spesso1+buco1+spesso2+buco2)/(y3*np.sin(polar)-0.5*largo))
        xpiano = lungo + spesso1*np.cos(angxpiano)
        ypiano = largo + spesso1*np.cos(angypiano)

        # Genera 2 numeri per le coordinate sul piano contenente il lato superiore del primo scintillatore
        x = rand_unif(-xpiano , xpiano)
        y = rand_unif(-ypiano , ypiano)
       
        interseca_1 = False
        interseca_2 = False
        interseca_3 = False

        # Parametri per angoli polari entro cui vedono - per capirne il senso guarda lo schema (se esiste ancora o abbi fede nella forza e nello sguardo distratto di una fisica teorica)
        A = (lungo/2)**2 + (largo/2)**2

        # Controlliamo che il primo veda
        E = x**2 + y**2
        alfa = np.arctan(y/x)
        alfa_prime = alfa + ROOT.TMath.Pi()

        Dx1 = (x - (lungo/2))**2 + (y + (largo/2))**2
        Fx1 = (x - (lungo/2))**2 + (y - (largo/2))**2 
        deltax1 = np.arccos((A-Dx1-E)/(2*Dx1*E))
        gammax1 = np.arccos((A-E-Fx1)/(2*E*Fx1))

        Dx2 = (x + (lungo/2))**2 + (y + (largo/2))**2
        Fx2 = (x + (lungo/2))**2 + (y - (largo/2))**2 
        deltax2 = np.arccos((A-Dx2-E)/(2*Dx2*E))
        gammax2 = np.arccos((A-E-Fx2)/(2*E*Fx2))

        Dy1 = (x - (lungo/2))**2 + (y - (largo/2))**2
        Fy1 = (x + (lungo/2))**2 + (y - (largo/2))**2 
        deltay1 = np.arccos((A-Dy1-E)/(2*Dy1*E))
        gammay1 = np.arccos((A-E-Fy1)/(2*E*Fy1))

        Dy2 = (x + (lungo/2))**2 + (y + (largo/2))**2
        Fy2 = (x - (lungo/2))**2 + (y + (largo/2))**2 
        deltay2 = np.arccos((A-Dy2-E)/(2*Dy2*E))
        gammay2 = np.arccos((A-E-Fy2)/(2*E*Fy2))
        
        param = 0/np.cos(azimut)
        if np.abs(x + param*np.sin(polar)*np.cos(azimut)) < lungo and np.abs(y + param*np.sin(polar)*np.sin(azimut)):
            interseca_1 = True
        else:
            param = spesso1/np.cos(azimut)
            if np.abs(x + param*np.sin(polar)*np.cos(azimut)) < lungo and np.abs(y + param*np.sin(polar)*np.sin(azimut)):
                interseca_1 = True
        if not interseca_1:
            if (x - lungo)*np.tan(ROOT.TMath.Pi() - azimut) < 0 and (x - lungo)*np.tan(ROOT.TMath.Pi() - azimut) > -spesso1 and polar > alfa_prime - gammax1 and polar < alfa_prime + deltax1:
                interseca_1 = True
            elif (x + lungo)*np.tan(ROOT.TMath.Pi() - azimut) < 0 and (x + lungo)*np.tan(ROOT.TMath.Pi() - azimut) > -spesso1 and polar < 2*ROOT.TMath.Pi() - alfa_prime +gammax2 and polar > alfa_prime - deltax2:
                interseca_1 = True
            elif (y + largo)*np.tan(ROOT.TMath.Pi() - azimut) < 0 and (y + largo)*np.tan(ROOT.TMath.Pi() - azimut) > -spesso1 and polar > alfa_prime - gammay1 and polar < alfa_prime + deltay1:
                interseca_1 = True
            elif (y - largo)*np.tan(ROOT.TMath.Pi() - azimut) < 0 and (y - largo)*np.tan(ROOT.TMath.Pi() - azimut) > -spesso1 and polar > 2*ROOT.TMath.Pi() - alfa_prime - gammay2 and polar < 2*ROOT.TMath.Pi() - alfa_prime + deltay2:
                interseca_1 = True

        # Controlliamo che il secondo veda
        E = (x2 - np.cos(ang2) - x)**2 + (y2 - np.sin(ang2) - y)**2
        alfa = np.arctan((y2 - np.sin(ang2) - y)/(x2 - np.cos(ang2) - x))
        alfa_prime = alfa + ROOT.TMath.Pi()

        Dx1 = (x - x2 - np.cos(ang2) - (lungo/2))**2 + (y - y2 - np.sin(ang2) + (largo/2))**2
        Fx1 = (x - x2 - np.cos(ang2) - (lungo/2))**2 + (y - y2 - np.sin(ang2) - (largo/2))**2 
        deltax1 = np.arccos((A-Dx1-E)/(2*Dx1*E))
        gammax1 = np.arccos((A-E-Fx1)/(2*E*Fx1))

        Dx2 = (x - x2 - np.cos(ang2) + (lungo/2))**2 + (y - y2 - np.sin(ang2) + (largo/2))**2
        Fx2 = (x - x2 - np.cos(ang2) + (lungo/2))**2 + (y - y2 - np.sin(ang2) - (largo/2))**2 
        deltax2 = np.arccos((A-Dx2-E)/(2*Dx2*E))
        gammax2 = np.arccos((A-E-Fx2)/(2*E*Fx2))

        Dy1 = (x - x2 - np.cos(ang2) - (lungo/2))**2 + (y - y2 - np.sin(ang2) - (largo/2))**2
        Fy1 = (x - x2 - np.cos(ang2) + (lungo/2))**2 + (y - y2 - np.sin(ang2) - (largo/2))**2 
        deltay1 = np.arccos((A-Dy1-E)/(2*Dy1*E))
        gammay1 = np.arccos((A-E-Fy1)/(2*E*Fy1))

        Dy2 = (x - x2 - np.cos(ang2) + (lungo/2))**2 + (y - y2 - np.sin(ang2) + (largo/2))**2
        Fy2 = (x - x2 - np.cos(ang2) - (lungo/2))**2 + (y - y2 - np.sin(ang2) + (largo/2))**2 
        deltay2 = np.arccos((A-Dy2-E)/(2*Dy2*E))
        gammay2 = np.arccos((A-E-Fy2)/(2*E*Fy2))

        param = (spesso1+buco1)/np.cos(azimut)
        if np.abs(x - x2 - np.cos(ang2) + param*np.sin(polar)*np.cos(azimut)) < lungo and np.abs(y - y2 - np.sin(ang2) + param*np.sin(polar)*np.sin(azimut)):
            interseca_2 = True
        else:
            param = (spesso1+buco1+spesso2)/np.cos(azimut)
            if np.abs(x - x2 - np.cos(ang2) + param*np.sin(polar)*np.cos(azimut)) < lungo and np.abs(y - y2 - np.sin(ang2) + param*np.sin(polar)*np.sin(azimut)):
                interseca_2 = True
        if not interseca_2:
            if (x - x2 - np.cos(ang2) - lungo)*np.tan(ROOT.TMath.Pi() - azimut) < -(spesso1+buco1) and (x - x2 - np.cos(ang2) - lungo)*np.tan(ROOT.TMath.Pi() - azimut) > -(spesso1+buco1+spesso2) and polar > alfa_prime - gammax1 and polar < alfa_prime + deltax1:
                interseca_2 = True
            elif (x - x2 - np.cos(ang2) + lungo)*np.tan(ROOT.TMath.Pi() - azimut) < -(spesso1+buco1) and (x - x2 - np.cos(ang2) + lungo)*np.tan(ROOT.TMath.Pi() - azimut) > -(spesso1+buco1+spesso2) and polar < 2*ROOT.TMath.Pi() - alfa_prime +gammax2 and polar > alfa_prime - deltax2:
                interseca_2 = True
            elif (y - y2 - np.sin(ang2) + largo)*np.tan(ROOT.TMath.Pi() - azimut) < -(spesso1+buco1) and (y - y2 - np.sin(ang2) - largo)*np.tan(ROOT.TMath.Pi() - azimut) > -(spesso1+buco1+spesso2) and polar > alfa_prime - gammay1 and polar < alfa_prime + deltay1:
                interseca_2 = True
            elif (y - y2 - np.sin(ang2) - largo)*np.tan(ROOT.TMath.Pi() - azimut) < -(spesso1+buco1) and (y - y2 - np.sin(ang2) + largo)*np.tan(ROOT.TMath.Pi() - azimut) > -(spesso1+buco1+spesso2) and polar > 2*ROOT.TMath.Pi() - alfa_prime - gammay2 and polar < 2*ROOT.TMath.Pi() - alfa_prime + deltay2:
                interseca_2 = True

        # Controlliamo che il terzo veda
        E = (x3 - np.cos(ang3) - x)**2 + (y3 - np.sin(ang3) - y)**2
        alfa = np.arctan((y3 - np.sin(ang3) - y)/(x3 - np.cos(ang3) - x))
        alfa_prime = alfa + ROOT.TMath.Pi()

        Dx1 = (x - x3 - np.cos(ang3) - (lungo/2))**2 + (y - y3 - np.sin(ang3) + (largo/2))**2
        Fx1 = (x - x3 - np.cos(ang3) - (lungo/2))**2 + (y - y3 - np.sin(ang3) - (largo/2))**2 
        deltax1 = np.arccos((A-Dx1-E)/(2*Dx1*E))
        gammax1 = np.arccos((A-E-Fx1)/(2*E*Fx1))

        Dx2 = (x - x3 - np.cos(ang3) + (lungo/2))**2 + (y - y3 - np.sin(ang3) + (largo/2))**2
        Fx2 = (x - x3 - np.cos(ang3) + (lungo/2))**2 + (y - y3 - np.sin(ang3) - (largo/2))**2 
        deltax2 = np.arccos((A-Dx2-E)/(2*Dx2*E))
        gammax2 = np.arccos((A-E-Fx2)/(2*E*Fx2))

        Dy1 = (x - x3 - np.cos(ang3) - (lungo/2))**2 + (y - y3 - np.sin(ang3) - (largo/2))**2
        Fy1 = (x - x3 - np.cos(ang3) + (lungo/2))**2 + (y - y3 - np.sin(ang3) - (largo/2))**2 
        deltay1 = np.arccos((A-Dy1-E)/(2*Dy1*E))
        gammay1 = np.arccos((A-E-Fy1)/(2*E*Fy1))

        Dy2 = (x - x3 - np.cos(ang3) + (lungo/2))**2 + (y - y3 - np.sin(ang3) + (largo/2))**2
        Fy2 = (x - x3 - np.cos(ang3) - (lungo/2))**2 + (y - y3 - np.sin(ang3) + (largo/2))**2 
        deltay2 = np.arccos((A-Dy2-E)/(2*Dy2*E))
        gammay2 = np.arccos((A-E-Fy2)/(2*E*Fy2))

        param = (spesso1+buco1+spesso2+buco2)/np.cos(azimut)
        if np.abs(x - x3 - np.cos(ang3) + param*np.sin(polar)*np.cos(azimut)) < lungo and np.abs(y - y3 - np.sin(ang3) + param*np.sin(polar)*np.sin(azimut)):
            interseca_3 = True
        else:
            param = (spesso1+buco1+spesso2+buco2+spesso3)/np.cos(azimut)
            if np.abs(x - x3 - np.cos(ang3) + param*np.sin(polar)*np.cos(azimut)) < lungo and np.abs(y - y3 - np.sin(ang3) + param*np.sin(polar)*np.sin(azimut)):
                interseca_3 = True
        if not interseca_3:
            if (x - x3 - np.cos(ang3) - lungo)*np.tan(ROOT.TMath.Pi() - azimut) < -(spesso1+buco1+spesso2+buco2) and (x - x3 - np.cos(ang3) - lungo)*np.tan(ROOT.TMath.Pi() - azimut) > -(spesso1+buco1+spesso2+buco2+spesso3) and polar > alfa_prime - gammax1 and polar < alfa_prime + deltax1:
                interseca_3 = True
            elif (x - x3 - np.cos(ang3) + lungo)*np.tan(ROOT.TMath.Pi() - azimut) < -(spesso1+buco1+spesso2+buco2) and (x - x3 - np.cos(ang3) + lungo)*np.tan(ROOT.TMath.Pi() - azimut) > -(spesso1+buco1+spesso2+buco2+spesso3) and polar < 2*ROOT.TMath.Pi() - alfa_prime +gammax2 and polar > alfa_prime - deltax2:
                interseca_3 = True
            elif (y - y3 - np.sin(ang3) + largo)*np.tan(ROOT.TMath.Pi() - azimut) < -(spesso1+buco1+spesso2+buco2) and (y - y3 - np.sin(ang3) - largo)*np.tan(ROOT.TMath.Pi() - azimut) > -(spesso1+buco1+spesso2+buco2+spesso3) and polar > alfa_prime - gammay1 and polar < alfa_prime + deltay1:
                interseca_3 = True
            elif (y - y3 - np.sin(ang3) - largo)*np.tan(ROOT.TMath.Pi() - azimut) < -(spesso1+buco1+spesso2+buco2) and (y - y3 - np.sin(ang3) + largo)*np.tan(ROOT.TMath.Pi() - azimut) > -(spesso1+buco1+spesso2+buco2+spesso3) and polar > 2*ROOT.TMath.Pi() - alfa_prime - gammay2 and polar < 2*ROOT.TMath.Pi() - alfa_prime + deltay2:
                interseca_3 = True

        ## Se il primo o l'ultimo non vedono non lo considero un evento
        #if not interseca_3:
        #    continue
        #if not interseca_1:
        #    continue

        vede1 = False
        vede2 = False
        vede3 = False

        # Aumento i conteggi
        if interseca_1:
            if alto == "Circe":
                if rand_unif(0, 1) < eff_C:
                    Singole_C += 1
                    vede1 = True
            elif alto == "Atena":
                if rand_unif(0, 1) < eff_A:
                    Singole_A += 1
                    vede1 = True
            else:
                if rand_unif(0, 1) < eff_P:
                    Singole_P += 1
                    vede1 = True
        if interseca_2:
            if centro == "Circe":
                if rand_unif(0, 1) < eff_C:
                    Singole_C += 1
                    vede2 = True
            elif centro == "Atena":
                if rand_unif(0, 1) < eff_A:
                    Singole_A += 1
                    vede2 = True
            else:
                if rand_unif(0, 1) < eff_P:
                    Singole_P += 1
                    vede2 = True
        if interseca_3:
            if basso == "Circe":
                if rand_unif(0, 1) < eff_C:
                    Singole_C += 1
                    vede3 = True
            elif basso == "Atena":
                if rand_unif(0, 1) < eff_A:
                    Singole_A += 1
                    vede3 = True
            else:
                if rand_unif(0, 1) < eff_P:
                    Singole_P += 1
                    vede3 = True
        if vede1 and vede3 and not vede2:
            doppie += 1
        if vede1 and vede3 and vede2:
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
    parser.add_argument("Alto", type=str, help="Nome rivelatore in alto")
    parser.add_argument("Centro", type=str, help="Nome rivelatore centrale")
    parser.add_argument("Basso", type=str, help="Nome rivelatore in basso")
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
    buco1 = args.buco_1
    buco2 = args.buco_2
    tempo = args.tempo
    eff_A = args.eff_A
    eff_P = args.eff_P
    eff_C = args.eff_C
    alto =args.Alto
    centro = args.Centro
    basso = args.Basso
    disegna = args.disegna

    # Ordina i 3 rivelatori (differenziati per spessore)
    if centro == "Circe":
        spesso1 = spesso
        spesso2 = spesso_circe
        spesso3 = spesso
    elif alto == "Circe":
        spesso1 = spesso_circe
        spesso2 = spesso
        spesso3 = spesso
    else:
        spesso1 = spesso
        spesso2 = spesso
        spesso3 = spesso_circe

    x2, y2 = map(float, input("Inserire le coordinate (x,y) del centro del rivelatore centrale: ").split(","))
    ang2 = input("Inserire l'angolo di rotazione del rivelatore centrale: ")
    x3, y3 = map(float, input("Inserire le coordinate (x,y) del centro dell'ultimo rivelatore: ").split(","))
    ang3 = input("Inserire l'angolo di rotazione dell'ultimo rivelatore: ")

    ang2 = float(ang2)
    ang3 = float(ang3)

    ang2 = np.radians(ang2)
    ang3 = np.radians(ang3)

    alfax = np.arctan((buco1 + spesso2 + buco2)/(x3*np.cos(ang3) - (0.5)*lungo))
    alfay = np.arctan((buco1 + spesso2 + buco2)/(y3*np.sin(ang3) - (0.5)*largo))

    Areax = lungo + spesso1*np.cos(alfax)
    Areay = largo + spesso1*np.cos(alfay)
    Area = Areax * Areay

    N = Area * tempo / 60 #passa (1/60) muoni per cm^2 al secondo

    MUONtecarlo2(N , lungo , largo , eff_C , eff_P , eff_A , spesso1 , spesso2 , spesso3 , buco1 , buco2 , x2 , x3 , y2 , y3 , ang2 , ang3)

    if disegna:
        args = [
                "./Draw_geom",
                str(lungo), str(largo),
                str(spesso1), str(spesso2), str(spesso3),
                str(buco1), str(buco2),
                str(x2), str(y2), str(x3), str(y3),
                str(ang2), str(ang3)
            ]

        # Esegui il programma C++
        subprocess.run(args)