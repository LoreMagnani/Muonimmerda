#include <TGeoManager.h>
#include <TGeoMaterial.h>
#include <TGeoMedium.h>
#include <TGeoVolume.h>
#include <TGeoMatrix.h>
#include <TApplication.h>
#include <iostream>
#include <cstdlib>

//Il primo rivelatore ha un il centro della faccia inferiore in 0,0,0
//Gli altri 2 sono sotto di lui, le coordinate fanno riferimento alla posizione del centro della faccia inferiore

int main(int argc, char** argv) {
    if (argc < 13) {
        std::cerr << "Usage: " << argv[0] << " <lunghezza> <larghezza> <spessore1> <spessore2> <spessore3> <buco1> <buco2> <x2> <y2> <x3> <y3> <ang2> <ang3>" << std::endl;
        return 1;
    }

    double lunghezza = std::atof(argv[1]) / 2.0;
    double larghezza = std::atof(argv[2]) / 2.0;
    double spessore1 = std::atof(argv[3]) / 2.0;
    double spessore2 = std::atof(argv[4]) / 2.0;
    double spessore3 = std::atof(argv[5]) / 2.0;
    double x2 = std::atof(argv[8]) ;
    double y2 = std::atof(argv[9]) ;
    double x3 = std::atof(argv[10]) ;
    double y3 = std::atof(argv[11]) ;
    double z2 = std::atof(argv[6]) + std::atof(argv[4]) ;
    double z3 = std::atof(argv[6]) + std::atof(argv[4]) + std::atof(argv[7]) + std::atof(argv[5]) ;
    double ang2 = std::atof(argv[12]);
    double ang3 = std::atof(argv[13]);

    TApplication app("app", &argc, argv);
    
    // Creazione del gestore della geometria
    TGeoManager geom("SimpleShapes", "Three Parallelepipeds");

    // Creazione del materiale e del medium
    TGeoMaterial *mat = new TGeoMaterial("Vacuum", 0, 0, 0);
    TGeoMedium *med = new TGeoMedium("Vacuum", 1, mat);

    // Creazione del volume madre
    TGeoVolume *top = geom.MakeBox("Top", med, 20, 20, 20);
    geom.SetTopVolume(top);

    // Creazione di tre parallelepipedi con dimensioni da input
    TGeoVolume *box1 = geom.MakeBox("Box1", med, lunghezza, larghezza, spessore1);
    TGeoVolume *box2 = geom.MakeBox("Box2", med, lunghezza, larghezza, spessore2);
    TGeoVolume *box3 = geom.MakeBox("Box3", med, lunghezza, larghezza, spessore3);
    
    // Creazione delle trasformazioni con rotazione per box2 e box3
    TGeoRotation *rot2 = new TGeoRotation();
    rot2->RotateZ(ang2);
    TGeoCombiTrans *trans2 = new TGeoCombiTrans(x2, y2, -z2 + spessore1, rot2);
    
    TGeoRotation *rot3 = new TGeoRotation();
    rot3->RotateZ(ang3);
    TGeoCombiTrans *trans3 = new TGeoCombiTrans(x3, y3, -z3 + spessore1, rot3);

    // Aggiunta dei parallelepipedi al volume madre con coordinate e rotazioni da input
    top->AddNode(box1, 1, new TGeoTranslation(0, 0, spessore1));
    top->AddNode(box2, 1, trans2);
    top->AddNode(box3, 1, trans3);

    // Chiude la geometria e la disegna
    geom.CloseGeometry();
    top->Draw("ogl");
    
    app.Run();

    return 0;
}
