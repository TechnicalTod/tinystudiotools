# TinyStudio TODO

## Asset & workfile publishing

- [ ] Workfile and asset manager — asset and folder trees should populate from ftrack assets and shots (ftrack API)

## Maya & rigging

- [ ] Get Technodolly geo to reskin the Technodolly
- [ ] Tunnel — import assets ready for set dec

rigs are now publishing with the standalone tool and importing back into unreal - still needs the master material fix and check materials are importing properly

once these are publishing properly then need to get the asset manager to publish rigs propoerly. I think the process should be two step

1. tag the rig first with all the correct metadata (called out as missing in pre-publish)
2. publish the rig. this will have two separate rig publishes. 1 will just be the maya - rig and then there will be another product type which will be unreal - skeletal mesh a skeletal mesh will will obviously require a maya rig first

## Unreal

- [ ] Get Unreal media plate blueprint
- [ ] Get UE master materials

## Shot publisher

once the rigs are importing correctly above we need to try animate a rig and then send that rig across with the shot publisher

continue working on broken alembic imports not importing with frame 1001 offset

unreal side is importing a full fresh set dec, this should just be fbx geo and then use the publish attr data to source the shader that is being used on the official published set dec

multiple CUSTOM folders are being created in the level sequence, this should just be a single folder called CUSTOMGEO

## After Effects

- [ ] Render HUD
- [ ] Render output tool — ensure everyone exports and renders to the same place with the same format
- [ ] AE workfile publisher is a behemoth — split into manageable chunks

## Asset manager

- [ ] asset manager needs to start enforcing the prepublish checks but this should only happen once we have the rigs publishing properly
