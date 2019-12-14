# kmztosct2

## apd2kml

Converts an airport diagram from the sct file to kml. Give the master file directory (containing ZSE-v3_05.sct2) and the airport code. Everything within 3 miles of the airport center is brought over, saved to master directory as code.kml. The structure of the kml file should match what the kmztosct2 program expects.

apd2kml.py "C:\Path\To\MasterDir" "KPDX"

## kmztosct2

Reads a kml file with airport diagrams and updates the masterfile with these new diagrams. Given the master directory with the sector files, location of the kml file, and a version to append to identify the new sector files.

kmztosct2.py "C:\Path\to\MasterDir" "C:\Path\to\diagrams.kmz" "r2.2"

## sectorfile.py

Parses sct2 files, documents this.

## kmzfile.py

Parses kml files, documents this.
