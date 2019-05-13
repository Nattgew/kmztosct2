#!/usr/bin/env python

# Hardcoded color names in hex
# This is the master list of colors to choose from
defaultcolors = {
    "apron": "#808080",
    "Aqua": "#00ffff",
    "background": "#000000",
    "Black": "#000000",
    # "blastpad": "#ffff00",
    "Blue": "#0000ff",
    "building": "#ff0000",
    "BuildingTerminalLabels": "#408080",
    "centerline": "#606060",
    "classB": "#004080",
    "classC": "#800080",
    "classD": "#003060",
    "classEsfc": "#400040",
    "closed": "#ff0000",
    "COLOR_AirspaceA": "#008080",
    "COLOR_AirspaceB": "#008080",
    "COLOR_AirspaceC": "#008080",
    "COLOR_AirspaceD": "#008080",
    "COLOR_AirspaceE": "#008080",
    "COLOR_AirspaceF": "#800080",
    "COLOR_AirspaceG": "#008080",
    "COLOR_AoRapproach1": "#0000ff",
    "COLOR_AoRapproach2": "#ff8000",
    "COLOR_AoRapproach3": "#910546",
    "COLOR_AoRapproach4": "#7e7e7e",
    "COLOR_AoRapproach5": "#7e7e7e",
    "COLOR_AoRcenter1": "#646464",
    "COLOR_AoRcenter2": "#422100",
    "COLOR_AoRcenter3": "#7e7e7e",
    "COLOR_AoRcenter4": "#7e7e7e",
    "COLOR_AoRcenter5": "#7e7e7e",
    "COLOR_AoRdeparture1": "#808000",
    "COLOR_AoRdeparture2": "#7e7e7e",
    "COLOR_AoRground1": "#800000",
    "COLOR_AoRground2": "#008000",
    "COLOR_APP": "#0000ff",
    "COLOR_Building": "#808080",
    "COLOR_Centerlines": "#a6d90c",
    "COLOR_ClosureArea": "#ff0000",
    "COLOR_Coastline": "#0000ff",
    "COLOR_DangerArea": "#800000",
    "COLOR_FIRBorder": "#808080",
    "COLOR_GrasSurface": "#003200",
    "COLOR_GroundlayerGras": "#202a30",
    "COLOR_HardSurface1": "#5a5648",
    "COLOR_HardSurface2": "#636363",
    "COLOR_Holding": "#800000",
    "COLOR_Landmark1": "#7e7e7e",
    "COLOR_Landmark2": "#7e7e7e",
    "COLOR_Landmark3": "#7e7e7e",
    "COLOR_Landmark4": "#7e7e7e",
    "COLOR_Landmark5": "#7e7e7e",
    "COLOR_MRVA1": "#68540d",
    "COLOR_MRVA2": "#443708",
    "COLOR_ParkPos": "#008000",
    "COLOR_ParkPosUnused": "#800000",
    "COLOR_Releaseline": "#008000",
    "COLOR_RestrictedArea": "#800000",
    "COLOR_RMZ": "#800080",
    "COLOR_RunwayConcrete": "#808080",
    "COLOR_RunwayGrass": "#008000",
    "COLOR_SID": "#00ff00",
    "COLOR_STAR": "#ff0000",
    "COLOR_Stopbar": "#ff0000",
    "COLOR_TACAN-Route": "#004080",
    "COLOR_Taxiway": "#c0b631",
    "COLOR_TaxiwayBlue": "#004080",
    "COLOR_TaxiwayBorder": "#0000ff",
    "COLOR_TaxiwayGreen": "#008000",
    "COLOR_TaxiwayOrange": "#ffa500",
    "COLOR_TMA": "#000000",
    "COLOR_TMZ": "#800000",
    "COLOR_TWR-CTR": "#000000",
    "COLOR_UpperSector": "#422100",
    "COLOR_Vectors": "#000000",
    "COLOR_VFR-Route": "#000000",
    "COLOR_Water": "#004080",
    "Fuchsia": "#ff00ff",
    "Gray": "#808080",
    "Green": "#008000",
    # "helipad": "#ff8000",
    "HoldShort": "#ffff00",
    "ILSHoldShort": "#ffff9f",
    "interstate": "#400040",
    "Lawngreen": "#7cfc00",
    "Lime": "#00ff00",
    "Maroon": "#800000",
    "mea": "#3f3f3f",
    "MIA_Color": "#3f3f3f",
    "mountain": "#ff8000",
    "mva": "#3f3f3f",
    "Navy": "#000080",
    "NonMovementAreaBoundary": "#53afc4",
    "Olive": "#808000",
    "Orange": "#ff8000",
    "Purple": "#800080",
    "ramp": "#808080",
    "RampLabels": "#808040",
    "Red": "#ff0000",
    "river": "#000030",
    "runway": "#00ffff",
    "RunwayEdge": "#00ffff",
    "runwaymarks": "#ffff00",
    "sector": "#408040",
    "sector2": "#008000",
    "sector3": "#008080",
    "SectorLabel": "#800080",
    "Silver": "#c0c0c0",
    "split": "#313131",
    "state": "#a08080",
    "taxi": "#0000ff",
    "taxiway": "#0000ff",
    "TaxiwayEdge": "#0000ff",
    "TaxiwayLabel": "#ffffff",
    "Teal": "#008080",
    "tracon": "#006633",
    "water": "#000030",
    "White": "#ffffff",
    "Yellow": "#ffff00",
    "ZSE_MIA": "#800080",
    "taxiOld": "#ff00ff",
    'displacedthreshold': "#ffffff",  # Following are for new diagrams
    'helipad': "#ffaa00",
    'taxilane_labels': "#85c562",
    'twyrwy_labels': "#ffffff",
    'blastpad': "#ffff7f",
    'holdshort': "#ffff00",
    'movementarea': "#aaffff",
    'oldtaxiway': "#ff55ff",
    'taxilane': "#00aaff",
    'ramp_labels': '#808040',
    'building_labels': '#408080',
    'blast': '#ffff7f',
    'runwaylabel': "#ffffff",
    "txyrwy_labels": "#ffffff"
}


def getcolors(hexcolors=defaultcolors):
    # Create new dict for decimal colors
    deccolors = {}
    # Multiply colors by this to increase/decrease brightness
    derate = 1
    # Convert all the hex colors to the VRC format
    for name, hexcolor in hexcolors.items():
        # Get rid of the leading #
        straighthex = hexcolor.replace("#", '')
        # Split hex into R G B with 0x for conversion
        hexrgb = ["0x"+straighthex[i:i+2] for i in range(0, len(straighthex), 2)]
        # Convert each to int
        decred = int(int(hexrgb[0], 0)*derate)
        decgrn = int(int(hexrgb[1], 0)*derate)
        decblu = int(int(hexrgb[2], 0)*derate)
        # Cap at 255 in increasing brightness
        decred = decred if decred < 256 else 255
        decgrn = decgrn if decgrn < 256 else 255
        decblu = decblu if decblu < 256 else 255
        # Create the VRC color notation
        deccolor = decred + decgrn*256 + decblu*65536
        # Store names in lower case for key searches
        deccolors[name.lower()] = deccolor
    return deccolors

#print(colordefs)

def deccolortohtml(deccolor):
    decblu = int(deccolor/65536)
    decgrn = int((deccolor-decblu*65536)/256)
    decred = deccolor-decblu*65536-decgrn*256
    # print('"%s": "#%02x%02x%02x",' % (name, decred, decgrn, decblu))
    return "#%02x%02x%02x" % (decred, decgrn, decblu)
