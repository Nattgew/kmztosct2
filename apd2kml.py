#!/usr/bin/env python

# Converts an APD to a KML file
# Copy the applicable lines into a new sct2 file
# Output file will have same name, as kml file

import re
import sys
from pathlib import Path
import sectorfile
import vrccolors


class sct2apd:

    def __init__(self, name):
        self.linecolors = {}
        self.labelcolors = {}
        self.name = name

    def addline(self, clist, color):
        if color in self.linecolors:
            self.linecolors[color].append(clist)
        else:
            self.linecolors[color] = [clist]
            # self.gencolor(color)

    def addlabel(self, name, coords, color):
        if color in self.labelcolors:
            self.labelcolors[color].append((coords, name))
        else:
            self.labelcolors[color] = [(coords, name)]

    def genstyles(self):
        styles = ""
        for color in self.linecolors:
            styles += self.genstyle(color)
        for color in self.labelcolors:
            styles += self.genstyle(color)
        return styles

    def htmlcolortokml(self, color):
        if color in vrccolors.defaultcolors:
            color = vrccolors.defaultcolors[color].replace('#', '')
        elif re.search(r'^\d{,8}$', color) is not None:
            color = vrccolors.deccolortohtml(int(color)).replace('#', '')
        colorsplit = [color[i:i+2] for i in range(0, len(color), 2)]
        colorsplit.reverse()
        return ''.join(colorsplit)

    def genstyle(self, color):
        # print(vrccolors.defaultcolors[color])
        mapid = "m_" + color
        styleid = "s_" + color
        styleidhl = styleid + "_hl"
        pushurl = "http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png"
        colorhex = self.htmlcolortokml(color.lower())

        style = '<StyleMap id="'+mapid+'">\n'
        style += "\t\t<Pair>\n\t\t\t<key>normal</key>\n"
        style += "<styleUrl>#"+styleid+"</styleUrl>\n"
        style += "\t\t</Pair>\n\t\t<Pair>\n\t\t\t<key>highlight</key>\n"
        style += "<styleUrl>#"+styleidhl+"</styleUrl>\n"
        style += "</Pair>\n\t</StyleMap>\n"
        style += '<Style id="'+styleidhl+'">\n'
        style += "<IconStyle>\n\t\t<scale>1.3</scale>\n\t\t<Icon>\n"
        style += "<href>"+pushurl+"</href>\n"
        style += '</Icon>\n\t\t<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>\n'
        style += "</IconStyle>\n\t\t<LineStyle>\n"
        style += "<color>ff"+colorhex+"</color>\n"
        style += "</LineStyle>\n\t\t</Style>\n"
        style += '<Style id="'+styleid+'">\n'
        style += "<IconStyle>\n\t\t<scale>1.1</scale>\n\t\t<Icon>\n"
        style += "<href>"+pushurl+"</href>\n"
        style += '</Icon>\n\t\t<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>\n'
        style += "</IconStyle>\n\t\t<LineStyle>\n"
        style += "<color>ff"+colorhex+"</color>\n"
        style += "</LineStyle>\n\t</Style>\n"

        return style

    def writekml(self, file):
        styles = self.genstyles()
        kheader = '''<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
        <Document>\n'''
        kheader += "\t\t<name>"+self.name+".kml</name>\n"+styles+"\t\t<Folder>\n"
        kheader += "\t\t\t<name>"+self.name+"</name>\n\t\t\t<open>1</open>\n"
        kfooter = "\t</Folder>\n</Document>\n</kml>\n"
        pmheader = '\t\t<Placemark>\n'
        lsheader = '''\t\t\t<name>Untitled Path</name>\n
                <LineString>
                <tessellate>1</tessellate>
                <coordinates>\n'''
        ptheader = '''\t\t\t<Point>
                <coordinates>\n'''
        lsfooter = "\t\t\t\t\t</coordinates>\n\t\t\t\t</LineString>\n\t\t\t</Placemark>\n"
        ptfooter = "\t\t\t\t\t</coordinates>\n\t\t\t\t</Point>\n\t\t\t</Placemark>\n"
        ffooter = "</Folder>\n"
        with open(file, "w") as k:
            k.write(kheader)
            for color, lists in self.linecolors.items():
                fheader = "<Folder>\n\t<name>"+color+"</name>\n"
                k.write(fheader)
                for clist in lists:
                    k.write(pmheader)
                    surl = "<styleUrl>#m_"+color+"</styleUrl>"
                    k.write(surl)
                    k.write(lsheader)
                    for coord in clist:
                        cline = "\t\t\t\t\t%s,%s,0\n" % (coord[1], coord[0])
                        k.write(cline)
                    k.write(lsfooter)
                k.write(ffooter)
            for color, labels in self.labelcolors.items():
                fheader = "<Folder>\n\t<name>"+color+"</name>\n"
                k.write(fheader)
                # print(labels)
                for label in labels:
                    # print(label[0])
                    k.write(pmheader)
                    surl = "<styleUrl>#m_"+color+"</styleUrl>"
                    k.write(surl)
                    name = label[1]
                    k.write("<name>"+name+"</name>")
                    k.write(ptheader)
                    cline = "\t\t\t\t\t%s,%s,0\n" % (label[0][1], label[0][0])
                    k.write(cline)
                    k.write(ptfooter)
                k.write(ffooter)
            k.write(kfooter)


def findlines(masterdir, apt):
    masterdir = Path(masterdir)
    kmlfn = apt + ".kml"
    kmlfile = masterdir / kmlfn
    airac = "1903"
    modver = ""
    lastcoord = ""
    lastcolor = ""
    thislist = []
    print("Building sector file object...")
    sectorobj = sectorfile.sectorfileobj("ZSE-v3_05", masterdir, airac, modver)
    aptloc = sectorobj.airportcoords[apt]
    apd = sct2apd(apt)
    print("Searching sid section for lines near "+apt+"...")
    for line in sectorobj.sections['sid']:
        if re.search(r'^[ \t]+N\d{3}', line) is not None:
            elems = [i for i in re.sub(r";.+", '', line).strip().split(' ') if i != '']
            if len(elems) > 4:
                # print(elems)
                coord1 = sectorfile.dmstodd((elems[0], elems[1]))
                coord2 = sectorfile.dmstodd((elems[2], elems[3]))
                color = elems[4]
                if coord1 == lastcoord and color == lastcolor:
                    thislist.append(coord2)
                elif lastcoord == "" and lastcolor == "":
                    thislist = [coord1, coord2]
                else:
                    if sectorfile.cosinedist(lastcoord, aptloc) < 3:
                        apd.addline(thislist, lastcolor)
                    thislist = [coord1, coord2]
                lastcoord = coord2
                lastcolor = color
    apd.writekml(kmlfile)


apt = sys.argv[2]
masterdir = Path(sys.argv[1])
findlines(masterdir, apt)
