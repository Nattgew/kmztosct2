#!/usr/bin/env python
import xml.etree.ElementTree as etree
from zipfile import ZipFile


class newAirportDiag:

    def __init__(self):
        # self.aptname = ""
        # Each dict has color as the key
        # Each key is a list of the elements to draw in that color
        self.apdlines = {}
        self.reflines = {}
        self.labels = {}
        self.reflabels = {}

        self.cats = {}

    def addlabel(self, label, color, cat):
        # label: (name, lat, lon, desc)
        if cat not in self.cats:
            #print("  Init cat "+str(len(self.cats)+1)+": "+cat)
            self.cats[cat] = {'lines': {}, 'labels': {}}
            #print(self.cats)
        if color not in self.cats[cat]['labels']:
            #print("   Init color: "+color)
            self.cats[cat]['labels'][color] = []
        # Add this label to the right color
        self.cats[cat]['labels'][color].append(label)

    def addline(self, name, coordlist, desc, color, cat):
        if cat not in self.cats:
            #print("  Init cat "+str(len(self.cats)+1)+": "+cat)
            self.cats[cat] = {'lines': {}, 'labels': {}}
            #print(self.cats)
        if color not in self.cats[cat]['lines']:
            #print("   Init color: "+color)
            self.cats[cat]['lines'][color] = []
        # Add this label to the right color
        self.cats[cat]['lines'][color].append((name, coordlist, desc))
    #
    # def addlabel(self, label, color):
    #     # Add a new regular label
    #     # Check if new color to be initialized
    #     if color not in self.labels:
    #         self.labels[color] = []
    #     # Add this label to the right color
    #     self.labels[color].append(label)
    #
    # def addline(self, name, coordlist, color):
    #     if color not in self.apdlines:
    #         self.apdlines[color] = []
    #     self.apdlines[color].append((name, coordlist))
    #
    # def addreflabel(self, label, color):
    #     if color not in self.reflabels:
    #         self.reflabels[color] = []
    #     self.reflabels[color].append(label)
    #
    # def addrefline(self, coordlist, color):
    #     if color not in self.reflines:
    #         self.reflines[color] = []
    #     self.reflines[color].append(coordlist)


def readkmz(kmlfile):
    newdiagrams = {}
    kmz = ZipFile(kmlfile, 'r')
    # Open kml doc in kmz
    kml = kmz.open('doc.kml', 'r')  # .read()
    # namespace for XML stuff, required for etree
    ns = {'sfn': 'http://www.opengis.net/kml/2.2'}
    tree = etree.parse(kml)
    # print("Tree:")
    # print(tree)
    root = tree.getroot()
    # print("Root:")
    # print(root)
    print("Reading Airport Diagram KML...")
    for document in root:  # Document tag
        mainfolderfind = document.findall("sfn:Folder", ns)
        # Main folder with subfolders:
        # ZSE Airport Diagrams
        #     Old Diagram Ref
        #     Current Diagrams
        #     In Work (ignored)
        for mainfolder in mainfolderfind:  # Subfolders are per category
            catfind = mainfolder.findall("sfn:Folder", ns)
            for cat in catfind:
                catname = cat.findall("sfn:name", ns)
                for name in catname:
                    category = name.text
                    print("Category: "+category)

                    #if category == "Current Diagrams":
                    currents = cat.findall("sfn:Folder", ns)
                    for folder in currents:
                        elaptname = folder.findall("sfn:name", ns)
                        for name in elaptname:
                            aptname = name.text
                            print(" Apt name: "+aptname)
                            if aptname not in newdiagrams:
                                newdiagrams[aptname] = newAirportDiag()
                        for apttags in folder:  # Subfolders in airport per color group
                            # print(apttags.tag,apttags.text)
                            nametag = apttags.findall("sfn:name", ns)
                            for tag in nametag:
                                subname = tag.text
                                #print(" Subfolder: "+subname)
                                placemarks = apttags.findall("sfn:Placemark", ns)
                                # keep track of which line we are on
                                apdi = 0
                                for pm in placemarks:  # Placemarks are lines or points
                                    # Create new list to hold points for a line
                                    nametag = pm.findall("sfn:name", ns)
                                    for tag in nametag:
                                        pmname = tag.text
                                        #print("  Placemark: "+pmname)
                                    point = pm.findall("sfn:Point", ns)
                                    lstr = pm.findall("sfn:LineString", ns)
                                    elpol = pm.findall("sfn:Polygon", ns)
                                    descfind = pm.findall("sfn:description", ns)
                                    if descfind:
                                        desc = descfind[0].text.strip()
                                        #print("   Description: "+desc)
                                    else:
                                        desc = ""
                                    for pt in point:  # add any points to this folder
                                        coords = pt.findall("sfn:coordinates", ns)
                                        for coord in coords:  # Get the coords tag
                                            cfields = coord.text.split(",")
                                            lat = float(cfields[1])
                                            lon = float(cfields[0])
                                            # labels[aptname][subname].append([pmname,lat,lon])
                                            newdiagrams[aptname].addlabel((pmname, lat, lon, desc), subname, category)
                                            #print("   Point coords: "+coord.text)
                                            # print(cfields)
                                            # cstr = ddtodms()
                                            # print(cstr)
                                    for ls in lstr:  # Add any lines to this folder
                                        coords = ls.findall("sfn:coordinates", ns)
                                        for coord in coords:  # Get the coords tag
                                            # get rid of the extra whitespace
                                            # Split by spaces between coords
                                            clist = []
                                            cleancoords = coord.text.strip().split(' ')
                                            for cleancoord in cleancoords:
                                                # Coords are lon,lat,alt
                                                # Split these out and convert to float
                                                cfields = cleancoord.split(",")
                                                if len(cfields) > 1:  # some lists are empty
                                                    lat = float(cfields[1])
                                                    lon = float(cfields[0])
                                                    # apdlines[aptname][subname][apdi].append([lat,lon])
                                                    clist.append((lat, lon))
                                            newdiagrams[aptname].addline(pmname, clist, desc, subname, category)
                                            # print("   Line coords: "+cleancoords)
                                            # print("   Line coords:")
                                            # print(cleancoords)
                                    for poly in elpol:
                                        #print("     "+poly.tag)
                                        elobi = poly.findall("sfn:outerBoundaryIs", ns)
                                        for bdry in elobi:
                                            ellinrng = bdry.findall("sfn:LinearRing", ns)
                                            for ring in ellinrng:
                                                coords = ring.findall("sfn:coordinates", ns)
                                                for coord in coords:  # Get the coords tag
                                                    clist = []
                                                    # get rid of the extra whitespace
                                                    # Split by spaces between coords
                                                    cleancoords = coord.text.strip().split(' ')
                                                    for cleancoord in cleancoords:
                                                        # Coords are lon,lat,alt
                                                        # Split these out and convert to float
                                                        cfields = cleancoord.split(",")
                                                        if len(cfields) > 1:  # some lists are empty
                                                            lat = float(cfields[1])
                                                            lon = float(cfields[0])
                                                            # apdlines[aptname][subname][apdi].append([lat,lon])
                                                            clist.append((lat, lon))
                                                    newdiagrams[aptname].addline(pmname, clist, desc, subname, category)
                                                    # print("   Line coords: "+cleancoords)
                                                    #print("   Line coords:")
                                                    # print(cleancoords)
                                    # move on to next list
                                    apdi += 1

                    # elif category == "Old Diagram Ref":
                    #     oldref = cat.findall("sfn:Folder", ns)
                    #     for folder in oldref:
                    #         aptname = folder.findall("sfn:name", ns)
                    #         for name in aptname:
                    #             aptname = name.text
                    #             print("Apt name: "+aptname)
                    #         for apttags in folder:  # Subfolders in airport per color group
                    #             # print(apttags.tag,apttags.text)
                    #             nametag = apttags.findall("sfn:name", ns)
                    #             for tag in nametag:
                    #                 subname = tag.text
                    #                 print(" Subfolder: "+subname)
                    #                 placemarks = apttags.findall("sfn:Placemark", ns)
                    #                 # keep track of which line we are on
                    #                 # apdi = 0
                    #                 for pm in placemarks:  # Placemarks are lines or points
                    #                     # Create new list to hold points for a line
                    #                     nametag = pm.findall("sfn:name", ns)
                    #                     for tag in nametag:
                    #                         pmname = tag.text
                    #                         print("  Placemark: "+pmname)  # REF ONLY for lines
                    #                     point = pm.findall("sfn:Point", ns)
                    #                     lstr = pm.findall("sfn:LineString", ns)
                    #                     for pt in point:  # add any points to this folder
                    #                         coords = pt.findall("sfn:coordinates", ns)
                    #                         for coord in coords:  # Get the coords tag
                    #                             cfields = coord.text.split(",")
                    #                             lat = float(cfields[1])
                    #                             lon = float(cfields[0])
                    #                             # oldlabels[aptname][subname].append([pmname,lat,lon])
                    #                             newdiagrams[aptname].addreflabel((pmname, lat, lon), subname)
                    #                             print("   Point coords: "+coord.text)
                    #                             # print(cfields)
                    #                             # cstr = ddtodms()
                    #                             # print(cstr)
                    #                     for ls in lstr:  # Add any linse to this folder
                    #                         coords = ls.findall("sfn:coordinates", ns)
                    #                         for coord in coords:  # Get the coords tag
                    #                             # get rid of the extra whitespace
                    #                             # Split by spaces between coords
                    #                             cleancoords = coord.text.strip().split(' ')
                    #                             # print(cleancoords)
                    #                             clist = []
                    #                             for cleancoord in cleancoords:
                    #                                 # Coords are lon,lat,alt
                    #                                 # Split these out and convert to float
                    #                                 cfields = cleancoord.split(",")
                    #                                 if len(cfields) > 1:  # some lists are empty
                    #                                     lat = float(cfields[1])
                    #                                     lon = float(cfields[0])
                    #                                     # oldlines[aptname][subname][apdi].append([lat,lon])
                    #                                     clist.append((lat, lon))
                    #                             newdiagrams[aptname].addrefline(clist, subname)
                    #                             # print("   Line coords: "+cleancoords)
                    #                             print("   Line coords:")
                    #                             # print(cleancoords)
                    #                     # move on to next list
                    #                     # apdi += 1
    print("")
    print("THE WHOLE ENCHILADA")
    for apt, dobj in newdiagrams.items():
        print(apt)
        for cat, colors in dobj.cats.items():
            print(" "+cat)
            for color, itemlist in colors.items():
                print("  "+color)
    return newdiagrams
