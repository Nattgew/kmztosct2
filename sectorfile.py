#!/usr/bin/env python

import math
import re
from pathlib import Path
import vrccolors

# Basic structure of sct2 file is as follows
# All headers listed, some not used here:
# ;header
# #define colors
# [REGIONS]
# [LABELS]
# [AIRPORT]
# [INFO]
# [VOR]
# [NDB]
# [RUNWAY]
# [FIXES]
# [ARTCC]
# [ARTCC HIGH] ;unused
# [ARTCC LOW] ;unused
# [SID]
# ========SIDs=========     N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000
# ========APDs=========     N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000
# (Airports)                 N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000
# ;KSEA...
# ======AIRSPACE=======     N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000
# =====VIDEO MAPS======     N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000
# [STAR]
# ========SUAs=========     N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000
# =====VIDEO MAPS======     N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000
# **COMMON DATA**            N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000 ; GEO stuff
# ==SECTOR BOUNDARIES==     N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000
# ===2 SECTOR SPLIT===         N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000
# [LOW AIRWAY]
# [HIGH AIRWAY]
# [GEO] ;unused


class sectorfileobj:
    # List of main airports and which sector they are in
    # This is used to include the diagrams/labels in the right files
    aptsectors = {
        "KALW": "PSC",
        "KBFI": "S46",
        "KBLI": "BLI",
        "KEUG": "EUG",
        "KGEG": "GEG",
        "KGRF": "S46",
        "KHIO": "P80",
        "KLMT": "LMT",
        "KLWS": "",
        "KMFR": "MFR",
        "KMWH": "MWH",
        "KNUW": "NUW",
        "KOLM": "S46",
        "KOTH": "OTH",
        "KPAE": "S46",
        "KPDT": "PSC",
        "KPDX": "P80",
        "KPSC": "PSC",
        "KRDM": "",
        "KRNT": "S46",
        "KSEA": "S46",
        "KSFF": "GEG",
        "KSKA": "GEG",
        "KSLE": "",
        "KTCM": "S46",
        "KTIW": "S46",
        "KTTD": "P80",
        "KUAO": "P80",
        "KYKM": "YKM"
    }

    # Standard sections recognized by VRC
    # "header" is comment info at the top
    stdsections = ["header", "colors", "info", "regions", "low airway",
                   "high airway", "airport", "vor", "ndb", "runway",
                   "fixes", "artcc", "labels", "sid", "star",
                   "artcc high", "artcc low", "geo"]

    # Get dictionary of colors
    deccolors = vrccolors.getcolors()

    def __init__(self, filename, directory, airac, modver):
        # Sector code is first 3 of file name
        self.sector = filename[:3]
        self.basename = filename
        self.directory = Path(directory)
        self.airac = airac
        self.modver = modver
        self.masterfilename = filename+"_"+self.airac+".sct2"
        self.filename = filename+"_"+self.airac+self.modver+".sct2"
        self.airports = self.initairports()
        # Every ICAO key will correspond to coordinates from the AIRPORT section
        # This is used to exclude existing labels for airports that have new labels defined
        self.airportcoords = {}
        # Keep track of which colors are used
        # Only these will be added to the final file
        self.usedcolors = []
        # Subsections so we can remember the order
        self.sidsubs = []
        self.starsubs = []
        self.subsecs = {"sid": {}, "star": {}}
        self.sections = self.getsections()

    def initairports(self):
        if self.sector == "ZSE":
            # ZSE will include everything
            airports = [i for i in self.aptsectors]
        else:
            # Only pick out new airports in this sector
            airports = [apt for apt, asector in self.aptsectors.items() if asector == self.sector]
        return airports

    def getsections(self):
        sections = {}
        # Reads file into sections
        # Start with laying out the sct2 sections
        for key in self.stdsections:
            sections[key] = ""
        # Track which section we're in
        currsec = "header"
        subsec = ''
        secfilepath = self.directory / self.masterfilename
        # Open sector file and iterate through the lines
        f = open(secfilepath, 'r')
        for line in f:
            # Build the airport coordinates dictionary
            # This is used to exclude labels around airports with new ones
            if currsec == "airport":  # do this first so we skip the header line
                # WY67 000.000 N041.47.21.809 W110.32.30.609
                # Split by spaces, remove blanks/newline
                elems = [i for i in line.strip().split(' ') if i != '']
                # print(elems)
                # 0 for empty line, 1 for next header
                # Could test only for >3 but would like to investigate if it's in between
                if len(elems) > 1:
                    # Convert to decimal degrees
                    dcoords = dmstodd([elems[2], elems[3]])
                    # Add airport and coords to dict
                    self.airportcoords[elems[0]] = dcoords
            elif currsec == "regions":
                if re.search(r'^[ \t]+N\d{3}', line) is None:
                    elems = [i for i in re.sub(r";.+", '', line).strip().split(' ') if i != '']
                    if len(elems) > 2:
                        color = elems[0].lower()
                        if color in self.deccolors or re.search(r'^\d{,8}$', color) is not None:
                            if color not in self.usedcolors:
                                self.usedcolors.append(color)
                        else:
                            print(elems)
                            print("Color not found: "+color)
                            # for i in range(5):
                            #     print(str(i)+": "+elems[i])
            else:
                elems = [i for i in re.sub(r";.+", '', line).strip().split(' ') if i != '']
                # Add colors to used colors list
                if len(elems) > 4 and re.search(r'^N\d{3}', elems[0]) is not None:
                    color = elems[4].lower()
                    if color in self.deccolors or re.search(r'^\d{,8}$', color) is not None:
                        if color not in self.usedcolors:
                            self.usedcolors.append(color)
                    else:
                        print(elems)
                        print("Color not found: "+color)
                        # for i in range(5):
                        #     print(str(i)+": "+elems[i])
            # See if we've made it to the colors section
            # These colors aren't used right now as they're applied from the main list as used
            if re.search("^#define", line) is not None:
                currsec = "colors"
                # elems=[i for i in line.strip().split(' ') if i!='']
                # #print(elems)
                # if len(elems)>2:
                #     colordict[elems[1]]=[elems[2],0]
            # Otherwise we're in the thick of it, see if we're starting a new section
            elif currsec != "headers":
                for key in sections.keys():
                    # see if the line is [SECTION]
                    if re.search(r"^\["+key.upper()+r"\]", line) is not None:
                        currsec = key
                        # If we just switched from SID to STAR, we need to blank this out until we get the next one
                        subsec = ""
                        break
            # Break SID and STAR down into subsections
            # TODO: Search for actual headers, not just ( and =
            # We only really care about certain ones though
            if currsec in ["sid", "star"]:
                # Search for the headers in parens
                resub = re.search(r"^[=\(]+([^=]+)[=\)]+", line)
                # If either of these matches, start a new section
                if resub is not None:
                    subsec = resub[1]  # Get name of subsection
                    if currsec == "sid":
                        self.sidsubs.append(subsec)
                    elif currsec == "star":
                        self.starsubs.append(subsec)
                    # print("New subsec: "+subsec)
                    self.subsecs[currsec][subsec] = line  # Add the header line to it
                elif subsec != "":  # if no new section but we are in one
                    # print("Adding to "+currsec+" -> "+subsec)
                    self.subsecs[currsec][subsec] += line
                sections[currsec] += line  # write to the main list too
            else:  # Any other random line
                subsec = ""  # Just in case
                sections[currsec] += line
        # Add sections for the new diagrams
        aptsubi = self.sidsubs.index("Airports")
        fakecoords = "N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000\n"
        cdsec = "(Current Diagrams)"
        refsec = "(Old Diagram REF)"
        currhdr = "\n"+cdsec.ljust(27)+fakecoords
        refhdr = "\n"+refsec.ljust(27)+fakecoords
        self.sidsubs.insert(aptsubi+1, refsec)
        self.sidsubs.insert(aptsubi+1, cdsec)
        self.subsecs["sid"][cdsec] = currhdr
        self.subsecs["sid"][refsec] = refhdr
        return sections

    def addnewdiagrams(self, newlayouts):
        newaptlbls = []
        newlabels = ""
        newlines = ""
        newreflines = ""
        # print(newlayouts)
        for apt, diag in newlayouts.items():
            if apt in self.airports:
                if diag.apdlines != {}:
                    newaptlbls.append(apt)
                    newlines += ";"+apt+"\n"
                    # print(";"+airport)
                    for color, coords in diag.apdlines.items():
                        # print("COLOR: "+color)
                        if color not in self.usedcolors:
                            self.usedcolors.append(color)
                        for coordlist in coords:
                            # print("Coord: "+str(coordlist[0])+" "+str(coordlist[1]))
                            # Keep last coord to tie lines together
                            lastcoord = ""
                            for line in coordlist:
                                cstr = ddtodms(line[0], line[1])
                                # Skip first point so we can get next one too
                                if lastcoord != "":
                                    if color in self.deccolors.keys():  # or color in colordict.keys():
                                        # if color in colordict:
                                        #     colordict[color][1]=1
                                        line = "%s %s %s" % (lastcoord, cstr, color)
                                        newlines += " "+line+"\n"
                                        # print(line)
                                    else:
                                        print("  Color not found at "+apt+": "+color)
                                lastcoord = cstr
                if diag.labels != {}:
                    newlabels += "\n;"+apt+"\n"
                    # print(";"+airport)
                    for color, lbls in diag.labels.items():
                        # print(color)
                        if color not in self.usedcolors:
                            self.usedcolors.append(color)
                        for point in lbls:
                            if color in self.deccolors.keys():  # or color in colordict.keys():
                                # print(point)
                                #  if color in colordict:
                                #     colordict[color][1]=1
                                cstr = ddtodms(point[1], point[2])
                                newlabels += '"'+point[0]+'" '+cstr+" "+color+"\n"
                                # print(' "'+point[0]+'" '+cstr)
                            else:
                                print("  Color not found at "+apt+": "+color)
                if diag.reflines != {}:
                    newreflines += "\n;"+apt+" - REF\n"
                    # print("Adding ref lines for: "+apt)
                    # print(";"+airport)
                    for color, coords in diag.reflines.items():
                        if color not in self.usedcolors:
                            self.usedcolors.append(color)
                        # print("COLOR: "+color)
                        for coordlist in coords:
                            # Keep last coord to tie lines together
                            # print("New coords list")
                            lastcoord = ""
                            for line in coordlist:
                                # print("Coord: "+str(line[0])+" "+str(line[1]))
                                cstr = ddtodms(line[0], line[1])
                                # Skip first point so we can get next one too
                                if lastcoord != "":
                                    if color in self.deccolors.keys():  # or color in colordict.keys():
                                        # if color in colordict:
                                        #     colordict[color][1]=1
                                        line = "%s %s %s" % (lastcoord, cstr, color)
                                        newreflines += " "+line+"\n"
                                        # print(line)
                                    else:
                                        print("  Color not found at "+apt+": "+color)
                                lastcoord = cstr
                # else:
                    # print("No ref lines for: "+apt)
        self.subsecs["sid"]["(Current Diagrams)"] += "\n"+newlines
        self.subsecs["sid"]["(Old Diagram REF)"] += "\n"+newreflines
        self.prunelabels(newaptlbls)
        self.sections["labels"] += "\n"+newlabels

    def prunelabels(self, newlabels):
        # Don't keep labels around airports we have new labels for
        # String to hold the lines we keep
        keptlines = ""
        # Print out the names and locations of airports to prune, mostly for debug
        for newapt in newlabels:
            coords = self.airportcoords[newapt]
            print("  Will prune for %s: %f,%f" % (newapt, coords[0], coords[1]))
        # Actually prune all labels lines
        for line in self.sections["labels"].split('\n'):
            # reicao=re.search("^;.+K[A-Z0-9]{3}",line)
            # if reicao is not None:
            #   print("Found airport labels for: "+line)
            # See if line looks like a label
            relbl = re.search('^".+" +[NS]', line)
            if relbl is not None:
                # print("Found label: "+line)
                # Split by spaces and remove spaces/newline
                lblpre = [i for i in line.strip().split('"') if i != '']
                postelems = [i for i in lblpre[1].strip().split(' ') if i != '']
                # print(lblpre)
                # print(postelems)
                lblelems = ['"'+lblpre[0]+'"']
                lblelems.extend(postelems)
                # Convert coords to decimal
                # print(lblelems)
                prune = 0
                if len(lblelems) > 1:
                    color = lblelems[3].lower()
                    if color in self.deccolors or re.search(r'^\d{,8}$', color) is not None:
                        if color not in self.usedcolors:
                            self.usedcolors.append(color)
                    else:
                        print(lblelems)
                        print("Color not found: "+color)
                    lblcoords = dmstodd((lblelems[1], lblelems[2]))
                    # Check against new airports
                    for newapt in newlabels:
                        # Calculate distance of label from airport
                        dist = cosinedist(self.airportcoords[newapt], lblcoords)
                        # Prune if distance less than theshold
                        # 3 seems to just exclude our closest cases while accounding for large fields
                        # Could possibly be smaller
                        # Another way to do this would be to draw exclusion zones around each airport like X-Plane does
                        if dist < 3:
                            # print("Pruning line for "+newapt+": "+line)
                            prune = 1
                            break
                        # if dist<8:
                            # print(dist)
                    # if prune:
                        # print("Pruning for "+newapt+":"+line)
                # else:
                #     print("Bad elements: "+str(lblelems))
                # elems=[i for i in line.strip().split(' ') if i!='']
                if not prune:
                    keptlines += line+"\n"  # Keep anything not pruned
        # Rewrite labels section to just be the lines we kept
        self.sections["labels"] = "[LABELS]\n"+keptlines

    def write(self):
        print("Writing new file...")
        newfile = self.directory / self.filename
        # Build new sector file
        with open(newfile, "w") as newsct:
            # Write each section
            for key, contents in self.sections.items():
                # Handle special cases first
                if key == "info":
                    lines = contents.split('\n')
                    lines[1] = lines[1]+self.modver
                    contents = '\n'.join(lines)
                if key == "colors":
                    # print("Writing: "+key)
                    # Write existing colors
                    # newsct.write(contents)
                    # Write new colors
                    # for name,deccolor in deccolors.items():
                    #    newsct.write("#define "+name+" "+str(deccolor)+"\n")
                    for color in self.usedcolors:
                        if re.search(r'^\d{,8}$', color) is not None:
                            dcolor = color
                        else:
                            dcolor = str(self.deccolors[color])
                        newsct.write("#define "+color+" "+dcolor+"\n")
                elif key == "sid":
                    # Need to insert new diagrams
                    # Write header first
                    newsct.write("[SID]\n")
                    # Go through the subsections
                    for sub in self.sidsubs:
                        newsct.write(self.subsecs["sid"][sub])
                elif key == "labels":
                    newsct.write(contents)
                else:  # Business as usual
                    # print("Writing: "+key)
                    newsct.write(contents)
                newsct.write("\n\n")


def ddtodms(lat, lon):
    # Convert decimal degrees to the sct2 format of [NSEW]DDD.MM.SS.SSS
    # First get the NSEW directions
    if lat > 0:
        latdir = "N"
    else:
        latdir = "S"
    if lon > 0:
        londir = "E"
    else:
        londir = "W"
    # Take out any negatives
    lat = abs(lat)
    lon = abs(lon)
    # Round down to integers
    latdeg = int(lat)
    londeg = int(lon)
    # Get minutes
    latdmin = (lat-latdeg)*60
    londmin = (lon-londeg)*60
    # Get seconds
    latdsec = (latdmin - int(latdmin))*60
    londsec = (londmin - int(londmin))*60
    # Assemble the strings
    latstr = "%s%03.f.%02.f.%06.3f" % (latdir, latdeg, int(latdmin), latdsec)
    lonstr = "%s%03.f.%02.f.%06.3f" % (londir, londeg, int(londmin), londsec)
    # Return the lat lon pair in VRC format
    coordstr = latstr + " " + lonstr
    return coordstr


def cosinedist(coord1, coord2):  # Use cosine to find distance between coordinates
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dellamb = math.radians(lon2-lon1)
    R = 3440.06479  # Nmi
    # gives d in Nmi
    d = math.acos(math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb)) * R
    return d


def dmstodd(clist):
    # ["N000.00.00.000","E000.00.00.000"]
    # Get the letters
    latletter = clist[0][:1]
    lonletter = clist[1][:1]
    # Start with positive/negative based on letters
    declat = 1 if latletter == "N" else -1
    declon = 1 if lonletter == "E" else -1
    # print(clist)
    # Split by decimals, exclude leading letters
    latelems = clist[0][1:].split('.')
    lonelems = clist[1][1:].split('.')
    # print(latelems)
    # print(lonelems)
    # Calculate decimal degrees
    # Multiply by itself which was set above as positive/negative by letter
    # print(latelems)
    # print(lonelems)
    declat *= int(latelems[0])+int(latelems[1])/60+float(latelems[2]+"."+latelems[3])/3600
    declon *= int(lonelems[0])+int(lonelems[1])/60+float(lonelems[2]+"."+lonelems[3])/3600
    return (declat, declon)
