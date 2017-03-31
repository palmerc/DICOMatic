from optparse import OptionParser
from PIL import Image
import math
import numpy
import svgwrite
import SectorData
import StringIO
import base64
import os



def bitmapToArray(bitmap):
    width, height = bitmap.size
    beamPixelArray = numpy.array(bitmap)
    sampledImage = numpy.zeros((height, width), dtype=numpy.uint8)
    for x in range(0, width):
        for y in range(0, height):
            sampledImage[y][x] = beamPixelArray[y][x][0]
    return sampledImage

def svgCreate((widthInMillimeters, heightInMillimeters), lineWidthInMillimeters, angleInRadians, lines):
    halfWidth = widthInMillimeters / 2.0
    halfAngle = angleInRadians / 2.0

    drawing = svgwrite.Drawing()
    drawing.viewbox(0, 0, widthInMillimeters, heightInMillimeters)
    lineIndex = 0
    beams = svgwrite.container.Group(id='Beams')
    beams.add(drawing.rect(insert=(-halfWidth, 0), size=('100%', '100%'), rx=None, ry=None, fill='rgb(0, 0, 0)'))
    beams.translate((halfWidth, 0))
    for line in lines:
        lineArray = numpy.zeros((len(line), 1), dtype=numpy.uint8)
        for pointIndex in range(0, len(line)):
            point = line[pointIndex]
            lineArray[pointIndex][0] = point['intensity']

        lineImage = Image.fromarray(lineArray)
        lineImageSize = (lineWidthInMillimeters, heightInMillimeters)
        lineImageBuffer = StringIO.StringIO()
        lineImage.save(lineImageBuffer, format='png')
        lineImageEncoded = base64.b64encode(lineImageBuffer.getvalue())
        lineImageBuffer.close()

        svgLineImage = svgwrite.image.Image('data:image/png;base64,' + lineImageEncoded, size=lineImageSize)
        rotation = lineIndex * math.degrees(angleInRadians) / len(lines) - math.degrees(halfAngle)
        svgLineImage.rotate(angle=rotation)
        beams.add(svgLineImage)
        lineIndex += 1
    drawing.add(beams)
    return drawing

def main():
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="filename",
                      help="Read in beamspace data", metavar="FILE")

    (options, args) = parser.parse_args()
    path = options.filename
    filenameWithExtension = os.path.split(path)[1]
    filename = os.path.splitext(filenameWithExtension)[0]

    bitmap = Image.open(path)
    bitmapArray = bitmapToArray(bitmap)
    angleInRadians = 1.396
    sectorData = SectorData.SectorData(bitmapArray, 0, 0.24, angleInRadians)
    scanLines = sectorData.scanLineMatrix()
    widthInMillimeters = sectorData.probeSpaceSizeWidthInMeters() * 1000
    heightInMillimeters = (sectorData.endDepthInMeters - sectorData.startDepthInMeters) * 1000
    lineWidth = sectorData.sampleSpacing
    lineWidthInMillmeters = lineWidth * 1000

    drawing = svgCreate((widthInMillimeters, heightInMillimeters), lineWidthInMillmeters, angleInRadians, scanLines)
    drawing.filename = filename + '.svg'
    drawing.save(pretty=True)

if __name__ == "__main__":
    main()