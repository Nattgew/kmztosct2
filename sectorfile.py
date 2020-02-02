#!/usr/bin/env python

import math
import re
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

    def __init__(self, filename, directory, airac, modver=''):
        # Sector code is first 3 of file name
        self.sector = filename[:3]
        # Just the file name
        self.basename = filename
        # Directory containing the file
        self.directory = directory
        # Version info
        self.airac = airac
        self.modver = modver
        self.magvar = 0
        # Name of original file
        self.masterfilename = filename+"_"+self.airac+".sct2"
        # Name of modified file to be saved
        self.filename = filename+"_"+self.airac+self.modver+".sct2"
        # List of airports in this sector
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
        self.re_coord = re.compile(r'^[NS]\d{3}')
        self.re_deccolor = re.compile(r'^\d{,8}$')
        self.sections = self.getsections()

    def initairports(self):
        if self.sector == "ZSE":
            # ZSE will include everything
            airports = [i for i in self.aptsectors]
        else:
            # Only pick out new airports in this sector
            airports = [apt for apt, asector in self.aptsectors.items() if asector == self.sector]
        return airports

    def usedcolor(self, color):
        # Add new color to list of used colors
        if color in self.deccolors or self.re_deccolor.search(color) is not None:
            if color not in self.usedcolors:
                self.usedcolors.append(color)
        else:  # Warn if color is not defined
            print("Color not found: "+color)
            # for i in range(5):
            #     print(str(i)+": "+elems[i])

    def getsections(self):
        # Reads file into sections
        # Start with laying out the sct2 sections
        sections = {}
        kres = {}
        for key in self.stdsections:
            sections[key] = []
            skey = "["+key.upper()+"]"
            kres[key] = [skey, len(skey)]
        # Track which section we're in
        currsec = "header"
        subsec = ''
        secfilepath = self.directory / self.masterfilename
        infosec = 0
        # Open sector file and iterate through the lines
        with open(secfilepath, 'r') as f:
            for line in f:
                line = line.rstrip()
                # Build the airport coordinates dictionary
                # This is used to exclude labels around airports with new ones
                if currsec == "airport":  # do this first so we skip the header line
                    # WY67 000.000 N041.47.21.809 W110.32.30.609
                    # Split by spaces, remove blanks/newline
                    elems = [i for i in line.split(' ') if i]
                    # length 0 for empty line, 1 for next header
                    # Could test only for >3 but would like to investigate if it's in between
                    if len(elems) > 1:
                        # Convert to decimal degrees
                        # Add airport and coords to dict
                        self.airportcoords[elems[0]] = dmstodd([elems[2], elems[3]])
                # Add colors to used colors list
                # Start with regions section as it's unique
                elif currsec == "regions":
                    if self.re_coord.search(line) is None:
                        elems = [i for i in line.split(';')[0].split(' ') if i]
                        if len(elems) > 2:
                            self.usedcolor(elems[0].lower())
                elif currsec == "info":
                    infosec += 1
                    if infosec == 8:
                        self.magvar = float(line)
                        print("Magvar: "+str(self.magvar))
                # Handle other sections
                else:
                    elems = [i for i in line.split(';')[0].split(' ') if i]
                    # Add colors to used colors list
                    if len(elems) > 4 and self.re_coord.search(elems[0]) is not None:
                        self.usedcolor(elems[4].lower())

                # See if we've made it to the colors section
                # These colors aren't used right now as they're applied from the main list as used
                if line[:7] == "#define":
                    currsec = "colors"
                    # elems=[i for i in line.split(' ') if i]
                    # print(elems)
                # Otherwise we're in the thick of it, see if we're starting a new section
                elif currsec != "headers" and line[:1] == "[":
                    for key in sections.keys():
                        # see if the line is [SECTION]
                        if line[:kres[key][1]] == kres[key][0]:
                            currsec = key
                            # print("Entered section: "+key)
                            # If we just switched from SID to STAR, we need to blank this out until we get the next one
                            subsec = ""
                            break

                # Break SID and STAR down into subsections
                # We only really care about certain ones though
                if currsec in ["sid", "star"]:
                    # Search for the headers, start a new section
                    ochar = line[:1]
                    if ochar != " " and ochar != ";" and ochar != "\n":
                        subsec = line[:26].strip()  # Get name of subsection
                        if currsec == "sid":
                            self.sidsubs.append(subsec)
                        elif currsec == "star":
                            self.starsubs.append(subsec)
                        # print("New subsec: "+subsec)
                        self.subsecs[currsec][subsec] = [line]  # Add the header line to it
                    elif subsec:  # if no new section but we are in one
                        # print("Adding to "+currsec+" -> "+subsec)
                        self.subsecs[currsec][subsec].append(line)
                    sections[currsec].append(line)  # write to the main list too
                else:  # Any other random line
                    subsec = ""  # Just in case
                    sections[currsec].append(line)

        # Index of Airports section in the list of SID subsections
        self.aptsubi = self.sidsubs.index("(Airports)")

        return sections

    def addsubsec(self, name):
        # Add a new subsection to the diagrams
        # Section for new diagrams
        # TODO: truncate to max length
        sectionname = "("+name+")"
        if sectionname not in self.subsecs["sid"]:
            print("  Adding subsec: "+name)
            # VRC wants this at the end of header lines
            fakecoords = "N000.00.00.000 E000.00.00.000 N000.00.00.000 E000.00.00.000\n"
            # Create full header lines
            # Header name is first 26 characters
            rhdr = "\n"+sectionname.ljust(27)+fakecoords
            # Insert these sections into to the subsection list after Airports
            self.sidsubs.insert(self.aptsubi+1, sectionname)
            # Initialize these subsections with the headers
            # addnewdiagrams() will put new content here
            self.subsecs["sid"][sectionname] = [rhdr]

    def coordlisttolines(self, coordlist, color):
        # Convert a list of coordinates to lines
        # Each lines starts with end point of previous line
        # Keep last coord to tie lines together
        # print("New coords list")
        lastcoord = ""
        for coord in coordlist:
            # Get DMS of these coordinates
            thiscoord = ddtodms(coord[0], coord[1])
            # Skip first point so we can get next one too
            if lastcoord:
                if color in self.deccolors.keys():
                    line = " %s %s %s" % (lastcoord, thiscoord, color)
                    yield line
                    # print(line)
                else:
                    print("  Color not found: "+color)
            lastcoord = thiscoord

    def dashline(self, coords, color, dashlen):
        # Assume we just get two coords for now
        totaldist = cosinedist(coords[0], coords[1])
        dashes = int(totaldist/dashlen)
        brng = math.radians(coordbrng(coords[0], coords[1]))
        # print("Would make %i dashes over %.2f nmi hdg %.2f" % (dashes, totaldist, brng))
        # See if we'd end on an extra long empty space
        if not dashes % 2:
            actualdashes = dashes-1
            # Get amount of empty space at the end
            deficit = totaldist-dashlen*actualdashes
            # Split this on both sides of the line
            lastcoord = coordbrgdist(coords[0], brng, deficit/2)
        else:
            lastcoord = coords[0]
        for i in range(dashes):
            nextcoord = coordbrgdist(lastcoord, brng, dashlen)
            # print(nextcoord)
            if i % 2 == 0:
                lastdms = ddtodms(lastcoord[0], lastcoord[1])
                nextdms = ddtodms(nextcoord[0], nextcoord[1])
                line = " %s %s %s" % (lastdms, nextdms, color)
                yield line
            lastcoord = nextcoord

    def drawcircle(self, coords, color):
        # Draws circle with center at first point, radius of length
        center = coords[0]
        radius = cosinedist(coords[0], coords[1])
        segments = 18
        increment = int(360/segments)
        lastcoord = coordbrgdist(center, 0, radius)
        for i in range(increment, 360+increment, increment):
            # print("Projecting %i deg at %.2f nmi" % (i, radius))
            nextcoord = coordbrgdist(center, math.radians(i), radius)
            lastdms = ddtodms(lastcoord[0], lastcoord[1])
            nextdms = ddtodms(nextcoord[0], nextcoord[1])
            line = " %s %s %s" % (lastdms, nextdms, color)
            yield line
            lastcoord = nextcoord

    def drawstring(self, coords, name, color, scale, magvec):
        # Draws out text in "name" using lines, aligned to magnetic vector magvec
        import freetype

        # Load the font face to use
        # Excellent single stroke - machtgth.ttf
        #face = freetype.Face('/usr/share/fonts/TTF/DejaVuSans.ttf')
        closed = 0
        defspace = scale/150
        flags = freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP
        face.set_char_size( 16*90 )
        #height = 5
        #print("Magvec: "+str(magvec))
        vector = -magvec + 90 + self.magvar
        #print("Drawing "+name+" with scale "+str(scale)+" and vector "+str(vector))
        # Draw each character
        i=0
        # print("   Printing: "+name)
        # if len(name)>3:
        #     print("   Printing: "+name)
        #     pc = 1
        # else:
        #     pc = 0
        for c in name:
            if c != " ":
                # if pc:
                #     print("    Printing: "+c)
                # print("    Printing: "+c)
                # Track the max and min to determine character witdth
                maxlen = -200
                minlen = 200
                face.load_char(c, flags)
                slot = face.glyph
                outline = slot.outline
                start = 0
                # print(outline.contours)
                # print(outline.points)
                # Loop through the points to draw lines
                for end in outline.contours:
                    lastcoord = ""
                    path = outline.points[start:end+1]
                    if outline.tags[end] == 0 or closed:
                        # print("Looping")
                        path.append(path[0])
                    #path.append(path[0])
                    for pair in path:
                        #latp, lonp = self.rotatepoint((pair[1]/10000, pair[0]/10000), self.magvar/2)
                        # Convert font coordinates to lat/lon
                        # Font points are scaled to 1000 height, divide by this to make them 1 degree lat tall
                        # Then multiply by height/60 to set height in Nm
                        newcoords = (coords[0]+pair[1]*scale/60000, coords[1]+pair[0]*scale/60000)
                        # Get distance from origin to this point
                        # print("     From: "+str(coords)+"   To: "+str(newcoords))
                        if coords != newcoords:
                            dist = cosinedist(coords, newcoords)
                        else:
                            dist = 0
                        #print(pair[1]/pair[0])
                        #brg = math.pi/2 - math.atan(pair[1]/pair[0]) - math.radians(self.magvar)
                        # Get bearing from origin to this point
                        # Correct this for magnetic variation
                        brg = math.radians(coordbrng(coords, newcoords) - vector)
                        # Project the new point accounting for the magnetic variation
                        lat, lon = coordbrgdist(coords, brg, dist)
                        #print(coords)
                        #print(dist)
                        #print(math.degrees(brg))
                        #print(lat)
                        #print(lon)
                        #lat = coords[0]+latp
                        #lon = coords[1]+lonp
                        # Track the width of the character
                        if newcoords[1] > maxlen:
                            maxlen = newcoords[1]
                        if newcoords[1] < minlen:
                            minlen = newcoords[1]
                        # Convert this coordinate for printing
                        thiscoord = ddtodms(lat, lon)
                        if lastcoord:
                            line = " %s %s %s" % (lastcoord, thiscoord, color)
                            # print(line)
                            yield line
                        lastcoord = thiscoord
                    start = end+1
                space = maxlen-minlen if maxlen-minlen > defspace else defspace
            else:
                space = defspace
            i+=1
            if i<len(name):
                #print("Spacing over by "+str(space))
                #latp, lonp = self.rotatepoint((0,1.1*(maxlen-minlen)), self.magvar/2)
                # Project origin for next character
                dist = cosinedist(coords, (coords[0], coords[1]+1.4*space))
                latp, lonp = coordbrgdist(coords, math.pi/2 - math.radians(vector), dist)
                coords = (latp, lonp)
                #print(line)
        #[(828, 128), (728, 58), (543, 0), (437, 0), (262, 0), (74, 172), (74, 307), (74, 385), (145, 515), (260, 594), (332, 614), (385, 628), (492, 641), (710, 668), (813, 704), (814, 731), (814, 738), (814, 819), (763, 851), (694, 896), (558, 896), (431, 896), (310, 840), (281, 768), (105, 768), (129, 879), (239, 1015), (447, 1088), (584, 1088), (720, 1088), (890, 1023), (970, 924), (986, 848), (995, 801), (995, 696), (995, 485), (995, 264), (1018, 83), (1052, 0), (864, 0), (836, 55), (813, 512), (715, 481), (519, 460), (408, 447), (316, 417), (266, 357), (266, 321), (266, 266), (375, 192), (480, 192), (584, 192), (746, 277), (784, 334), (813, 378), (813, 464)]

    def rotatepoint(self, coords, angle):
        angle = math.radians(angle)
        lat = coords[1] * math.sin(angle) + coords[0] * math.cos(angle)
        lon = coords[1] * math.cos(angle) - coords[0] * math.sin(angle)
        return lat, lon

    def addnewdiagrams(self, newlayouts):
        # List of airports with new labels
        # Old labels will be pruned out there
        newaptlbls = []
        # New section content with labels
        newlabels = []
        twylabels = []
        # New section content with new diagram lines
        # newlines = []
        # New section content with old diagram reference lines
        # newreflines = []
        # print(newlayouts)
        # Loop through each airport in this sector
        for apt, diag in {apt: diag for apt, diag in newlayouts.items() if apt in self.airports}.items():
            print("Adding new diagrams for: "+apt)

            for cat, objs in diag.cats.items():
                print(" Processing cat: "+cat)
                self.addsubsec(cat)
                if objs['lines']:
                    newlines = []
                    # Comment as heading for this airport's stuff
                    newlines.append(";"+apt)
                    # print(";"+airport)
                    for color, linelist in objs['lines'].items():
                        # print("COLOR: "+color)
                        if color not in self.usedcolors:
                            self.usedcolors.append(color)
                        for linestring in linelist:
                            nameelem = linestring[0].split('_')
                            name = nameelem[0]
                            coords = linestring[1]
                            desc = linestring[2]
                            if name == "dashed":
                                # We'll assume this color is already used...
                                if len(nameelem) > 1:
                                    dashlen = int(nameelem[1])/6076
                                    # print("Setting custom dash length: "+nameelem[1])
                                else:
                                    dashlen = 60/6076
                                for line in self.dashline(coords, color, dashlen):
                                    newlines.append(line)
                            elif name == "circle":
                                for line in self.drawcircle(coords, color):
                                    newlines.append(line)
                            else:
                                if desc == "plot=True":
                                    scale = cosinedist(coords[0], coords[1])
                                    vert = coordbrng(coords[0], coords[1]) + self.magvar
                                    print("Vert brg: "+str(vert))
                                    for line in self.drawstring((coords[0][0], coords[0][1]), name, color, scale, vert+90):
                                        newlines.append(line)
                                else:
                                    for line in self.coordlisttolines(coords, color):
                                        newlines.append(line)
                    self.subsecs["sid"]["("+cat+")"].extend(newlines)
                if objs['labels']:
                    # Add this to list of airports with new labels
                    newaptlbls.append(apt)
                    # Comment as heading for this airport's stuff
                    newlabels.append(";"+apt)
                    # print(";"+airport)
                    for color, lbls in objs['labels'].items():
                        # print(color)
                        if color not in self.usedcolors:
                            self.usedcolors.append(color)
                        for point in lbls:
                            if color in self.deccolors.keys():
                                # print(point)
                                if point[3] == "plot=True":
                                    for line in self.drawstring((point[1], point[2]), point[0], color, 5, 90):
                                        newlines.append(line)
                                else:
                                    cstr = ddtodms(point[1], point[2])
                                    newlabels.append('"'+point[0]+'" '+cstr+" "+color)
                                    if color == "twyrwy_labels":
                                        for line in self.drawstring((point[1], point[2]), point[0], color, .04, 90):
                                            twylabels.append(line)
                                # print(' "'+point[0]+'" '+cstr)
                            else:
                                print("  Color not found at "+apt+": "+color)
            self.addsubsec("Taxiways")
            self.subsecs["sid"]["(Taxiways)"].extend(twylabels)
            # if diag.reflines:
            #     # Comment as heading for this airport's stuff
            #     newreflines.append(";"+apt+" - REF")
            #     # print("Adding ref lines for: "+apt)
            #     # print(";"+airport)
            #     for color, coords in diag.reflines.items():
            #         if color not in self.usedcolors:
            #             self.usedcolors.append(color)
            #         # print("COLOR: "+color)
            #         for coordlist in coords:
            #             for line in self.coordlisttolines(coordlist, color):
            #                 newreflines.append(line)
            # else:
                # print("No ref lines for: "+apt)
        # Add the new content to applicable sections
        # self.subsecs["sid"]["(Current Diagrams)"].extend(newlines)
        # self.subsecs["sid"]["(Old Diagram REF)"].extend(newreflines)
        # First remove labels where we have new ones
        self.prunelabels(newaptlbls)
        # Add new labels to remaining ones
        if not self.sections["labels"]:
            self.sections["labels"] = ["[LABELS]"]
        self.sections["labels"].extend(newlabels)

    def prunelabels(self, newlabels):
        # Don't keep existing labels around airports we have new labels for
        # String to hold the lines we keep
        keptlines = []
        # Print out the names and locations of airports to prune, mostly for debug
        # for newapt in newlabels:
        #   coords = self.airportcoords[newapt]
        #   print("  Will prune for %s: %f,%f" % (newapt, coords[0], coords[1]))
        # Actually prune all labels lines
        re_lbl = re.compile('^".+" +[NS]')
        for line in self.sections["labels"]:
            # reicao=re.search("^;.+K[A-Z0-9]{3}",line)
            # if reicao is not None:
            #   print("Found airport labels for: "+line)
            # See if line looks like a label
            prune = 0
            lblelems = []
            if re_lbl.search(line) is not None:
                # print("Found label: "+line)
                # Split by spaces and remove spaces/newline
                lblpre = [i for i in line.split('"') if i]
                postelems = [i for i in lblpre[1].split(';')[0].strip().split(' ') if i]
                # print(lblpre)
                # print(postelems)
                lblelems = ['"'+lblpre[0]+'"']
                lblelems.extend(postelems)
                # Convert coords to decimal
                # print(lblelems)
                if len(lblelems) > 2:
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
                keptlines.append(line)  # Keep anything not pruned
                if len(lblelems) > 3:
                    self.usedcolor(lblelems[3].lower())
        # Rewrite labels section to just be the lines we kept
        self.sections["labels"] = keptlines

    def write(self):
        print("Writing new file...")
        newfile = self.directory / self.filename
        # Build new sector file
        with open(newfile, "w") as newsct:
            # Write each section
            for key, contents in self.sections.items():
                # Handle special cases first
                if key == "info":
                    contents[1] = contents[1]+self.modver
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
                    # Go through the subsections
                    for sub in self.sidsubs:
                        # print("Writing: "+sub)
                        # print(self.subsecs["sid"][sub])
                        for line in self.subsecs["sid"][sub]:
                            newsct.write(line+"\n")
                else:  # Business as usual
                    # print("Writing: "+key)
                    # print(contents)
                    for line in contents:
                        # print(line)
                        newsct.write(line+"\n")
                newsct.write("\n\n")


def ddtodms(lat, lon):
    # Convert decimal degrees to the sct2 format of [NSEW]DDD.MM.SS.SSS
    # First get the NSEW directions
    latdir = "N" if lat > 0 else "S"
    londir = "E" if lon > 0 else "W"
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


def cosinedist(coord1, coord2):  # Use cosine to find distance between coordinates
    # Split into lat/lon
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    # Convert latitudes to radians, get difference
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dellamb = math.radians(lon2-lon1)
    R = 3440.06479  # Nmi
    # gives d in Nmi
    d = math.acos(math.sin(phi1)*math.sin(phi2) + math.cos(phi1)*math.cos(phi2) * math.cos(dellamb)) * R
    return d


def coordbrng(coord1, coord2):  # Find heading between coordinates
    phi1 = math.radians(coord1[0])
    phi2 = math.radians(coord2[0])
    lamb1 = math.radians(coord1[1])
    lamb2 = math.radians(coord2[1])
    y = math.sin(lamb2-lamb1) * math.cos(phi2)
    x = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(lamb2-lamb1)
    brng = math.degrees(math.atan2(y, x))
    if brng < 0:
        brng += 360
    return brng


def coordbrgdist(coord, brng, dist):
    angdist = dist / 3440.06479
    phi = math.radians(coord[0])
    # lamb = math.radians(coord[1])
    # brng = coordbrng(coord1, coord2)
    lat = math.degrees(math.asin(math.sin(phi) * math.cos(angdist) + math.cos(phi) * math.sin(angdist) * math.cos(brng)))
    lon = coord[1] + math.degrees(math.atan2(math.sin(brng) * math.sin(angdist) * math.cos(phi), math.cos(angdist) - math.sin(phi) * math.sin(math.radians(lat))))
    return (lat, lon)
