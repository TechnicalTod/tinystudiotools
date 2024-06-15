import maya.cmds as mc
from functools import partial
import sys


def find_bbox(object):
    '''Finds the bbox of an object and returns the scales
    '''
    scales = []

    bbox = mc.exactWorldBoundingBox(object)

    lengthX = abs(bbox[0] - bbox[3])
    lengthY = abs(bbox[1] - bbox[4])
    lengthZ = abs(bbox[2] - bbox[5])

    scales.append(lengthX)
    scales.append(lengthY)
    scales.append(lengthZ)
    return scales


def generate_cards(card_number):
    '''Generates the cards.

    Args:
        card_number(int): taken from slider value

    Example:
        Use slider or input in field number of cards wanted and run Generate Cards

    '''
    selection = mc.ls(sl=True)

    if selection == []:
        mc.warning("Select an object(s)")

    else:
        for object in selection:
            mc.select(object)
            mc.CenterPivot(object)
            position = mc.xform(object, q=True, a=True, ws=True, rp=True)
            mc.undo()

            scales = find_bbox(object)

            if card_number == 1:
                card_01 = mc.polyPlane(w=scales[2], h=scales[1], n="card_01", sx=1, sy=1, ax=[1, 0, 0])

                mc.xform(card_01, t=position)

            if card_number == 2:
                card_01 = mc.polyPlane(w=scales[2], h=scales[1], n="card_01", sx=1, sy=1, ax=[1, 0, 0])
                card_02 = mc.polyPlane(w=scales[0], h=scales[1], n="card_02", sx=1, sy=1, ax=[0, 0, 1])

                mc.xform(card_01, card_02, t=position)

            if card_number == 3:
                card_01 = mc.polyPlane(w=scales[2], h=scales[1], n="card_01", sx=1, sy=1, ax=[1, 0, 0])
                card_02 = mc.polyPlane(w=scales[0], h=scales[1], n="card_02", sx=1, sy=1, ax=[0, 0, 1])
                card_03 = mc.polyPlane(w=scales[0], h=scales[2], n="card_03", sx=1, sy=1, ax=[0, 1, 0])

                mc.xform(card_01, card_02, card_03, t=position)
        sys.stdout.write("Cards created")

    mc.select(cl=True)


def slider_value(slider, *args):
    '''Checks the slider value
    '''
    value = mc.intSliderGrp(slider, query=True, value=True)
    generate_cards(value)


def create_window(name, slider):
    '''Makes the UI
    '''
    win = mc.window(name, title="Card Generator", widthHeight=(200, 200))
    mc.paneLayout(configuration="horizontal4")
    mc.scrollField(wordWrap=True, editable=False, h=(20), text="Select any number of objects then choose how many cards you would like to generate for each object")
    mc.intSliderGrp(slider, label="Number of cards", cw3=(84, 55, 0), field=True, min=1, max=3, value=1)
    mc.button(label="Generate Cards", command=partial(slider_value, slider))
    mc.showWindow(win)


def launch():
    name = "window"
    slider = "slider"
    if mc.window(name, ex=True):
        mc.deleteUI(name)
        create_window(name, slider)
    else:
        create_window(name, slider)
