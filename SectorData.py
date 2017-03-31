import math
import numpy



class SectorData:
    sampleImage = None
    sampleWidth = 0
    sampleHeight = 0
    startDepthInMeters = 0.0
    endDepthInMeters = 0.0
    sectorAngleInRadians = 0.0
    sampleSpacing = 0.0
    outputCrop = True

    def __init__(self, sampleImage, startDepthInMeters, endDepthInMeters, sectorAngleInRadians, crop=True):
        self.sampleImage = sampleImage
        self.sampleHeight, self.sampleWidth = self.sampleImage.shape
        self.startDepthInMeters = startDepthInMeters
        self.endDepthInMeters = endDepthInMeters
        self.sectorAngleInRadians = sectorAngleInRadians
        self.sampleSpacing = (self.endDepthInMeters - self.startDepthInMeters) / self.sampleWidth
        self.outputCrop = crop

    def probeSpaceSizeWidthInMeters(self):
        beamSpaceDepthInMeters = self.endDepthInMeters - self.startDepthInMeters
        return 2 * (beamSpaceDepthInMeters * math.sin(self.sectorAngleInRadians / 2.0))

    def scanLineMatrix(self):
        sampleAngleStep = self.sectorAngleInRadians / self.sampleHeight

        lines = []
        sampleHalfHeight = self.sampleHeight / 2
        for y in range(0, self.sampleHeight):
            sampleAngleOffset = (self.sampleHeight - y) - sampleHalfHeight
            thetaInRadians = sampleAngleOffset * sampleAngleStep
            points = []
            for x in range(0, self.sampleWidth):
                rhoInMeters = x * self.sampleSpacing
                point = self.beamSpaceToProbeSpaceCoordinate(rhoInMeters, thetaInRadians)
                points.append({ 'point': point, 'intensity': self.sampleImage[y][x] })
            lines.append(points)

        return lines

    def beamSpaceToProbeSpaceCoordinate(self, rhoInMeters, thetaInRadians):
        sampleColumnPositionInMeters = rhoInMeters * math.sin(thetaInRadians)
        sampleRowPositionInMeters = rhoInMeters * math.cos(thetaInRadians)
        return (sampleRowPositionInMeters, sampleColumnPositionInMeters)

    def bilinearInterpolatedMatrix(self):
        columns = int(math.ceil(self.probeSpaceSizeWidthInMeters() / self.sampleSpacing))
        if columns % 2 != 0:
            columns += 1
        rows = int(self.sampleWidth)

        scanConvertedMatrix = numpy.zeros((rows, columns), dtype=numpy.uint8)

        for row in range(0, rows):
            for col in range(0, columns):
                scanConvertedMatrix[row][col] = self.intensityForMatrixCoordinate(row, col)

        if self.outputCrop:
            padding = abs((rows - columns) / 2)
            scanConvertedMatrix = scanConvertedMatrix[0:rows, padding:columns - padding]

        return scanConvertedMatrix

    def intensityForMatrixCoordinate(self, rowInPixels, columnInPixels):
        halfWidth = self.probeSpaceSizeWidthInMeters() / 2.0

        ### Probespace
        columnInMeters = columnInPixels * self.sampleSpacing - halfWidth
        rowInMeters = rowInPixels * self.sampleSpacing

        theta, rho = self.probeSpaceToBeamSpaceCoordinate(rowInMeters, columnInMeters)
        return self.intensityForBeamSpaceCoordinate(theta, rho)

    def probeSpaceToBeamSpaceCoordinate(self, rowInMeters, columnInMeters):
        rho = math.sqrt(rowInMeters ** 2 + columnInMeters ** 2)
        halfSectorAngle = self.sectorAngleInRadians / 2.0
        az = math.asin(columnInMeters / (rho + 0.000001))
        thetaNormalized = (az + halfSectorAngle) * (1.0 / self.sectorAngleInRadians)
        rhoNormalized = (rho - self.startDepthInMeters) / (self.endDepthInMeters - self.startDepthInMeters)
        return thetaNormalized, rhoNormalized

    def intensityForBeamSpaceCoordinate(self, thetaNormalized, rhoNormalized):
        rhoSize = self.sampleWidth
        thetaSize = self.sampleHeight
        rho = rhoNormalized * rhoSize + 1.0
        theta = thetaNormalized * thetaSize + 1.0

        rho_n1 = int(rho)
        theta_m1 = int(theta)
        rho_n = rho_n1 - 1
        theta_m = theta_m1 - 1

        if rho_n1 < 1 or theta_m1 < 1:
            return 0
        if rho_n1 >= rhoSize or theta_m1 >= thetaSize:
            return 0

        sample1 = self.sampleImage[theta_m][rho_n]
        sample2 = self.sampleImage[theta_m1][rho_n]
        sample3 = self.sampleImage[theta_m][rho_n1]
        sample4 = self.sampleImage[theta_m1][rho_n1]

        deltaRho = rho - rho_n1
        alpha = (1 - deltaRho) * sample1 + deltaRho * sample3
        beta = (1 - deltaRho) * sample2 + deltaRho * sample4
        deltaTheta = theta - theta_m1
        intensityValue = numpy.uint8((1 - deltaTheta) * alpha + deltaTheta * beta)

        return intensityValue