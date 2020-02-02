#!/usr/bin/env python

# Converts an APD to a KML file
# Grabs lines/labels near airport from sectorfile
# Output file will have same name, as kml file

import re
import sys
from pathlib import Path
import sectorfile
import vrccolors
import xml.etree.ElementTree as ET
import xml.dom.minidom

class sct2apd:

    def __init__(self, name):
        # Each color will have a list of coordinate lists (lines)
        self.linecolors = {}
        self.labelcolors = {}
        # Name used when saving file
        self.name = name

    def addline(self, clist, color):
        # Add line to existing color, or start new list
        if color in self.linecolors:
            self.linecolors[color].append(clist)
        else:
            self.linecolors[color] = [clist]
            # self.gencolor(color)

    def addlabel(self, name, coords, color):
        # Add label to existing color, or start new list
        if color in self.labelcolors:
            self.labelcolors[color].append((coords, name))
        else:
            self.labelcolors[color] = [(coords, name)]
            
    def htmlcolortokml(self, color):
        # Get the color in KML format
        if color in vrccolors.defaultcolors:
            # Get HTML color, strip the #
            color = vrccolors.defaultcolors[color].replace('#', '')
        elif re.search(r'^\d{,8}$', color) is not None:
            # If it's a plain VRC format, convert to HTML and strip the #
            color = vrccolors.deccolortohtml(int(color)).replace('#', '')
        else:
            print("Missing color: "+color)
        # Might want to handle a non-match, just in case
        # Split into RGB pairs
        colorsplit = [color[i:i+2] for i in range(0, len(color), 2)]
        # Reverse because that's how KML does it
        colorsplit.reverse()
        # Join back together and return KML color
        return ''.join(colorsplit)
        
    def newsubfol(self, parent, name, open=0):
        # Add subfolder to XML parent
        newfol = ET.SubElement(parent, 'Folder')
        fname = ET.SubElement(newfol, 'name')
        fname.text = name
        if open:  # Whether folder is expanded
            openit = ET.SubElement(newfol, 'open')
            openit.text = "1"
        return newfol

    def stylepair(self, key, surl):
        # Create style pair for normal/highlighted
        sroot = ET.Element('root')
        pairit = ET.SubElement(sroot, 'Pair')
        keyit = ET.SubElement(pairit, 'key')
        keyit.text = key
        surlit = ET.SubElement(pairit, 'styleUrl')
        surlit.text = "#"+surl
        return sroot

    def style(self, styleid, scale, color):
        # Create style definition for color
        sroot = ET.Element('root')
        styleit = ET.SubElement(sroot, 'Style', id=styleid)
        isit = ET.SubElement(styleit, 'IconStyle')
        scaleit = ET.SubElement(isit, 'scale')
        scaleit.text = scale
        iconit = ET.SubElement(isit, 'Icon')
        hrefit = ET.SubElement(iconit, 'href')
        hrefit.text = "http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png"
        hsit = ET.SubElement(isit, 'hotSpot', x="20", y="2", xunits="pixels", yunits="pixels")
        lsit = ET.SubElement(styleit, 'LineStyle')
        colit = ET.SubElement(lsit, 'color')
        colit.text = "ff"+color
        return sroot

    def genstyles(self):
        # Create style section for each color
        sroot = ET.Element('root')
        for color in self.linecolors:
            sroot.extend(self.genstyle(color))
        for color in self.labelcolors:
            sroot.extend(self.genstyle(color))
        return sroot

    def genstyle(self, color):
        # print(vrccolors.defaultcolors[color])
        # Return a style so we can color the lines
        # Create a map and style IDs
        mapid = "m_" + color
        styleid = "s_" + color
        styleidhl = styleid + "_hl"
        pushurl = "http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png"
        colorhex = self.htmlcolortokml(color)

        sroot = ET.Element('root')
        smap = ET.SubElement(sroot, 'StyleMap', id=mapid)
        smap.extend(self.stylepair("normal", styleid))
        smap.extend(self.stylepair("highlight", styleidhl))
        sroot.extend(self.style(styleidhl, "1.3", colorhex))
        sroot.extend(self.style(styleid, "1.1", colorhex))
        return sroot
    
    def newpmark(self, parent, color, name="Untitled Path"):
        # Create a new placemark under parent
        pmark = ET.SubElement(parent, 'Placemark')
        pname = ET.SubElement(pmark, 'name')
        pname.text = name
        surl = ET.SubElement(pmark, 'styleUrl')
        surl.text = "#m_"+color
        return pmark

    def makelinestring(self, clist, color):
        # Create a new linestring item with coord list
        sroot = ET.Element('root')
        pmark = self.newpmark(sroot, color)
        lsit = ET.SubElement(pmark, 'LineString')
        tess = ET.SubElement(lsit, 'tessellate')
        tess.text = "1"
        coordit = ET.SubElement(lsit, 'coordinates')
        coordit.text = " ".join(["%s,%s,0" % (coord[1], coord[0]) for coord in clist])
        return sroot

    def makelabel(self, label, color):
        # Create a new label item
        sroot = ET.Element('root')
        pmark = self.newpmark(sroot, color, label[1])
        point = ET.SubElement(pmark, 'Point')
        coordit = ET.SubElement(point, 'coordinates')
        coordit.text = "%s,%s,0" % (label[0][1], label[0][0])
        return sroot

    def writekml(self, file):
        # Take the apd info and write KML file with it
        # Set up the basic header fields
        kroot = ET.Element('kml')
        hdratt = [("xmlns", "http://www.opengis.net/kml/2.2"),
                  ("xmlns:gx", "http://www.google.com/kml/ext/2.2"),
                  ("xmlns:kml", "http://www.opengis.net/kml/2.2"),
                  ("xmlns:atom", "http://www.w3.org/2005/Atom")]
        for att in hdratt:
            kroot.set(*att)
        rootdoc = ET.SubElement(kroot, 'Document')
        rootname = ET.SubElement(rootdoc, 'name')
        rootname.text = self.name+".kml"
        # Add styles
        rootdoc.extend(self.genstyles())
        # Create basic folder layout
        zseapd = self.newsubfol(rootdoc, 'ZSE Airport Diagrams', 1)
        currdia = self.newsubfol(zseapd, 'Current Diagrams', 1)
        # olddia = self.newsubfol(zseapd, 'Old Diagram Ref')
        # Create folder for this airport
        aptfol = self.newsubfol(currdia, self.name, 1)
        # Add all of the lines
        for color, lists in self.linecolors.items():
            # Create subfolder for the color
            csub = self.newsubfol(aptfol, color)
            for clist in lists:
                csub.extend(self.makelinestring(clist, color))
        # Add all of the labels
        for color, labels in self.labelcolors.items():
            # Create subfolder for the color
            csub = self.newsubfol(aptfol, color)
            for label in labels:
                csub.extend(self.makelabel(label, color))
        
        # Make it pretty and write the file
        dom = xml.dom.minidom.parseString(ET.tostring(kroot))
        pretty_xml_as_string = dom.toprettyxml(indent="    ")
        with open(file, 'w') as kfile:
            kfile.write(pretty_xml_as_string)

def findlines(masterdir, apt):
    masterdir = Path(masterdir)
    kmlfn = apt + ".kml"
    kmlfile = masterdir / kmlfn
    airac = "1903"
    # For remembering last coord to connect lines
    lastcoord = ""
    lastcolor = ""
    # For storing a new line of coordinates
    thislist = []
    # Read the ZSE file since it should have everything
    print("Building sector file object...")
    sectorobj = sectorfile.sectorfileobj("ZSE-v3_05", masterdir, airac)
    # Get the coordinates for the airport in question
    aptloc = sectorobj.airportcoords[apt]
    # Create an object to convert and store KML
    apd = sct2apd(apt)
    # Go through the SID section looking for layout lines
    print("Searching sid section for lines near "+apt+"...")
    for line in sectorobj.sections['sid']:
        # See if line looks like a valid line
        if re.search(r'^[ \t]+N\d{3}', line) is not None:
            # Split it up to read the elements
            elems = [i for i in line.split(';')[0].split(' ') if i != '']
            if len(elems) > 4:
                # print(elems)
                # Get decimal degrees of coordinates
                coord1 = sectorfile.dmstodd((elems[0], elems[1]))
                coord2 = sectorfile.dmstodd((elems[2], elems[3]))
                color = elems[4]
                # See if it's a continuation of last line
                if coord1 == lastcoord and color == lastcolor:
                    thislist.append(coord2)
                # Test for the initial line, create a new list
                elif lastcoord == "" and lastcolor == "":
                    thislist = [coord1, coord2]
                else:
                    # Last line finished, see if it ended near airport
                    if sectorfile.cosinedist(lastcoord, aptloc) < 3:
                        apd.addline(thislist, lastcolor)
                    # Start a new list with these coordinates
                    thislist = [coord1, coord2]
                # Remeber second coordinates/color for next time
                lastcoord = coord2
                lastcolor = color
    print("Searching labels section for items near "+apt+"...")
    for line in sectorobj.sections['labels']:
        if re.search('^".+" +[NS]', line) is not None:
            lblpre = [i for i in line.split('"') if i]
            postelems = [i for i in lblpre[1].split(';')[0].strip().split(' ') if i]
            # print(lblpre)
            # print(postelems)
            lblelems = ['"'+lblpre[0]+'"']
            lblelems.extend(postelems)
            if len(lblelems) > 3:
                lblcoords = sectorfile.dmstodd((lblelems[1], lblelems[2]))
                if sectorfile.cosinedist(lblcoords, aptloc) < 3:
                    apd.addlabel(lblelems[0].split('"')[1], lblcoords, lblelems[3])
    print("Writing to KML file...")
    apd.writekml(kmlfile)


apt = sys.argv[2]
masterdir = Path(sys.argv[1])
findlines(masterdir, apt)
