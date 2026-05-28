"""Shim package that bridges the Maya shelf to the shared workfile publisher.

The shelf button in
``MayaRepository/2026/config/tinystudio_tools.json`` calls
``workfiles.main_window.main`` for legacy compatibility. The real code lives
in ``workfile_publisher`` (under ``GenTools/workfilePublisher/src``), which is
already on PYTHONPATH thanks to ``configs/maya_2026.json``'s
``additional_paths`` entry.
"""
