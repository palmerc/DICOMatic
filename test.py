#!/usr/bin/env python
import StringIO
import xml.etree.cElementTree as ET
import vkbeautify as vkb
import base64

from ctypes import cdll

mp4Freeform = cdll.LoadLibrary('./libmp4freeform-lib.dylib')
regions = ET.Element("Regions")
regions.set('version', '1.0')

region = ET.SubElement(regions, "Region")
ET.SubElement(region, "RegionDataType").text = "1"
ET.SubElement(region, "PhysicalDeltaX").text = "0.05417"
ET.SubElement(region, "PhysicalDeltaY").text = "0.05417"
ET.SubElement(region, "PhysicalUnitsXDirection").text = "3"
ET.SubElement(region, "PhysicalUnitsYDirection").text = "3"
ET.SubElement(region, "ReferencePixelX0").text = "1"
ET.SubElement(region, "ReferencePixelY0").text = "1"
ET.SubElement(region, "RegionLocationMinX0").text = "0"
ET.SubElement(region, "RegionLocationMaxX1").text = "240"
ET.SubElement(region, "RegionLocationMinY0").text = "0"
ET.SubElement(region, "RegionLocationMaxY1").text = "320"
ET.SubElement(region, "RegionSpatialFormat").text = "1"

image = ET.SubElement(regions, "Image")
ET.SubElement(image, "PixelsPerMeterX").text = "1846.15385"
ET.SubElement(image, "PixelsPerMeterY").text = "1846.15385"

buffer = StringIO.StringIO()
tree = ET.ElementTree(regions)
tree.encoding = 'utf-8'
tree.write(buffer)
xml_string = buffer.getvalue()
buffer.close()

pretty_string = vkb.xml(xml_string)
freeformBase64 = base64.b64encode(pretty_string)
mp4Freeform.modifyFreeformData("H3HC4T82.mp4", "no.uio.test", "Calibrate", freeformBase64, 1);
