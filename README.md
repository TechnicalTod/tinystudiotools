# TinyStudio Previs Tools Repository

This is the repository for the TinyStudio pipeline.

## Description

This requires two main drives to be set to correctly run

studioLib **(L:/TinyStudioTools)** - This contains the contents of this repository<br />
showDrive **(S:/)** - This contains all of the Studio show project dirs<br />

In addition to this it requires the following folders to be created

**L:\Artist** - Artist folder

**App Launcher**
All artists must interact with applications through the TinyStudio launcher.
Make a shortcut copy of the launcher executable: **L:\TinyStudioTools\GenTools\TinyStudioLauncher\dist\TinyStudioLauncher\TinyStudioLauncher.exe** (or your installed build path).

**Unreal Generic project setup docs**
https://docs.google.com/document/d/1NRxG60mvPhEzeWD2NCXaiJ-_0_pyBCbX-a-44ctsJb8/edit

### Prerequisite additional apps

- UV package manager
- Advanced skeleton

### Prerequisite python libs

These libraries should be pip installed directly into the corresponding tools folder

### Tunnel Asset Browser reqs

- Requires the megascansMetaData folder to be in the studiolib **(L:/megaScansMetadata)**
- Must have the megascans base ZIP repositiory on network attached storage (around 2TB)

**MAYA:**

- PyMel 1.5.0
  - https://help.autodesk.com/view/MAYAUL/2025/ENU/?guid=GUID-2AA5EFCE-53B1-46A0-8E43-4CD0B2C72FB4
  - https://www.autodesk.com/support/technical/article/caas/tsarticles/ts/6gfZgdPquwZ2qCVxfAkb1n.html
  - **Maya 2026 PyMEL Cache Fix:** If PyMEL fails to import or causes Maya to crash, you need to create Maya 2026 cache files:
    1. Navigate to Maya bin directory: `cd "C:\Program Files\Autodesk\Maya2026\bin"`
    2. Install PyMEL: `.\mayapy.exe -m pip install pymel`
    3. Navigate to cache directory: `cd "C:\Users\[USERNAME]\AppData\Roaming\Python\Python311\site-packages\pymel\cache"`
    4. Copy cache files from Maya 2025 to 2026:
       - `Copy-Item "mayaApi2025.py" "mayaApi2026.py"`
       - `Copy-Item "mayaCmdsDocs2025.py" "mayaCmdsDocs2026.py"`
       - `Copy-Item "mayaCmdsExamples2025.py" "mayaCmdsExamples2026.py"`
       - `Copy-Item "mayaCmdsList2025.py" "mayaCmdsList2026.py"`
- Numpy

**UNREAL**

- PySide6
- Numpy
- transforms3d

**FAQ:**

1. Must disable Antivirus when re-building the launcher, otherwise it will try to delete the newly created .EXE
2. had to install numpy directly into unreal using:<br />
   cd "C:\Program Files\Epic Games\UE_5.3\Engine\Binaries\ThirdParty\Python3\Win64"<br />
   .\python.exe -m pip install --upgrade numpy<2<br />
