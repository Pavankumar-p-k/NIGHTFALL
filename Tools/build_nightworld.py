import unreal, json, os, math, random, time

OUT = {}
ls = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
NM = '/Game/Maps/NightWorld'
ok = unreal.EditorLevelLibrary.new_level(NM)
OUT['new_level'] = bool(ok)
if not ok:
    print('@@UNREAL_CONNECTOR_JSON@@' + json.dumps(OUT))
    raise SystemExit(1)
time.sleep(1.0)

sun = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 5000.0))
sun.set_actor_rotation(unreal.Rotator(-55.0, 40.0, 0.0), False)
sun.set_actor_label('SUN')
lc = sun.get_editor_property('light_component')
lc.set_editor_property('intensity', 8.0)
lc.set_editor_property('light_color',
                       unreal.Color(255, 244, 224, 255))

skyl = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.SkyLight, unreal.Vector(0.0, 0.0, 3000.0))
skyl.set_actor_label('SKYLIGHT')
slc = skyl.get_editor_property('light_component')
try:
    slc.set_editor_property('real_time_capture', True)
except Exception:
    pass

unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.SkyAtmosphere, unreal.Vector(0.0, 0.0, 0.0)
).set_actor_label('SKYATMOS')

fog = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.ExponentialHeightFog, unreal.Vector(0.0, 0.0, 0.0))
fog.set_actor_label('FOG')
fc = fog.get_editor_property('component')
try:
    fc.set_editor_property('fog_density', 0.012)
    fc.set_editor_property('fog_max_opacity', 0.85)
except Exception:
    pass

unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.VolumetricCloud, unreal.Vector(0.0, 0.0, 6000.0)
).set_actor_label('CLOUDS')
OUT['env'] = True

mesh = unreal.EditorAssetLibrary.load_asset('/Game/Terrain/SM_Hills')
floor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 800.0))
comp = floor.get_editor_property('static_mesh_component')
comp.set_editor_property('static_mesh', mesh)
try:
    bs = mesh.get_editor_property('body_setup')
    bs.set_editor_property(
        'collision_trace_flag',
        unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
except Exception:
    pass
try:
    comp.set_collision_profile_name('BlockAll')
except Exception:
    pass
floor.set_actor_label('GDT_FLOOR')
floor.set_actor_scale3d(unreal.Vector(100.0, 100.0, 100.0))
floor.set_actor_location(unreal.Vector(0.0, 0.0, 0.0), False, True)
OUT['floor'] = True


def h(x, y):
    v = 0.0
    v += 38.0 * math.sin(x * 0.0043 + 1.7) * math.cos(y * 0.0037 - 0.6)
    v += 18.0 * math.sin(x * 0.0091 - 2.1) * math.sin(y * 0.0084 + 1.2)
    v += 8.0 * math.cos(x * 0.021 + 0.4) * math.cos(y * 0.019 - 1.1)
    v += 3.5 * math.sin(x * 0.048 + 2.5) * math.cos(y * 0.052 + 0.9)
    v += 22.0 * math.sin((x + y) * 0.0016 + 0.8)
    return v * 100.0


mat = unreal.EditorAssetLibrary.load_asset('/Game/Terrain/M_Water')
rmat = unreal.EditorAssetLibrary.load_asset('/Game/Terrain/M_Road')
plane = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Plane')
tree_mesh = unreal.EditorAssetLibrary.load_asset(
    '/Game/Fab/Low_Poly_Tree_Scene_Free/low_poly_tree_scene_free/'
    'StaticMeshes/low_poly_tree_scene_free')
rock_mesh = unreal.EditorAssetLibrary.load_asset(
    '/Game/Fab/Landscape_Sketching/landscape_sketching/StaticMeshes/'
    'landscape_sketching')


def spawn_ism(label, mesh_obj, material):
    a = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.Actor, unreal.Vector(0.0, 0.0, 2000.0))
    comp = unreal.InstancedStaticMeshComponent(a, 'ISM_' + label)
    comp.set_editor_property('static_mesh', mesh_obj)
    if material is not None:
        comp.set_material(0, material)
    a.set_editor_property('root_component', comp)
    a.set_actor_label(label)
    return a, comp


pond_a, pond_c = spawn_ism('GND_PONDS', plane, mat)
cands = []
for gx in range(-8, 9):
    for gy in range(-8, 9):
        x, y = gx * 110.0, gy * 110.0
        if abs(x) < 250 and abs(y) < 250:
            continue
        cands.append((h(x, y), x, y))
cands.sort()
ponds = []
for hh, x, y in cands:
    if len(ponds) >= 3:
        break
    if all((x - px) ** 2 + (y - py) ** 2 > 400.0 ** 2
           for _, px, py in ponds):
        ponds.append((hh, x, y))
for hh, x, y in ponds:
    pond_c.add_instance(unreal.Transform(
        unreal.Vector(x, y, hh + 25.0), unreal.Rotator(0.0, 0.0, 0.0),
        unreal.Vector(120.0, 100.0, 1.0)))
OUT['ponds'] = len(ponds)

road_a, road_c = spawn_ism('GND_ROADS', plane, rmat)
rd = 0
for ang in (0.3, 1.9, 3.5, 5.1):
    x, y = 0.0, 0.0
    for seg in range(24):
        nx = x + 38.0 * math.cos(ang) + 8.0 * math.sin(seg * 0.5)
        ny = y + 38.0 * math.sin(ang) + 8.0 * math.cos(seg * 0.4)
        if abs(nx) > 950 or abs(ny) > 950:
            break
        yaw = math.degrees(math.atan2(ny - y, nx - x)) - 90.0
        road_c.add_instance(unreal.Transform(
            unreal.Vector(nx, ny, h(nx, ny) + 12.0),
            unreal.Rotator(0.0, 0.0, yaw),
            unreal.Vector(9.0, 42.0, 1.0)))
        rd += 1
        x, y = nx, ny
OUT['road_segs'] = rd

random.seed(42)
tree_a, tree_c = spawn_ism('GND_TREES', tree_mesh, None)
tn = 0
for i in range(55):
    x = random.uniform(-920, 920)
    y = random.uniform(-920, 920)
    if abs(x) < 120 and abs(y) < 120:
        continue
    tree_c.add_instance(unreal.Transform(
        unreal.Vector(x, y, h(x, y) - 30.0),
        unreal.Rotator(0.0, 0.0, random.uniform(0, 360)),
        unreal.Vector(random.uniform(1.0, 2.8), random.uniform(1.0, 2.8),
                      random.uniform(1.0, 2.2))))
    tn += 1
OUT['trees'] = tn

rock_a, rock_c = spawn_ism('GND_ROCKS', rock_mesh, None)
rn = 0
for i in range(10):
    x = random.uniform(-900, 900)
    y = random.uniform(-900, 900)
    rock_c.add_instance(unreal.Transform(
        unreal.Vector(x, y, h(x, y) - 15.0),
        unreal.Rotator(0.0, 0.0, random.uniform(0, 360)),
        unreal.Vector(random.uniform(2.0, 5.0), random.uniform(2.0, 5.0),
                      random.uniform(1.5, 4.0))))
    rn += 1
OUT['rocks'] = rn

psz = h(0.0, 0.0) + 900.0
ps = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.PlayerStart, unreal.Vector(0.0, 0.0, psz))
ps.set_actor_label('PLAYERSTART')
OUT['ps_z'] = round(psz, 0)

key = str(ls.get_active_viewport_config_key())
cam_z = max(h(0.0, -1500.0), 0.0) + 1400.0
ls.set_level_viewport_camera_info(
    unreal.Vector(0.0, -1500.0, cam_z),
    unreal.Rotator(-20.0, 0.0, 0.0), key)

time.sleep(0.5)
ls.save_current_level()
time.sleep(2.0)
NM_U = r'C:\Users\peter\Desktop\NightFall\Content\Maps\NightWorld.umap'
OUT['umap_exists'] = os.path.exists(NM_U)
OUT['umap_size'] = os.path.getsize(NM_U) if OUT['umap_exists'] else 0
print('@@UNREAL_CONNECTOR_JSON@@' + json.dumps(OUT))
