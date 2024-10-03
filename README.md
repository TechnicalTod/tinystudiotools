# Saga Previs Tools Repository
This is the repository for the Saga Studio pipeline repository

## Description
This requires two main drives to be set to correctly run

studioLib **(L:/SagaTools)** - This contains the contents of this repository<br />
showDrive **(S:/)** - This contains all of the Studio show project dirs<br />

In addition to this it requires the following folders to be created

**L:\Artist** - Artist folder

**Unreal Generic project setup docs**
https://docs.google.com/document/d/1NRxG60mvPhEzeWD2NCXaiJ-_0_pyBCbX-a-44ctsJb8/edit

### Prerequisite additional apps

- Prism asset manager
- Advanced skeleton

### Prerequisite python libs
These libraries should be pip installed directly into the corresponding tools folder

### Tunnel Asset Browser reqs
- Requires the megascansMetaData folder to be in the studiolib **(L:/megaScansMetadata)**
- Must have the megascans base ZIP repositiory on network attached storage (around 2TB)

**MAYA:**
- Numpy

**UNREAL**
- Pyside2
- Numpy
- transforms3d

**FAQ:**
1. Must disable Antivirus when re-building the launcher, otherwise it will try to delete the newly created .EXE
2. had to install numpy directly into unreal using:<br />
cd "C:\Program Files\Epic Games\UE_5.3\Engine\Binaries\ThirdParty\Python3\Win64"<br />
.\python.exe -m pip install --upgrade numpy**<br />

