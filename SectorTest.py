import unittest
from PIL import Image
import numpy

import SectorData

class BilinearInterpolationTestCase(unittest.TestCase):
    """ This is a test """

    def test_intensityForBeamSpaceCoordinate(self):
        """ Test 1 """
        scanImage = Image.open("Test Images/scan00.bmp")
        scanImageWidth, scanImageHeight = scanImage.size
        scanImagePixelArray = numpy.array(scanImage)
        grayscaleValues = numpy.zeros((scanImageHeight, scanImageWidth), dtype=numpy.uint8)
        for x in range(0, scanImageWidth):
            for y in range(0, scanImageHeight):
                grayscaleValues[y][x] = scanImagePixelArray[y][x][0]

        beamImage = Image.open("Test Images/beam00.bmp")
        beamImageWidth, beamImageHeight = beamImage.size
        beamPixelArray = numpy.array(beamImage)
        sampledImage = numpy.zeros((beamImageHeight, beamImageWidth), dtype=numpy.uint8)
        for x in range(0, beamImageWidth):
            for y in range(0, beamImageHeight):
                sampledImage[y][x] = beamPixelArray[y][x][0]
        sector = SectorData.SectorData(sampledImage, 0, 0.129, 1.31)

        intensity1 = sector.intensityForBeamSpaceCoordinate(1.70007253, .608730137)
        self.assertEquals(intensity1, 0)

        intensity2 = sector.intensityForBeamSpaceCoordinate(0.854760944, 0.00182451657)
        self.assertEquals(intensity2, 198)

        intensity3 = sector.intensityForBeamSpaceCoordinate(0.1452391, 0.00182451657)
        self.assertEquals(intensity3, 175)

    def test_probeSpaceToBeamSpace(self):
        # ps: -0.000318665, 0.000212072
        # bs: 0.00294448, 1.25146
        # ps: -0.000106223, 0.000212072
        # bs: 0.00182452, 0.854761
        # ps: 0.000106223, 0.000212072
        # bs: 0.00182452, 0.145239

        """ Test 1 """
        scanImage = Image.open("Test Images/scan00.bmp")
        scanImageWidth, scanImageHeight = scanImage.size
        scanImagePixelArray = numpy.array(scanImage)
        grayscaleValues = numpy.zeros((scanImageHeight, scanImageWidth), dtype=numpy.uint8)
        for x in range(0, scanImageWidth):
            for y in range(0, scanImageHeight):
                grayscaleValues[y][x] = scanImagePixelArray[y][x][0]

        beamImage = Image.open("Test Images/beam00.bmp")
        beamImageWidth, beamImageHeight = beamImage.size
        beamPixelArray = numpy.array(beamImage)
        sampledImage = numpy.zeros((beamImageHeight, beamImageWidth), dtype=numpy.uint8)
        for x in range(0, beamImageWidth):
            for y in range(0, beamImageHeight):
                sampledImage[y][x] = beamPixelArray[y][x][0]
        sector = SectorData.SectorData(sampledImage, 0, 0.129, 1.31)

        beamspaceCoord = sector.probeSpaceToBeamSpaceCoordinate(0, -1.0 * -0.0791349)
        self.assertEqual(beamspaceCoord, (1.70007, 0.60873))

        beamspaceCoord = sector.probeSpaceToBeamSpaceCoordinate(-1.0 * 0.000212072, -1.0 * -0.000318665)
        self.assertEqual(beamspaceCoord, (1.25146, 0.00294448))

if __name__ == '__main__':
    unittest.main()