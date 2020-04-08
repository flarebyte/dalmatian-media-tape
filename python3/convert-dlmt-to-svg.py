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

print(args)

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

#view i:1 lang en-gb xy 1/5 1/3 width 1/4 height 1/5 -> head
def parseView(line):
    other, description  = line.split("->")
    cmd, viewId, langKey, langId, xyKey, x, y, widthKey, width, heightKey, height = other.split()
    assert cmd == "view"
    assert langKey == "lang"
    assert xyKey == "xy"
    assert widthKey == "width"
    assert heightKey == "height"

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
    views = [parseView(line) for line in otherLines]
    return views

def loadDalmatianAsString(filename):
    with open(filename, 'r') as myfile:
        data = myfile.read()
        header, views, tagDescriptions, brushes, brushstrokes = data.split('--------')
        return {
            'headers': parseHeader(header),
            'views': parseViews(views)

        }

print(loadDalmatianAsString(args.file))