#include <iostream>
#include <sstream>
#include <cmath>
#include <TGeoManager.h>
#include <TGeoMaterial.h>
#include <TGeoMedium.h>
#include <TGeoVolume.h>
#include <TGeoMatrix.h>

//Per Compilare : g++ -g -o draw_geom draw_geom.cpp $(root-config --cflags) $(root-config --libs) -lGeom

// Funzione per aggiungere un parallelepipedo
void add_box(TGeoManager* geom, TGeoVolume* mother, const std::string& name,
             double dx, double dy, double dz,
             double tx, double ty, double tz, double angle) {
    TGeoMaterial* mat = geom->GetMaterial("Vacuum");
    TGeoMedium* med = geom->GetMedium("Vacuum");

    TGeoVolume* box = geom->MakeBox(name.c_str(), med, 2*dx, 2*dy, 2*dz);
    TGeoRotation* rotation = new TGeoRotation();
    rotation->RotateZ(angle); // Ruota rispetto al piano XY
    TGeoCombiTrans* transform = new TGeoCombiTrans(tx, ty, tz, rotation);
    mother->AddNode(box, 1, transform);
}

int main(int argc, char** argv) {
    if (argc < 14) {
        std::cerr << "Usage: " << argv[0]
                  << "largo + lungo + spesso1 + spesso2 + spesso3 + buco_1 + buco_2 + x2 + y2 + x3 + y3 + ang2 + ang3"
                  << std::endl;
        return 1;
    }

    // Crea il gestore della geometria
    TGeoManager* geom = new TGeoManager("geom", "Geometry with Parallelepipeds");
    TGeoMaterial* mat = new TGeoMaterial("Vacuum", 1, 1, 0.0001785);
    TGeoMedium* med = new TGeoMedium("Vacuum", 1, mat);

    // Crea il volume madre
    TGeoVolume* motherVolume = geom->MakeBox("MotherVolume", med, 200, 200, 200);
    geom->SetTopVolume(motherVolume);

    // Parallelepipedo 1: fisso sul piano XY
    double dx1 = std::stod(argv[1])/2;
    double dy1 = std::stod(argv[2])/2;
    double dz1 = std::stod(argv[3])/2;
    add_box(geom, motherVolume, "Box1", dx1, dy1, dz1, 0, 0, 0, 0);

    // Parallelepipedo 2: specificato da parametri
    double dx2 = std::stod(argv[1])/2;
    double dy2 = std::stod(argv[2])/2;
    double dz2 = std::stod(argv[4])/2;
    double x2 = std::stod(argv[8]);
    double y2 = std::stod(argv[9]);
    double z2 = std::stod(argv[6]) + std::stod(argv[4]);
    double angle2 = std::stod(argv[12]);
    add_box(geom, motherVolume, "Box2", dx2, dy2, dz2, x2, y2, z2, angle2);

    // Parallelepipedo 3: specificato da parametri
    double dx3 = std::stod(argv[1])/2;
    double dy3 = std::stod(argv[2])/2;
    double dz3 = std::stod(argv[5])/2;
    double x3 = std::stod(argv[10]);
    double y3 = std::stod(argv[11]);
    double z3 = std::stod(argv[6]) + std::stod(argv[4]) + std::stod(argv[5]) + std::stod(argv[7]);
    double angle3 = std::stod(argv[13]);
    add_box(geom, motherVolume, "Box3", dx3, dy3, dz3, x3, y3, z3, angle3);

    // Completa la geometria e disegna
    geom->CloseGeometry();
    motherVolume->Draw("ogl");

    return 0;
}
