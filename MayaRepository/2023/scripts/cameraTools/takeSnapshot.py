import re
import maya.cmds as mc
from genTools.genUtils import viewportMessage
import genTools.versionFile
import filePaths

def versionSnapshotFile():
    saveDir = filePaths.downloadsFolder
    fileName = "TmpSnapshot"
    fileExtension = ".png"
    existing_file, new_file = genTools.versionFile.VersionExistingFilePath(saveDir, fileName, fileExtension)

    return new_file

def capture(camera=None,
            width=None,
            height=None,
            filename=None,
            complete_filename=versionSnapshotFile(),
            start_frame=None,
            end_frame=None,
            frame=None,
            format='image',
            compression='png',
            quality=100,
            off_screen=False,
            viewer=True,
            isolate=None,
            maintain_aspect_ratio=True,
            overwrite=True,
            raw_frame_numbers=False,
            camera_options=None,
            display_options=None,
            viewport_options=None,
            viewport2_options=None):

    camera = camera or "persp"

    # Ensure camera exists
    if not mc.objExists(camera):
        raise RuntimeError("Camera does not exist: {0}".format(camera))

    width = width or mc.getAttr("defaultResolution.width")
    height = height or mc.getAttr("defaultResolution.height")
    if maintain_aspect_ratio:
        ratio = mc.getAttr("defaultResolution.deviceAspectRatio")
        height = width / ratio

    start_frame = start_frame or mc.playbackOptions(minTime=True, query=True)
    end_frame = end_frame or mc.playbackOptions(maxTime=True, query=True)

    playblast_kwargs = dict()
    if complete_filename:
        playblast_kwargs['completeFilename'] = complete_filename
    if frame:
        playblast_kwargs['frame'] = frame

    mc.currentTime(mc.currentTime(q=1))

    output = mc.playblast(
        compression=compression,
        format=format,
        percent=100,
        quality=quality,
        viewer=viewer,
        startTime=start_frame,
        endTime=end_frame,
        offScreen=off_screen,
        forceOverwrite=overwrite,
        filename=filename,
        widthHeight=[width, height],
        rawFrameNumbers=raw_frame_numbers,
        **playblast_kwargs)
    return output


def snap(*args, **kwargs):
    # capture single frame
    frame = kwargs.pop('frame', mc.currentTime(q=1))
    kwargs['start_frame'] = frame
    kwargs['end_frame'] = frame
    kwargs['frame'] = frame

    if not isinstance(frame, (int, float)):
        raise TypeError("frame must be a single frame (integer or float). "
                        "Use `capture()` for sequences.")

    # override capture defaults
    format = kwargs.pop('format', "image")
    compression = kwargs.pop('compression', "png")
    viewer = kwargs.pop('viewer', False)
    raw_frame_numbers = kwargs.pop('raw_frame_numbers', True)
    kwargs['compression'] = compression
    kwargs['format'] = format
    kwargs['viewer'] = viewer
    kwargs['raw_frame_numbers'] = raw_frame_numbers

    # pop snap only keyword arguments
    clipboard = kwargs.pop('clipboard', False)

    # perform capture
    output = capture(*args, **kwargs)

    def replace(m):
        '''Substitute with frame number'''
        return str(int(frame)).zfill(len(m.group()))

    output = re.sub("#+", replace, output)

    # add image to clipboard
    if clipboard:
        image_to_clipboard(output)
    
    print (output)
    viewportMessage('Saving screengrab.......', output, '#00ff00')
    return output

def image_to_clipboard(path):
    from PySide2 import QtGui, QtWidgets
    image = QtGui.QImage(path)
    clipboard = QtWidgets.QApplication.clipboard()
    clipboard.setImage(image, mode=QtGui.QClipboard.Clipboard)



