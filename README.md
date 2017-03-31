# DICOMatic

This was a tool used to generate cardiac heart loops by dumping the JPEG 2000 files from the DICOM and reassembling them into MP4s without needing to actually understand the DICOM format, or deal with the typcial problems of text or overlays I was not interested in. The JPEG 2000 files are actually the beamspace data, so you need to scanconvert them and interpolate to reconstruct the typical sector image

## Conversion sample
### Beamspace image
![Beamspace image](images/Image00.jp2)

### Scan-converted image
![Scan converted image](images/beam00.png)

### Interpolated image
![Interpolated image](images/scan00.png)
