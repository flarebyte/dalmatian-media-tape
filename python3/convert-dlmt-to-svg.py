import os
import sys
import argparse

if not (sys.version_info.major == 3 and sys.version_info.minor >= 5):
    print("convert-dlmt-to-svg requires Python 3.5 or higher!")
    print("You are using Python {}.{}.".format(sys.version_info.major, sys.version_info.minor))
    sys.exit(1)

parser = argparse.ArgumentParser(description = 'Convert a Dalmatian Mask Tape media')
parser.add_argument("-f", "--file", help="The dlmt file to convert.", required = True)
parser.add_argument("-e", "--export-svg", help="Specify the filename for SVG export.", required = True)
parser.add_argument("-H", "--export-height", help="The height of generated bitmap in pixels.", required = True)
parser.add_argument("-W", "--export-width", help="The width of generated bitmap in pixels.", required = True)
parser.add_argument("-v", "--view", help="The view id to export.", required = True)
args = parser.parse_args()

def normLines(lines):
    return [line.strip() for line in lines if line.strip() != ""]

def stripUnknown(expected, lines):
    return [line for line in lines if expected in line]

def parseHeader(content):
    lines = content.splitlines()
    section = lines[0]
    otherLines = stripUnknown(":", normLines(lines[1:]))
    if not "section header" in section:
        print("Expected header section but got {}".format(section))
        sys.exit(1)
    headers = { i.split(":", 1)[0].strip() : i.split(":", 1)[1].strip() for i in otherLines }
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
        "x": x,
        "y": y,
        "width": width,
        "height": height       
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
        "same-as": sameAsInfo  
    }

def idLang(obj):
    return obj['id']+"-"+obj['lang']

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
    cmd, brushId, other = line.split(" ", 2 )
    assert cmd == "brush", line
    return {
        "id": brushId,
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
    cmd, brushstrokeId, xyKey, x, y, scaleKey, scale, angleKey, angle, tagsKey, tagsInfo = line.split(" ", 10 )
    assert cmd == "brushstroke", line
    assert xyKey == "xy", line
    assert scaleKey == "scale", line
    assert angleKey == "angle", line
    assert tagsKey == "tags", line
    return {
        "id": brushstrokeId,
        "x": x,
        "y": y,
        "scale": scale,
        "angle": angle,
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

def loadDalmatianAsString(filename):
    with open(filename, 'r') as myfile:
        data = myfile.read()
        header, views, tagDescriptions, brushes, brushstrokes = data.split('--------')
        return {
            'header': parseHeader(header),
            'views': parseViews(views),
            'tag-descriptions': parseTagDescriptions(tagDescriptions),
            'brushes': parseBrushes(brushes),
            'brushstrokes': parseBrushStrokes(brushstrokes)
        }

print(loadDalmatianAsString(args.file))