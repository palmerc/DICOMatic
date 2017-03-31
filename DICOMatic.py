#!/usr/bin/env python

import dicom
import os
import math
import glymur
import tempfile
import SectorData
from PIL import Image
from subprocess import call
from ctypes import cdll
import xml.etree.cElementTree as ET
import vkbeautify as vkb
import base64

import cStringIO as StringIO



def findall(p, s):
    '''Yields all the positions of
    the pattern p in the string s.'''
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i+1)

mp4FreeformLibrary = cdll.LoadLibrary("./libmp4freeform-lib.dylib")

PathDicom = "./DICOMs/"
dicomFilenames = []  # create an empty list
for dirName, subdirList, fileList in os.walk(PathDicom):
    for filename in fileList:
        if ".dcm" in filename.lower():  # check whether the file's DICOM
            dicomFilenames.append(os.path.join(dirName,filename))

outputSize = (240, 416)

for dicomFilename in dicomFilenames:
    filenameWithExtension = os.path.split(dicomFilename)[1]
    filename = os.path.splitext(filenameWithExtension)[0]
    mpegFilename = filename + '.mp4'

    print "Converting " + filenameWithExtension + " to " + mpegFilename

    # Get ref file
    RefDs = dicom.read_file(dicomFilename)
    frameTime = 0
    try:
        frameTime = RefDs.get('FrameTime', default=22) / 1000.0
    except KeyError:
        print "No FrameTime key."

    framesPerSecond = 0
    try:
        framesPerSecond = RefDs.get('CineRate', default=24)
    except KeyError:
        print "No CineRate key."
        framesPerSecond = int(1.0 / frameTime)

    # Load spacing values (in mm)
    regionSpatialFormat = RefDs.SequenceOfUltrasoundRegions[0].RegionSpatialFormat
    regionDataType = RefDs.SequenceOfUltrasoundRegions[0].RegionDataType
    regionLocationMinX0 = RefDs.SequenceOfUltrasoundRegions[0].RegionLocationMinX0
    regionLocationMaxX1 = RefDs.SequenceOfUltrasoundRegions[0].RegionLocationMaxX1
    regionLocationMinY0 = RefDs.SequenceOfUltrasoundRegions[0].RegionLocationMinY0
    regionLocationMaxY1 = RefDs.SequenceOfUltrasoundRegions[0].RegionLocationMaxY1

    physicalUnitsXDirection = RefDs.SequenceOfUltrasoundRegions[0].PhysicalUnitsXDirection
    physicalUnitsYDirection = RefDs.SequenceOfUltrasoundRegions[0].PhysicalUnitsYDirection
    pixelSpacingInMeters = RefDs.SequenceOfUltrasoundRegions[0].PhysicalDeltaX / 100.0

    halfWidthInPixels = (regionLocationMaxX1 - regionLocationMinX0) / 2
    halfWidthInMeters = halfWidthInPixels * pixelSpacingInMeters

    depthInPixels = regionLocationMaxY1 - regionLocationMinY0
    depthInMeters = depthInPixels * pixelSpacingInMeters

    sectorAngleInRadians = 2.0 * math.asin(halfWidthInMeters / depthInMeters)

    dicomFile = open(dicomFilename, "r").read()
    jp2Magic = '\x00\x00\x00\x0C\x6A\x50\x20\x20\x0D\x0A\x87\x0A\x00\x00\x00\x14\x66\x74\x79\x70\x6A\x70\x32'
    frameLocations = [i for i in findall(jp2Magic, dicomFile)]
    print "Frame count: " + str(len(frameLocations))
    filePrefix = filename + "_"
    # Dump JPEG2000 files, reprocessing them to minimize them
    sampleSpacing = 0
    index = 0
    scanConvertedFilenameFormat = filePrefix + "scanconverted%04d.png"
    for frameLocation in frameLocations:
        oversizeFilename = filePrefix + str(frameLocation) + '.jp2'
        oversizeFileContents = dicomFile[frameLocation:]

        file = tempfile.NamedTemporaryFile()
        file.write(oversizeFileContents)
        jp2File = glymur.Jp2k(file.name)[:]
        file.close()

        sectorData = SectorData.SectorData(jp2File, 0, depthInMeters, sectorAngleInRadians, crop=True)
        sampleSpacing = sectorData.sampleSpacing
        interpolatedArray = sectorData.bilinearInterpolatedMatrix()
        interpolatedImage = Image.fromarray(interpolatedArray)

        scanConvertedFilename = scanConvertedFilenameFormat % index
        interpolatedImage.save(scanConvertedFilename)

        index += 1

    try:
        os.remove(mpegFilename)
    except OSError:
        pass

    width = str(outputSize[0])
    halfWidth = str(outputSize[0] / 2)
    height = str(outputSize[1])
    scale = 'scale=iw*min(' + width + '/iw\,' + height + '/ih):ih*min(' + width + '/iw\,' + height +'/ih)'
    pad = 'pad=' + width + ':' + height + ':0:0'
    filter = scale + ',' + pad
    call(['ffmpeg', '-r', str(framesPerSecond),
          '-i', scanConvertedFilenameFormat,
          '-vf', filter,
          '-crf', '18',
          '-pix_fmt', 'yuv420p',
          '-movflags', '+faststart',
          '-vcodec', 'libx264',
          mpegFilename])

    for index in range(0, len(frameLocations)):
        scanConvertedFilename = scanConvertedFilenameFormat % index
        os.remove(scanConvertedFilename)

    regions = ET.Element("Regions")
    regions.set('version', '1.0')
    region = ET.SubElement(regions, "Region")
    ET.SubElement(region, "RegionDataType").text = str(regionDataType)
    ET.SubElement(region, "PhysicalDeltaX").text = str(sampleSpacing)
    ET.SubElement(region, "PhysicalDeltaY").text = str(sampleSpacing)
    ET.SubElement(region, "PhysicalUnitsXDirection").text = str(physicalUnitsXDirection)
    ET.SubElement(region, "PhysicalUnitsYDirection").text = str(physicalUnitsYDirection)
    ET.SubElement(region, "ReferencePixelX0").text = halfWidth
    ET.SubElement(region, "ReferencePixelY0").text = "0"
    ET.SubElement(region, "RegionLocationMinX0").text = "0"
    ET.SubElement(region, "RegionLocationMaxX1").text = width
    ET.SubElement(region, "RegionLocationMinY0").text = "0"
    ET.SubElement(region, "RegionLocationMaxY1").text = height
    ET.SubElement(region, "RegionSpatialFormat").text = str(regionSpatialFormat)

    image = ET.SubElement(regions, "Image")
    ET.SubElement(image, "PixelsPerMeterX").text = str(100.0 / sampleSpacing)
    ET.SubElement(image, "PixelsPerMeterY").text = str(100.0 / sampleSpacing)

    tree = ET.ElementTree(regions)
    xmlBuffer = StringIO.StringIO()
    tree.write(xmlBuffer)
    metadataXMLString = vkb.xml(xmlBuffer.getvalue())
    metadataXMLBase64 = base64.b64encode(metadataXMLString)
    mp4FreeformLibrary.modifyFreeformData(mpegFilename, "com.ge.med.vscan", "Calibration", metadataXMLBase64, 1);
    xmlBuffer.close()
