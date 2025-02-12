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

def MUONtecarlo2 (N , lungo , largo , eff_C , eff_P , eff_A , spesso1 , spesso2 , spesso3 , buco1 , buco2 , x2 , x3 , y2 , y3 , ang2 , ang3 , Areax , Areay):
    #Per quando modifico la geometria
    Singole_C = 0
    Singole_P = 0
    Singole_A = 0
    doppie = 0
    triple = 0

    i = 0
    while i < N:
        i += 1

        # Genera 2 numeri per le coordinate sul piano contenente il lato superiore del primo scintillatore
        x = rand_unif(-Areax , Areax)
        y = rand_unif(-Areay , Areay)

        # Genera 2 numeri per gli angoli polari e azimutali
        polar = rand_unif(0, 2 * ROOT.TMath.Pi())  # Angolo polare
        u = rand_unif(0, 1)
        azimut = np.arccos(np.sqrt(u))  # Angolo azimutale

        # Correzione
        while rand_unif(0, 1) >= np.exp(-0.14 / np.cos(azimut)):  # Condizione per applicare correzione
            polar = rand_unif(0, 2 * ROOT.TMath.Pi())  # Riprova a generare un nuovo angolo polare
            azimut = np.arccos(np.sqrt(rand_unif(0, 1)))  # Riprova a generare un nuovo angolo azimutale

        interseca_1 = False
        interseca_2 = False
        interseca_3 = False

        # Parametri per angoli polari entro cui vedono - per capirne il senso guarda lo schema (se esiste ancora) o abbi fede nella forza e nello sguardo distratto di una fisica teorica
        A = (lungo/2)**2 + (largo/2)**2

        # Controlliamo che il primo veda
        E = x**2 + y**2
        alfa = np.arctan(y/x)
        alfa_prime = alfa + ROOT.TMath.Pi()

        Dx1 = (x - (lungo/2))**2 + (y + (largo/2))**2
        Fx1 = (x - (lungo/2))**2 + (y - (largo/2))**2 
        if (E - A) == Fx1:
            if (-A+Dx1+E)/(2*Dx1*E) < -1 or (-A+Dx1+E)/(2*Dx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx1+E)/(2*Dx1*E)}")
                continue
            else:
                deltax1 = np.arccos((-A+Dx1+E)/(2*Dx1*E))
            gammax1 = 0
        elif (E - A) == Dx1:
            deltax1 = 0
            if (-A+Fx1+E)/(2*Fx1*E) < -1 or (-A+Fx1+E)/(2*Fx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx1+E)/(2*Fx1*E)}")
                continue
            else:
                gammax1 = np.arccos((-A+Fx1+E)/(2*Fx1*E))
        else:
            if (-A+Dx1+E)/(2*Dx1*E) < -1 or (-A+Dx1+E)/(2*Dx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx1+E)/(2*Dx1*E)}")
                continue
            else:
                deltax1 = np.arccos((-A+Dx1+E)/(2*Dx1*E))
            if (-A+Fx1+E)/(2*Fx1*E) < -1 or (-A+Fx1+E)/(2*Fx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx1+E)/(2*Fx1*E)}")
                continue
            else:
                gammax1 = np.arccos((-A+Fx1+E)/(2*Fx1*E))

        Dx2 = (x + (lungo/2))**2 + (y + (largo/2))**2
        Fx2 = (x + (lungo/2))**2 + (y - (largo/2))**2 
        if (E - A) == Fx2:
            if (-A+Dx2+E)/(2*Dx2*E) < -1 or (-A+Dx2+E)/(2*Dx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx2+E)/(2*Dx2*E)}")
                continue
            else:
                deltax2 = np.arccos((-A+Dx2+E)/(2*Dx2*E))
            gammax2 = 0
        elif (E - A) == Dx2:
            deltax2 = 0
            if (-A+Fx2+E)/(2*Fx2*E) < -1 or (-A+Fx2+E)/(2*Fx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx2+E)/(2*Fx2*E)}")
                continue
            else:
                gammax2 = np.arccos((-A+Fx2+E)/(2*Fx2*E))
        else:
            if (-A+Dx2+E)/(2*Dx2*E) < -1 or (-A+Dx2+E)/(2*Dx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx2+E)/(2*Dx2*E)}")
                continue
            else:
                deltax2 = np.arccos((-A+Dx2+E)/(2*Dx2*E))
            if (-A+Fx2+E)/(2*Fx2*E) < -1 or (-A+Fx2+E)/(2*Fx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx2+E)/(2*Fx2*E)}")
                continue
            else:
                gammax2 = np.arccos((-A+Fx2+E)/(2*Fx2*E))

        Dy1 = (x - (lungo/2))**2 + (y - (largo/2))**2
        Fy1 = (x + (lungo/2))**2 + (y - (largo/2))**2 
        if (E - A) == Fy1:
            if (-A+Dy1+E)/(2*Dy1*E) < -1 or (-A+Dy1+E)/(2*Dy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy1+E)/(2*Dy1*E)}")
                continue
            else:
                deltay1 = np.arccos((-A+Dy1+E)/(2*Dy1*E))
            gammay1 = 0
        elif (E - A) == Dy1:
            deltay1 = 0
            if (-A+Fy1+E)/(2*Fy1*E) < -1 or (-A+Fy1+E)/(2*Fy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy1+E)/(2*Fy1*E)}")
                continue
            else:
                gammay1 = np.arccos((-A+Fy1+E)/(2*Fy1*E))
        else:
            if (-A+Dy1+E)/(2*Dy1*E) < -1 or (-A+Dy1+E)/(2*Dy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy1+E)/(2*Dy1*E)}")
                continue
            else:
                deltay1 = np.arccos((-A+Dy1+E)/(2*Dy1*E))
            if (-A+Fy1+E)/(2*Fy1*E) < -1 or (-A+Fy1+E)/(2*Fy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy1+E)/(2*Fy1*E)}")
                continue
            else:
                gammay1 = np.arccos((-A+Fy1+E)/(2*Fy1*E))

        Dy2 = (x + (lungo/2))**2 + (y + (largo/2))**2
        Fy2 = (x - (lungo/2))**2 + (y + (largo/2))**2 
        if (E - A) == Fy2:
            if (-A+Dy2+E)/(2*Dy2*E) < -1 or (-A+Dy2+E)/(2*Dy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy2+E)/(2*Dy2*E)}")
                continue
            else:
                deltay2 = np.arccos((-A+Dy2+E)/(2*Dy2*E))
            gammay2 = 0
        elif (E - A) == Dy2:
            deltay2 = 0
            if (-A+Fy2+E)/(2*Fy2*E) < -1 or (-A+Fy2+E)/(2*Fy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy2+E)/(2*Fy2*E)}")
                continue
            else:
                gammay2 = np.arccos((-A+Fy2+E)/(2*Fy2*E))
        else:
            if (-A+Dy2+E)/(2*Dy2*E) < -1 or (-A+Dy2+E)/(2*Dy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy2+E)/(2*Dy2*E)}")
                continue
            else:
                deltay2 = np.arccos((-A+Dy2+E)/(2*Dy2*E))
            if (-A+Fy2+E)/(2*Fy2*E) < -1 or (-A+Fy2+E)/(2*Fy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy2+E)/(2*Fy2*E)}")
                continue
            else:
                gammay2 = np.arccos((-A+Fy2+E)/(2*Fy2*E))
        
        param = 0/np.cos(azimut)
        if np.abs(x + param*np.sin(polar)*np.cos(azimut)) < lungo/2 and np.abs(y + param*np.sin(polar)*np.sin(azimut)) < largo/2:
            interseca_1 = True
        else:
            param = spesso1/np.cos(azimut)
            if np.abs(x + param*np.sin(polar)*np.cos(azimut)) < lungo/2 and np.abs(y + param*np.sin(polar)*np.sin(azimut)) < largo/2:
                interseca_1 = True
        if not interseca_1:
            if (x - lungo/2)/np.tan(azimut) < 0 and (x - lungo/2)/np.tan(azimut) > -spesso1 and polar > alfa_prime - gammax1 and polar < alfa_prime + deltax1:
                interseca_1 = True
            elif (x + lungo/2)/np.tan(azimut) < 0 and (x + lungo/2)/np.tan(azimut) > -spesso1 and polar < 2*ROOT.TMath.Pi() - alfa_prime + gammax2 and polar > alfa_prime - deltax2:
                interseca_1 = True
            elif (y + largo/2)/np.tan(azimut) < 0 and (y + largo/2)/np.tan(azimut) > -spesso1 and polar > alfa_prime - gammay1 and polar < alfa_prime + deltay1:
                interseca_1 = True
            elif (y - largo/2)/np.tan(azimut) < 0 and (y - largo/2)/np.tan(azimut) > -spesso1 and polar > 2*ROOT.TMath.Pi() - alfa_prime - gammay2 and polar < 2*ROOT.TMath.Pi() - alfa_prime + deltay2:
                interseca_1 = True

        # Controlliamo che il secondo veda
        E = (x2 - x)**2 + (y2 - y)**2
        alfa = np.arctan((y2 - y)/(x2 - x))
        alfa_prime = alfa + ROOT.TMath.Pi()

        Dx1 = (x2 + (lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) - x)**2 + (y2 - (lungo/2)*np.sin(ang2) + (largo/2)*np.cos(ang2) - y)**2
        Fx1 = (x2 + (lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) - x)**2 + (y2 - (lungo/2)*np.sin(ang2) + (largo/2)*np.cos(ang2) - y)**2 
        if (E - A) == Fx1:
            if (-A+Dx1+E)/(2*Dx1*E) < -1 or (-A+Dx1+E)/(2*Dx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx1+E)/(2*Dx1*E)}")
                continue
            else:
                deltax1 = np.arccos((-A+Dx1+E)/(2*Dx1*E))
            gammax1 = 0
        elif (E - A) == Dx1:
            deltax1 = 0
            if (-A+Fx1+E)/(2*Fx1*E) < -1 or (-A+Fx1+E)/(2*Fx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx1+E)/(2*Fx1*E)}")
                continue
            else:
                gammax1 = np.arccos((-A+Fx1+E)/(2*Fx1*E))
        else:
            if (-A+Dx1+E)/(2*Dx1*E) < -1 or (-A+Dx1+E)/(2*Dx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx1+E)/(2*Dx1*E)}")
                continue
            else:
                deltax1 = np.arccos((-A+Dx1+E)/(2*Dx1*E))
            if (-A+Fx1+E)/(2*Fx1*E) < -1 or (-A+Fx1+E)/(2*Fx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx1+E)/(2*Fx1*E)}")
                continue
            else:
                gammax1 = np.arccos((-A+Fx1+E)/(2*Fx1*E))

        Dx2 = (x2 + (lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) - x)**2 + (y2 - (lungo/2)*np.sin(ang2) + (largo/2)*np.cos(ang2) - y)**2
        Fx2 = (x2 + (lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) - x)**2 + (y2 - (lungo/2)*np.sin(ang2) + (largo/2)*np.cos(ang2) - y)**2  
        if (E - A) == Fx2:
            if (-A+Dx2+E)/(2*Dx2*E) < -1 or (-A+Dx2+E)/(2*Dx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx2+E)/(2*Dx2*E)}")
                continue
            else:
                deltax2 = np.arccos((-A+Dx2+E)/(2*Dx2*E))
            gammax2 = 0
        elif (E - A) == Dx2:
            deltax2 = 0
            if (-A+Fx2+E)/(2*Fx2*E) < -1 or (-A+Fx2+E)/(2*Fx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx2+E)/(2*Fx2*E)}")
                continue
            else:
                gammax2 = np.arccos((-A+Fx2+E)/(2*Fx2*E))
        else:
            if (-A+Dx2+E)/(2*Dx2*E) < -1 or (-A+Dx2+E)/(2*Dx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx2+E)/(2*Dx2*E)}")
                continue
            else:
                deltax2 = np.arccos((-A+Dx2+E)/(2*Dx2*E))
            if (-A+Fx2+E)/(2*Fx2*E) < -1 or (-A+Fx2+E)/(2*Fx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx2+E)/(2*Fx2*E)}")
                continue
            else:
                gammax2 = np.arccos((-A+Fx2+E)/(2*Fx2*E))

        Dy1 = (x2 + (lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) - x)**2 + (y2 - (lungo/2)*np.sin(ang2) + (largo/2)*np.cos(ang2) - y)**2
        Fy1 = (x2 + (lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) - x)**2 + (y2 - (lungo/2)*np.sin(ang2) + (largo/2)*np.cos(ang2) - y)**2  
        if (E - A) == Fy1:
            if (-A+Dy1+E)/(2*Dy1*E) < -1 or (-A+Dy1+E)/(2*Dy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy1+E)/(2*Dy1*E)}")
                continue
            else:
                deltay1 = np.arccos((-A+Dy1+E)/(2*Dy1*E))
            gammay1 = 0
        elif (E - A) == Dy1:
            deltay1 = 0
            if (-A+Fy1+E)/(2*Fy1*E) < -1 or (-A+Fy1+E)/(2*Fy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy1+E)/(2*Fy1*E)}")
                continue
            else:
                gammay1 = np.arccos((-A+Fy1+E)/(2*Fy1*E))
        else:
            if (-A+Dy1+E)/(2*Dy1*E) < -1 or (-A+Dy1+E)/(2*Dy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy1+E)/(2*Dy1*E)}")
                continue
            else:
                deltay1 = np.arccos((-A+Dy1+E)/(2*Dy1*E))
            if (-A+Fy1+E)/(2*Fy1*E) < -1 or (-A+Fy1+E)/(2*Fy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy1+E)/(2*Fy1*E)}")
                continue
            else:
                gammay1 = np.arccos((-A+Fy1+E)/(2*Fy1*E))

        Dy2 = (x2 + (lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) - x)**2 + (y2 - (lungo/2)*np.sin(ang2) + (largo/2)*np.cos(ang2) - y)**2
        Fy2 = (x2 + (lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) - x)**2 + (y2 - (lungo/2)*np.sin(ang2) + (largo/2)*np.cos(ang2) - y)**2  
        if (E - A) == Fy2:
            if (-A+Dy2+E)/(2*Dy2*E) < -1 or (-A+Dy2+E)/(2*Dy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy2+E)/(2*Dy2*E)}")
                continue
            else:
                deltay2 = np.arccos((-A+Dy2+E)/(2*Dy2*E))
            gammay2 = 0
        elif (E - A) == Dy2:
            deltay2 = 0
            if (-A+Fy2+E)/(2*Fy2*E) < -1 or (-A+Fy2+E)/(2*Fy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy2+E)/(2*Fy2*E)}")
                continue
            else:
                gammay2 = np.arccos((-A+Fy2+E)/(2*Fy2*E))
        else:
            if (-A+Dy2+E)/(2*Dy2*E) < -1 or (-A+Dy2+E)/(2*Dy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy2+E)/(2*Dy2*E)}")
                continue
            else:
                deltay2 = np.arccos((-A+Dy2+E)/(2*Dy2*E))
            if (-A+Fy2+E)/(2*Fy2*E) < -1 or (-A+Fy2+E)/(2*Fy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy2+E)/(2*Fy2*E)}")
                continue
            else:
                gammay2 = np.arccos((-A+Fy2+E)/(2*Fy2*E))

        param = (spesso1+buco1)/np.cos(azimut)
        if np.abs(((x + param*np.sin(polar)*np.cos(azimut)) - x2)*np.cos(-ang2) - ((y + param*np.sin(polar)*np.sin(azimut)) - y2)*np.sin(-ang2)) < lungo/2 and np.abs(((x + param*np.sin(polar)*np.cos(azimut)) - x2)*np.sin(-ang2) + ((y + param*np.sin(polar)*np.sin(azimut)) - y2)*np.cos(-ang2)) < largo/2:
            interseca_2 = True
        else:
            param = (spesso1+buco1+spesso2)/np.cos(azimut)
            if np.abs(((x + param*np.sin(polar)*np.cos(azimut)) - x2)*np.cos(-ang2) - ((y + param*np.sin(polar)*np.sin(azimut)) - y2)*np.sin(-ang2)) < lungo/2 and np.abs(((x + param*np.sin(polar)*np.cos(azimut)) - x2)*np.sin(-ang2) + ((y + param*np.sin(polar)*np.sin(azimut)) - y2)*np.cos(-ang2)) < largo/2:
                interseca_2 = True
        if not interseca_2:
            if (x - ((lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) + x2))/np.tan(azimut) < -(spesso1+buco1) and (x - ((lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) + x2))/np.tan(azimut) > -(spesso1+buco1+spesso2) and polar > alfa_prime - gammax1 and polar < alfa_prime + deltax1:
                interseca_2 = True
            elif (x + ((lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) + x2))/np.tan(azimut) < -(spesso1+buco1) and (x + ((lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) + x2))/np.tan(azimut) > -(spesso1+buco1+spesso2) and polar < 2*ROOT.TMath.Pi() - alfa_prime +gammax2 and polar > alfa_prime - deltax2:
                interseca_2 = True
            elif (y + ((largo/2)*np.cos(ang2) - (lungo/2)*np.sin(ang2) + y2))/np.tan(azimut) < -(spesso1+buco1) and (y - ((largo/2)*np.cos(ang2) - (lungo/2)*np.sin(ang2) + y2))/np.tan(azimut) > -(spesso1+buco1+spesso2) and polar > alfa_prime - gammay1 and polar < alfa_prime + deltay1:
                interseca_2 = True
            elif (y - ((largo/2)*np.cos(ang2) - (lungo/2)*np.sin(ang2) + y2))/np.tan(azimut) < -(spesso1+buco1) and (y + ((largo/2)*np.cos(ang2) - (lungo/2)*np.sin(ang2) + y2))/np.tan(azimut) > -(spesso1+buco1+spesso2) and polar > 2*ROOT.TMath.Pi() - alfa_prime - gammay2 and polar < 2*ROOT.TMath.Pi() - alfa_prime + deltay2:
                interseca_2 = True

        # Controlliamo che il terzo veda
        E = (x3 - x)**2 + (y3 - y)**2
        alfa = np.arctan((y3 - y)/(x3 - x))
        alfa_prime = alfa + ROOT.TMath.Pi()

        Dx1 = (x3 + (lungo/2)*np.cos(ang3) + (largo/2)*np.sin(ang3) - x)**2 + (y3 - (lungo/2)*np.sin(ang3) + (largo/2)*np.cos(ang3) - y)**2
        Fx1 = (x3 + (lungo/2)*np.cos(ang3) + (largo/2)*np.sin(ang3) - x)**2 + (y3 - (lungo/2)*np.sin(ang3) + (largo/2)*np.cos(ang3) - y)**2 
        if (E - A) == Fx1:
            if (-A+Dx1+E)/(2*Dx1*E) < -1 or (-A+Dx1+E)/(2*Dx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx1+E)/(2*Dx1*E)}")
                continue
            else:
                deltax1 = np.arccos((-A+Dx1+E)/(2*Dx1*E))
            gammax1 = 0
        elif (E - A) == Dx1:
            deltax1 = 0
            if (-A+Fx1+E)/(2*Fx1*E) < -1 or (-A+Fx1+E)/(2*Fx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx1+E)/(2*Fx1*E)}")
                continue
            else:
                gammax1 = np.arccos((-A+Fx1+E)/(2*Fx1*E))
        else:
            if (-A+Dx1+E)/(2*Dx1*E) < -1 or (-A+Dx1+E)/(2*Dx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx1+E)/(2*Dx1*E)}")
                continue
            else:
                deltax1 = np.arccos((-A+Dx1+E)/(2*Dx1*E))
            if (-A+Fx1+E)/(2*Fx1*E) < -1 or (-A+Fx1+E)/(2*Fx1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx1+E)/(2*Fx1*E)}")
                continue
            else:
                gammax1 = np.arccos((-A+Fx1+E)/(2*Fx1*E))

        Dx2 = (x3 + (lungo/2)*np.cos(ang3) + (largo/2)*np.sin(ang3) - x)**2 + (y3 - (lungo/2)*np.sin(ang3) + (largo/2)*np.cos(ang3) - y)**2
        Fx2 = (x3 + (lungo/2)*np.cos(ang3) + (largo/2)*np.sin(ang3) - x)**2 + (y3 - (lungo/2)*np.sin(ang3) + (largo/2)*np.cos(ang3) - y)**2  
        if (E - A) == Fx2:
            if (-A+Dx2+E)/(2*Dx2*E) < -1 or (-A+Dx2+E)/(2*Dx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx2+E)/(2*Dx2*E)}")
                continue
            else:
                deltax2 = np.arccos((-A+Dx2+E)/(2*Dx2*E))
            gammax2 = 0
        elif (E - A) == Dx2:
            deltax2 = 0
            if (-A+Fx2+E)/(2*Fx2*E) < -1 or (-A+Fx2+E)/(2*Fx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx2+E)/(2*Fx2*E)}")
                continue
            else:
                gammax2 = np.arccos((-A+Fx2+E)/(2*Fx2*E))
        else:
            if (-A+Dx2+E)/(2*Dx2*E) < -1 or (-A+Dx2+E)/(2*Dx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dx2+E)/(2*Dx2*E)}")
                continue
            else:
                deltax2 = np.arccos((-A+Dx2+E)/(2*Dx2*E))
            if (-A+Fx2+E)/(2*Fx2*E) < -1 or (-A+Fx2+E)/(2*Fx2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fx2+E)/(2*Fx2*E)}")
                continue
            else:
                gammax2 = np.arccos((-A+Fx2+E)/(2*Fx2*E))

        Dy1 = (x3 + (lungo/2)*np.cos(ang3) + (largo/2)*np.sin(ang3) - x)**2 + (y3 - (lungo/2)*np.sin(ang3) + (largo/2)*np.cos(ang3) - y)**2
        Fy1 = (x3 + (lungo/2)*np.cos(ang3) + (largo/2)*np.sin(ang3) - x)**2 + (y3 - (lungo/2)*np.sin(ang3) + (largo/2)*np.cos(ang3) - y)**2  
        if (E - A) == Fy1:
            if (-A+Dy1+E)/(2*Dy1*E) < -1 or (-A+Dy1+E)/(2*Dy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy1+E)/(2*Dy1*E)}")
                continue
            else:
                deltay1 = np.arccos((-A+Dy1+E)/(2*Dy1*E))
            gammay1 = 0
        elif (E - A) == Dy1:
            deltay1 = 0
            if (-A+Fy1+E)/(2*Fy1*E) < -1 or (-A+Fy1+E)/(2*Fy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy1+E)/(2*Fy1*E)}")
                continue
            else:
                gammay1 = np.arccos((-A+Fy1+E)/(2*Fy1*E))
        else:
            if (-A+Dy1+E)/(2*Dy1*E) < -1 or (-A+Dy1+E)/(2*Dy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy1+E)/(2*Dy1*E)}")
                continue
            else:
                deltay1 = np.arccos((-A+Dy1+E)/(2*Dy1*E))
            if (-A+Fy1+E)/(2*Fy1*E) < -1 or (-A+Fy1+E)/(2*Fy1*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy1+E)/(2*Fy1*E)}")
                continue
            else:
                gammay1 = np.arccos((-A+Fy1+E)/(2*Fy1*E))

        Dy2 = (x3 + (lungo/2)*np.cos(ang3) + (largo/2)*np.sin(ang3) - x)**2 + (y3 - (lungo/2)*np.sin(ang3) + (largo/2)*np.cos(ang3) - y)**2
        Fy2 = (x3 + (lungo/2)*np.cos(ang3) + (largo/2)*np.sin(ang3) - x)**2 + (y3 - (lungo/2)*np.sin(ang3) + (largo/2)*np.cos(ang3) - y)**2  
        if (E - A) == Fy2:
            if (-A+Dy2+E)/(2*Dy2*E) < -1 or (-A+Dy2+E)/(2*Dy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy2+E)/(2*Dy2*E)}")
                continue
            else:
                deltay2 = np.arccos((-A+Dy2+E)/(2*Dy2*E))
            gammay2 = 0
        elif (E - A) == Dy2:
            deltay2 = 0
            if (-A+Fy2+E)/(2*Fy2*E) < -1 or (-A+Fy2+E)/(2*Fy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy2+E)/(2*Fy2*E)}")
                continue
            else:
                gammay2 = np.arccos((-A+Fy2+E)/(2*Fy2*E))
        else:
            if (-A+Dy2+E)/(2*Dy2*E) < -1 or (-A+Dy2+E)/(2*Dy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Dy2+E)/(2*Dy2*E)}")
                continue
            else:
                deltay2 = np.arccos((-A+Dy2+E)/(2*Dy2*E))
            if (-A+Fy2+E)/(2*Fy2*E) < -1 or (-A+Fy2+E)/(2*Fy2*E) > 1:
                print(f"Valore fuori intervallo per arccos: {(-A+Fy2+E)/(2*Fy2*E)}")
                continue
            else:
                gammay2 = np.arccos((-A+Fy2+E)/(2*Fy2*E))

        param = (spesso1+buco1+spesso2+buco2)/np.cos(azimut)
        if np.abs(((x + param*np.sin(polar)*np.cos(azimut)) - x3)*np.cos(-ang3) - ((y + param*np.sin(polar)*np.sin(azimut)) - y3)*np.sin(-ang3)) < lungo/2 and np.abs(((x + param*np.sin(polar)*np.cos(azimut)) - x3)*np.sin(-ang3) + ((y + param*np.sin(polar)*np.sin(azimut)) - y3)*np.cos(-ang3)) < largo/2:
            interseca_3 = True
        else:
            param = (spesso1+buco1+spesso2+buco2+spesso3)/np.cos(azimut)
            if np.abs(((x + param*np.sin(polar)*np.cos(azimut)) - x3)*np.cos(-ang3) - ((y + param*np.sin(polar)*np.sin(azimut)) - y3)*np.sin(-ang3)) < lungo/2 and np.abs(((x + param*np.sin(polar)*np.cos(azimut)) - x3)*np.sin(-ang3) + ((y + param*np.sin(polar)*np.sin(azimut)) - y3)*np.cos(-ang3)) < largo/2:
                interseca_3 = True
        if not interseca_3:
            if (x - ((lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) + x3))*np.tan(azimut) < -(spesso1+buco1+spesso2+buco2) and (x - ((lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) + x3))*np.tan(azimut) > -(spesso1+buco1+spesso2+buco2+spesso3) and polar > alfa_prime - gammax1 and polar < alfa_prime + deltax1:
                interseca_3 = True
            elif (x + ((lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) + x3))*np.tan(azimut) < -(spesso1+buco1+spesso2+buco2) and (x + ((lungo/2)*np.cos(ang2) + (largo/2)*np.sin(ang2) + x3))*np.tan(azimut) > -(spesso1+buco1+spesso2+buco2+spesso3) and polar < 2*ROOT.TMath.Pi() - alfa_prime +gammax2 and polar > alfa_prime - deltax2:
                interseca_3 = True
            elif (y + ((largo/2)*np.cos(ang2) - (lungo/2)*np.sin(ang2) + y3))*np.tan(azimut) < -(spesso1+buco1+spesso2+buco2) and (y - ((largo/2)*np.cos(ang2) - (lungo/2)*np.sin(ang2) + y3))*np.tan(azimut) > -(spesso1+buco1+spesso2+buco2+spesso3) and polar > alfa_prime - gammay1 and polar < alfa_prime + deltay1:
                interseca_3 = True
            elif (y - ((largo/2)*np.cos(ang2) - (lungo/2)*np.sin(ang2) + y3))*np.tan(azimut) < -(spesso1+buco1+spesso2+buco2) and (y + ((largo/2)*np.cos(ang2) - (lungo/2)*np.sin(ang2) + y3))*np.tan(azimut) > -(spesso1+buco1+spesso2+buco2+spesso3) and polar > 2*ROOT.TMath.Pi() - alfa_prime - gammay2 and polar < 2*ROOT.TMath.Pi() - alfa_prime + deltay2:
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
    parser.add_argument("--lungo", type=float, default=80, help="Lunghezza rivelatore (default: 80)")
    parser.add_argument("--largo", type=float, default=30, help="Larghezza rivelatore (default: 30)")
    parser.add_argument("--spesso", type=float, default=4, help="Spessore rivelatore (default: 80)")
    parser.add_argument("--spesso_circe", type=float, default=2, help="Spessore rivelatore Circe (default: 2)")
    parser.add_argument("--buco_1", type=float, default=7, help="Spessore buco sopra rivelatore Circe (default: 7)")
    parser.add_argument("--buco_2", type=float, default=3, help="Spessore buco sotto rivelatore Circe (default: 3)")
    parser.add_argument("--tempo", type=float, default=3600, help="Tempo di misura Circe in secondi (default: 3600 secondi)")
    parser.add_argument("--eff_C", type=float, default=0.998, help="Efficienza percentuale di Circe (default: 0.99")
    parser.add_argument("--eff_P", type=float, default=0.991, help="Efficienza percentuale di Partenope (default: 0.99)")
    parser.add_argument("--eff_A", type=float, default=0.994, help="Efficienza percentuale di Atena (default: 0.99)")
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
    Ang2 = input("Inserire l'angolo di rotazione del rivelatore centrale: ")
    x3, y3 = map(float, input("Inserire le coordinate (x,y) del centro dell'ultimo rivelatore: ").split(","))
    Ang3 = input("Inserire l'angolo di rotazione dell'ultimo rivelatore: ")

    ang2 = float(Ang2)
    ang3 = float(Ang3)

    ang2 = np.radians(ang2)
    ang3 = np.radians(ang3)

    alfax = np.arctan((buco1 + spesso2 + buco2)/(x3*np.cos(ang3) - (0.5)*lungo))
    alfay = np.arctan((buco1 + spesso2 + buco2)/(y3*np.sin(ang3) - (0.5)*largo))

    Areax = lungo + spesso1*np.cos(alfax)
    Areay = largo + spesso1*np.cos(alfay)
    Area = 2*Areax * 2*Areay

    N = Area * tempo / 60 #passa (1/60) muoni per cm^2 al secondo

    MUONtecarlo2(N , lungo , largo , eff_C , eff_P , eff_A , spesso1 , spesso2 , spesso3 , buco1 , buco2 , x2 , x3 , y2 , y3 , ang2 , ang3 , Areax , Areay)

    if disegna:
        args = [
                "./Draw_geom",
                str(lungo), str(largo),
                str(spesso1), str(spesso2), str(spesso3),
                str(buco1), str(buco2),
                str(x2), str(y2), str(x3), str(y3),
                str(Ang2), str(Ang3)
            ]

        # Esegui il programma C++
        subprocess.run(args)