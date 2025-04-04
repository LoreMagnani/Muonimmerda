/*  ><
 *
 */

#include <cstdlib>
#include <stdio.h>
#include <stdlib.h>
#include <fstream>
#include <iostream>
#include <sstream>
#include <cmath>
#include <string>
#include <stack>

#include "TPRegexp.h"
#include "TObjString.h"
#include "TObjArray.h"
#include "TGraph.h"
#include "TCanvas.h"
#include "TFile.h"
#include "TApplication.h"
#include "TAxis.h"
#include "TLegend.h"
#include "TMultiGraph.h"
#include "TH1.h"
#include "TFitResult.h"

// c++ `root-config --cflags` -o analysis analysis.cpp `root-config --glibs`

//int main(int argc, char **argv)
int Tree()
{
	std::fstream file("./xmlfile/test_trigger_100.xml");
	if(!file)
	{
		std::cout << "ERROR: this file does not exist!" <<std::endl;

		return 0;
	}
	/*****************************************************************************/
	/*                            CREO FILE ROOT PER TREE                        */
	/*****************************************************************************/

	TFile* output = TFile::Open("Digitizer.root", "recreate");
	TTree* tree = new TTree ("DigiTree", "Digi");

	/*****************************************************************************/
	/*                            PRESA DATI FILE                                */
	/*****************************************************************************/

	std::string line, sub1, sub2;
	int found, counter;
	int nevents = 4096;
	int recordlength = 4096; 
	std::vector < int > active_channels = {0};
	int* vector0 = new int[recordlength];
	int* vector1 = new int[recordlength];
	int* vector2 = new int[recordlength];
	int* vector3 = new int[recordlength];
	int value;
	int index;

	value = 0;
	found = 0;
	counter = 0;

	tree->Branch("EventId" , &index);
	tree->Branch("Channel0" , vector0, "Channel0[4096]/I");
	tree->Branch("Channel1" , vector1, "Channel1[4096]/I");
	tree->Branch("Channel2" , vector2, "Channel2[4096]/I");
	tree->Branch("Channel3" , vector3, "Channel3[4096]/I");


	TPRegexp r_event_open("<event id=\"([0-9]+)\".*");
	TPRegexp r_event_close("</event>");
	TPRegexp r_channel_open("^\\s*<trace channel=\"([0-4])\">(.*)");
	TPRegexp r_channel_close("\\s*</trace>");

	while ( std::getline(file, line) ) {
		if (r_event_open.MatchB(line) == false) continue;

		TObjArray* obj_array = r_event_open.MatchS(line); 
		TObjString* obj_string = (TObjString*)obj_array->At(1);
		index = std::atoi(obj_string->GetString().Data());
		cout << "Event " << index << endl; 

		for (int j=0; j<recordlength; j++) {
			vector0[j] = 0;
			vector1[j] = 0;
			vector2[j] = 0;
			vector3[j] = 0;
		}

		while ( std::getline(file, line) ) {
			if ( r_event_close.MatchB(line) == true ) {
				tree->Fill();
				break; 
			}

			if ( r_channel_open.MatchB(line) ) {
				TObjArray* obj_charray = r_channel_open.MatchS(line); 
				TObjString* obj_chstring = (TObjString*)obj_charray->At(1);
				TObjString* obj_valstring = (TObjString*)obj_charray->At(2);

				int channel = std::atoi(obj_chstring->GetString().Data());
				cout << "Channel " << channel << endl;

				stringstream sstream;
				sstream	<< obj_valstring->GetString().Data();
				int isample = 0; 
				int val = 0; 

				if (channel == 0) {
					while ( sstream >> val ) {
						vector0[isample] = val; 
						isample++;
					}
				}
				else if (channel == 1) {
					while ( sstream >> val ) {
						vector1[isample] = val;
						isample++;
					}
				}
			}
	
			continue;

		}
	}

	tree->Write(); 
	output->Close(); 

	delete[] vector0; 
	delete[] vector1; 
	delete[] vector2; 
	delete[] vector3; 
	

	return 0;
}


