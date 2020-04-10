import os
import sys
import argparse
import xml.etree.ElementTree as ET
from fractions import Fraction

if not (sys.version_info.major == 3 and sys.version_info.minor >= 5):
    print("convert-dlmt-to-svg requires Python 3.5 or higher!")
    print("You are using Python {}.{}.".format(sys.version_info.major, sys.version_info.minor))
    sys.exit(1)

parser = argparse.ArgumentParser(description = 'Convert a Dalmatian Mask Tape media')
parser.add_argument("-f", "--file", help="The dlmt file to convert.", required = True)
parser.add_argument("-e", "--export-svg", help="Specify the filename for SVG export.", required = True)
# parser.add_argument("-H", "--export-height", help="The height of generated bitmap in pixels.", required = True)
parser.add_argument("-W", "--width", help="The width of generated bitmap in pixels.", required = True)
parser.add_argument("-v", "--view", help="The view id to export.", required = True)
args = parser.parse_args()

def fmtFract(fraction):
    return format(float(fraction), '.3f')

def normLines(lines):
    return [line.strip() for line in lines if line.strip() != ""]

def stripUnknown(expected, lines):
    return [line for line in lines if expected in line]

# system cartesian right-dir + up-dir - origin-x 1/2 origin-y 1/3
def parseCoordinateSystem(line):
    systemKey, cartesianKey, rightDirKey, rightDir, upDirKey, upDir, originXKey, originX, originYKey, originY = line.split()
    assert systemKey == "system", line
    assert cartesianKey == "cartesian", line
    assert rightDirKey == "right-dir", line
    assert upDirKey == "up-dir", line
    assert originXKey == "origin-x", line
    assert originYKey == "origin-y", line

    return {
        "right-dir": rightDir,
        "up-dir": upDir,
        "origin-x": originX,
        "origin-y": originY  
    }

def parsePrefixes(str):
    return set(normLines(str.replace("[", "").replace("]", "").split(",")))

def parseHeader(content):
    lines = content.splitlines()
    section = lines[0]
    otherLines = stripUnknown(":", normLines(lines[1:]))
    if not "section header" in section:
        print("Expected header section but got {}".format(section))
        sys.exit(1)
    headers = { i.split(":", 1)[0].strip() : i.split(":", 1)[1].strip() for i in otherLines }
    assert "page-coordinate-system" in headers, "page-coordinate-system is missing"
    assert "page-ratio" in headers, "page-coordinate-system is missing"
    assert "brush-coordinate-system" in headers, "brush-coordinate-system"
    assert "brush-ratio" in headers, "brush-ratio is missing"
    assert "brush-page-ratio" in headers, "brush-page-ratio"
    assert "prefixes" in headers, "prefixes"
    headers['page-coordinate-system'] = parseCoordinateSystem(headers['page-coordinate-system'])
    headers['brush-coordinate-system'] = parseCoordinateSystem(headers['brush-coordinate-system'])
    headers['prefixes'] = { prefix.split()[0]: prefix.split()[1] for prefix in parsePrefixes(headers['prefixes'])}
    headers['page-ratio'] = Fraction(headers['page-ratio'])
    headers['brush-ratio'] = Fraction(headers['brush-ratio'])
    headers['brush-page-ratio'] = Fraction(headers['brush-page-ratio'])
    return headers

def parseView(line):
    other, description  = line.split("->")
    cmd, viewId, langKey, langId, xyKey, x, y, widthKey, width, heightKey, height = other.split()
    assert cmd == "view", line
    assert langKey == "lang", line
    assert xyKey == "xy", line
    assert widthKey == "width", line
    assert heightKey == "height", line

    return {
        "id": viewId,
        "description": description,
        "lang": langId,
        "x": Fraction(x),
        "y": Fraction(y),
        "width": Fraction(width),
        "height": Fraction(height)       
    }

def parseViews(content):
    lines = normLines(content.splitlines())
    section = lines[0]
    otherLines = stripUnknown("->", lines[1:])
    if not "section views" in section:
        print("Expected views section but got {}".format(section))
        sys.exit(1)
    views =  { parseView(line)['id'] : parseView(line) for line in otherLines }
    return views

def parseSameAs(str):
    return list(normLines(str.replace("[", "").replace("]", "").split(",")))

def parseTagDescription(line):
    other, description  = line.split("->")
    cmd, descId, langKey, langId, sameAsKey, sameAsInfo = other.split(" ",5)
    assert cmd == "tag", line
    assert langKey == "lang", line
    assert sameAsKey == "same-as", line

    return {
        "id": descId,
        "description": description,
        "lang": langId,
        "same-as": parseSameAs(sameAsInfo)  
    }

def idLang(obj):
    return obj['id']+" "+obj['lang']

def parseTagDescriptions(content):
    lines = normLines(content.splitlines())
    section = lines[0]
    otherLines = stripUnknown("->", lines[1:])
    if not "section tag-descriptions" in section:
        print("Expected tag-descriptions section but got {}".format(section))
        sys.exit(1)
    views = { idLang(parseTagDescription(line)): parseTagDescription(line) for line in otherLines }
    return views

def parseVectorialPath(str):
    return normLines(str.replace("[", "").replace("]", "").split(","))

def parseBrush(line):
    cmd, brushId, extIdKey, extId, pathKey, other = line.split(" ", 5 )
    assert cmd == "brush", line
    assert extIdKey == "ext-id", line
    assert pathKey == "path", line
    return {
        "id": brushId,
        "ext-id": extId,
        "path": parseVectorialPath(other)
    }

def parseBrushes(content):
    lines = normLines(content.splitlines())
    section = lines[0]
    otherLines = stripUnknown("[", lines[1:])
    if not "section brushes" in section:
        print("Expected brushes section but got {}".format(section))
        sys.exit(1)
    views = { parseBrush(line)['id']: parseBrush(line) for line in otherLines }
    return views


def parseTags(str):
    return set(normLines(str.replace("[", "").replace("]", "").split(",")))

def parseBrushStroke(line):
    cmd, brushId, xyKey, x, y, scaleKey, scale, angleKey, angle, tagsKey, tagsInfo = line.split(" ", 10 )
    assert cmd == "brushstroke", line
    assert xyKey == "xy", line
    assert scaleKey == "scale", line
    assert angleKey == "angle", line
    assert tagsKey == "tags", line
    return {
        "brush-id": brushId,
        "x": Fraction(x),
        "y": Fraction(y),
        "scale": Fraction(scale),
        "angle": Fraction(angle),
        "tags": parseTags(tagsInfo)
    }

def parseBrushStrokes(content):
    lines = normLines(content.splitlines())
    section = lines[0]
    otherLines = lines[1:]
    if not "section brushstrokes" in section:
        print("Expected brushstrokes section but got {}".format(section))
        sys.exit(1)
    views = [ parseBrushStroke(line) for line in otherLines ]
    return views

def getTagIds(tagDesc):
    return set([key.split()[0] for key in tagDesc])

def loadDalmatian(filename):
    with open(filename, 'r') as myfile:
        data = myfile.read()
        header, views, tagDescriptions, brushes, brushstrokes = data.split('--------')
        tagDesc = parseTagDescriptions(tagDescriptions)
        return {
            'header': parseHeader(header),
            'views': parseViews(views),
            'tag-descriptions': tagDesc,
            'tag-ids': getTagIds(tagDesc),
            'brushes': parseBrushes(brushes),
            'brushstrokes': parseBrushStrokes(brushstrokes)
        }

def checkReferences(everything, viewId):
    tagIds = everything['tag-ids']
    brushIds = set(everything['brushes'].keys())
    prefixes = set(everything['header']['prefixes'].keys())
    for _, tagDesc in everything['tag-descriptions'].items():
        for sameAs in tagDesc['same-as']:
            assert sameAs.split(':')[0] in prefixes, sameAs
    
    for _, brush in everything['brushes'].items():
        assert brush['ext-id'].split(':')[0] in prefixes, brush
    
    for brushstroke in everything['brushstrokes']:
        assert brushstroke['brush-id'] in brushIds, brushstroke
        assert brushstroke['tags'].issubset(tagIds), brushstroke
    
    assert viewId in everything['views'], 'missing view {}'.format(viewId)

class CoordinateSystem:
    def __init__(self, sectionHeader, width):
        self.header = sectionHeader
        self.pageCoord = sectionHeader['page-coordinate-system']
        self.brushCoord = sectionHeader['brush-coordinate-system']
    
    def toDeg(self, fraction):
        return fmtFract(360 * fraction)
    
    def toScale(self, fraction):
        return fmtFract(fraction)

    def toPageX(self, fraction):
        self.pageCoord['origin-x']
        return fmtFract(fraction)

    def toPageY(self, fraction):
        self.pageCoord['origin-y']
        return fmtFract(fraction)

    def toBrushX(self, fraction):
        self.brushCoord['origin-x']
        return fmtFract(fraction)

    def toBrushY(self, fraction):
        self.brushCoord['origin-y']
        return fmtFract(fraction)

def asSvgBrushId(id):
    return id.replace('i:', 'brush')

def createSvgBrush(brush, coordSystem):
    symbol = ET.Element('symbol', attrib = {"id": asSvgBrushId(brush['id']), "viewBox": "0 0 100 600"})
    ET.SubElement(symbol, 'path', attrib = { "d": "M0,10 h80 M10,0 v20 M25,0 v20 M40,0 v20 M55,0 v20 M70,0 v20"})
    return symbol

def createSvgBrushStroke(brushstroke, coordSystem):
    rotation = coordSystem.toDeg(brushstroke['angle'])
    scale = coordSystem.toScale(brushstroke['scale'])
    translation = coordSystem.toPageX(brushstroke['x']) + ' ' + coordSystem.toPageY(brushstroke['y'])
    element = ET.Element('g', attrib = {"transform": "rotate ({}) scale ({}) translate({})".format(rotation, scale, translation)})
    ET.SubElement(element, 'use', attrib = { "fill": "black", "xlink:href": '#'+asSvgBrushId(brushstroke['brush-id'])})
    return element

def createSvgDocument(everything, viewId, width):
    coordSystem = CoordinateSystem(everything['header'], width)
    svg = ET.Element('svg')
    for _, brush in everything['brushes'].items():
        svg.append(createSvgBrush(brush, coordSystem))
    for brushstroke in everything['brushstrokes']:
        svg.append(createSvgBrushStroke(brushstroke, coordSystem))
    return ET.dump(svg)

dlmtContent = loadDalmatian(args.file)

checkReferences(dlmtContent, args.view)
createSvgDocument(dlmtContent, args.view, args.width)
