import os
import unreal

MAP_PACKAGE = '/Game/Maps/TestArena'
CUBE_PATH = '/Engine/BasicShapes/Cube.Cube'
MARK = '[CreateTestMap]'
REPORT = os.path.join(unreal.SystemLibrary.get_project_directory(), 'Saved', 'Logs', 'CreateTestMap.report.txt')

level_lib = unreal.EditorLevelLibrary


def log(message):
    unreal.log('%s %s' % (MARK, message))
    with open(REPORT, 'a') as handle:
        handle.write(message + '\n')


def spawn(cls, location, pitch=0.0, yaw=0.0):
    if cls is None:
        raise RuntimeError('spawn received a null class')
    rotation = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)
    actor = level_lib.spawn_actor_from_class(cls, location, rotation)
    if actor is None:
        raise RuntimeError('failed to spawn actor for class %s' % cls)
    return actor


def set_mesh(actor, scale):
    component = actor.get_editor_property('static_mesh_component')
    if component is None:
        raise RuntimeError('static mesh actor has no component')
    component.set_editor_property('static_mesh', unreal.load_object(None, CUBE_PATH))
    component.set_editor_property('relative_scale3d', scale)


def build_level():
    sun_class = unreal.load_class(None, '/Script/NightFall.NightFallSunActor')
    if sun_class is None:
        raise RuntimeError('NightFallSunActor class not found - build the project first')

    floor = spawn(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, -25.0))
    floor.set_actor_label('Floor')
    set_mesh(floor, unreal.Vector(100.0, 100.0, 0.5))

    props = [
        ('Prop_West', unreal.Vector(-600.0, 300.0, 100.0), 45.0),
        ('Prop_East', unreal.Vector(700.0, -250.0, 100.0), -30.0),
        ('Prop_North', unreal.Vector(250.0, 900.0, 100.0), 15.0),
        ('Prop_Pillar', unreal.Vector(-900.0, -700.0, 200.0), 0.0),
    ]
    for label, location, yaw in props:
        prop = spawn(unreal.StaticMeshActor, location, yaw=yaw)
        prop.set_actor_label(label)
        set_mesh(prop, unreal.Vector(2.0, 2.0, 4.0 if label == 'Prop_Pillar' else 2.0))

    sun = spawn(sun_class, unreal.Vector(0.0, 0.0, 1000.0), pitch=45.0, yaw=-35.0)
    sun.set_actor_label('Sun')

    spawn(unreal.SkyAtmosphere, unreal.Vector(0.0, 0.0, 0.0)).set_actor_label('SkyAtmosphere')
    spawn(unreal.SkyLight, unreal.Vector(0.0, 0.0, 800.0)).set_actor_label('SkyLight')
    spawn(unreal.ExponentialHeightFog, unreal.Vector(0.0, 0.0, -100.0)).set_actor_label('HeightFog')
    spawn(unreal.PlayerStart, unreal.Vector(0.0, -300.0, 120.0)).set_actor_label('PlayerStart')


def main():
    with open(REPORT, 'w') as handle:
        handle.write('start\n')

    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PACKAGE):
        log('level already exists - nothing to do')
        return

    log('creating new level at %s' % MAP_PACKAGE)
    if not level_lib.new_level(MAP_PACKAGE):
        raise RuntimeError('new_level failed for %s' % MAP_PACKAGE)

    build_level()

    saved = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log('saved: %s' % saved)
    if not saved:
        raise RuntimeError('save_dirty_packages reported failure')

    actor_count = len(level_lib.get_all_level_actors())
    log('actor count: %d' % actor_count)
    log('done')


try:
    main()
except Exception as error:
    unreal.log_error('%s FAILED: %s' % (MARK, error))
    with open(REPORT, 'a') as handle:
        handle.write('FAILED: %s\n' % error)
    raise
