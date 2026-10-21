import bpy
import os
import math

blend_path = "/home/user/tbone_kart/tbone.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

# Setup render settings
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64
scene.cycles.use_denoising = False
try:
    bpy.context.scene.cycles.denoiser = 'NONE'
except:
    pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True

# Create world light
world = bpy.context.scene.world
if not world:
    world = bpy.data.worlds.new("World")
    scene.world = world
world.use_nodes = True
nodes = world.node_tree.nodes
nodes.clear()
out = nodes.new(type='ShaderNodeOutputWorld')
bg = nodes.new(type='ShaderNodeBackground')
bg.inputs['Color'].default_value = (0.12, 0.04, 0.04, 1) # dark burgundy background matching logo
bg.inputs['Strength'].default_value = 0.4
world.node_tree.links.new(bg.outputs['Background'], out.inputs['Surface'])

# Create lighting rig: key, fill, rim
# Remove existing lights
for obj in list(bpy.data.objects):
    if obj.type == 'LIGHT':
        bpy.data.objects.remove(obj)

def create_light(name, type='SUN', energy=5, location=(0,0,5), rotation=(0,0,0), color=(1,1,1)):
    bpy.ops.object.light_add(type=type, location=location)
    light = bpy.context.active_object
    light.name = name
    light.data.energy = energy
    light.data.color = color
    light.rotation_euler = rotation
    if type == 'SUN':
        light.data.angle = 0.05
    elif type == 'AREA':
        light.data.size = 2
    return light

# Sun key
key = create_light("KeySun", 'SUN', energy=8, location=(3, -4, 5), rotation=(0.8, 0.2, -0.6), color=(1, 0.95, 0.9))
fill = create_light("FillArea", 'AREA', energy=250, location=(-3, -2, 3), rotation=(1.0, 0, 2.5), color=(1, 0.8, 0.7))
rim = create_light("RimSpot", 'SPOT', energy=400, location=(0, 4, 4), rotation=(-0.2, 0, 3.14), color=(1, 0.9, 0.7))
rim.data.spot_size = 0.9
rim.data.spot_blend = 0.3
bounce = create_light("Bounce", 'AREA', energy=80, location=(0, 0, -1), rotation=(0,0,0), color=(0.8, 0.6, 0.5))

# Create ground plane for reflection
bpy.ops.mesh.primitive_plane_add(size=10, location=(0,0,0))
ground = bpy.context.active_object
ground.name = "GroundPlane"
mat_ground = bpy.data.materials.new("GroundMat")
mat_ground.use_nodes = True
nt = mat_ground.node_tree.nodes
lk = mat_ground.node_tree.links
nt.clear()
outg = nt.new('ShaderNodeOutputMaterial')
princ = nt.new('ShaderNodeBsdfPrincipled')
princ.inputs['Base Color'].default_value = (0.08, 0.02, 0.02, 1)
princ.inputs['Roughness'].default_value = 0.3
princ.inputs['Metallic'].default_value = 0.1
lk.new(princ.outputs['BSDF'], outg.inputs['Surface'])
ground.data.materials.append(mat_ground)
ground.hide_render = False
# Hide ground for some shots? Keep for kart show

# Setup camera
if "Camera" in bpy.data.objects:
    cam = bpy.data.objects["Camera"]
else:
    bpy.ops.object.camera_add(location=(0, -2, 1))
    cam = bpy.data.objects["Camera"]
scene.camera = cam
cam.data.lens = 50
cam.data.clip_start = 0.1
cam.data.clip_end = 100

def set_camera(loc, rot_euler, lens=50):
    cam.location = loc
    cam.rotation_euler = rot_euler
    cam.data.lens = lens

# Output dir
out_dir = "/home/user/tbone_kart/renders"
os.makedirs(out_dir, exist_ok=True)

def render_to_file(filepath, loc, rot, lens=50):
    set_camera(loc, rot, lens)
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {filepath}")

# 1. Hero 3/4 front view (most important)
render_to_file(os.path.join(out_dir, "hero_front34.png"),
               loc=(1.2, -1.8, 0.85), rot=(math.radians(78), 0, math.radians(28)), lens=50)
# 2. Front view (seeing license plate? Actually front is +Y)
render_to_file(os.path.join(out_dir, "front.png"),
               loc=(0, -2.2, 0.6), rot=(math.radians(88), 0, 0), lens=45)
# 3. Rear view (license plate visible)
render_to_file(os.path.join(out_dir, "rear.png"),
               loc=(0, 2.0, 0.55), rot=(math.radians(88), 0, math.radians(180)), lens=45)
# 4. Side view
render_to_file(os.path.join(out_dir, "side.png"),
               loc=(1.9, -0.1, 0.65), rot=(math.radians(82), 0, math.radians(90)), lens=55)
# 5. Top view
render_to_file(os.path.join(out_dir, "top.png"),
               loc=(0, 0, 3.2), rot=(0,0,0), lens=35)
# 6. Closeup of mascot
render_to_file(os.path.join(out_dir, "mascot_closeup.png"),
               loc=(0.4, -0.9, 0.75), rot=(math.radians(78), 0, math.radians(18)), lens=70)
# 7. Kart only wire? Do closeup of wheel
render_to_file(os.path.join(out_dir, "detail.png"),
               loc=(0.9, -0.8, 0.45), rot=(math.radians(80), 0, math.radians(45)), lens=60)

print("All renders done")

# Also render isolated steak mascot for icon comparison: hide kart parts
# Hide kart body, wheels etc, only mascot + arms
for obj in bpy.data.objects:
    if obj.name in ["KartBody", "Seat", "LicensePlate", "ExhaustLeft", "ExhaustRight", "SteeringColumn", "SteeringWheel", "Dashboard", "HeadlightLeft", "HeadlightRight", "FrontSplitter", "WheelFrontLeft", "WheelFrontRight", "WheelRearLeft", "WheelRearRight"]:
        obj.hide_render = True
        obj.hide_viewport = True

render_to_file(os.path.join(out_dir, "mascot_only.png"),
               loc=(0, -1.4, 0.7), rot=(math.radians(80), 0, math.radians(0)), lens=60)

# Restore
for obj in bpy.data.objects:
    obj.hide_render = False
    obj.hide_viewport = False

print("Mascot only done")
