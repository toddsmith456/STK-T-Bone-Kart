import bpy, os, math

blend_path = "/home/user/tbone_kart/tbone.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.eevee.use_gtao = True if hasattr(scene.eevee, 'use_gtao') else True

# Clean world
world = scene.world
if not world:
    world = bpy.data.worlds.new("World")
    scene.world = world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
nodes.clear()
out = nodes.new('ShaderNodeOutputWorld')
bg = nodes.new('ShaderNodeBackground')
bg.inputs['Color'].default_value = (0.06, 0.015, 0.015, 1)
bg.inputs['Strength'].default_value = 0.8
links.new(bg.outputs['Background'], out.inputs['Surface'])

# Remove existing lights, create new
for o in list(bpy.data.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o)

def add_light(name, type, energy, loc, rot, color=(1,1,1)):
    bpy.ops.object.light_add(type=type, location=loc)
    l = bpy.context.active_object
    l.name = name
    l.data.energy = energy
    l.data.color = color
    l.rotation_euler = rot
    return l

# EEVEE lights need high energy
add_light("Sun", 'SUN', 5, (4,-4,6), (math.radians(45), math.radians(15), math.radians(-45)), (1,0.95,0.9))
add_light("Fill", 'AREA', 300, (-3,2,3), (math.radians(70),0, math.radians(45)), (0.9,0.7,0.6))
add_light("Rim", 'SPOT', 600, (0,5,3), (math.radians(80),0, math.radians(180)), (1,0.9,0.8))

# Ground
if "GroundPlane" not in bpy.data.objects:
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0,0, -0.01))
    gp = bpy.context.active_object
    gp.name = "GroundPlane"
else:
    gp = bpy.data.objects["GroundPlane"]
gp.location.z = -0.01
if len(gp.data.materials)==0 or "GroundMat" not in bpy.data.materials:
    mat = bpy.data.materials.new("GroundMat")
    mat.use_nodes=True
    nt=mat.node_tree.nodes
    lk=mat.node_tree.links
    nt.clear()
    o=nt.new('ShaderNodeOutputMaterial')
    p=nt.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value=(0.04,0.01,0.01,1)
    p.inputs['Roughness'].default_value=0.8
    lk.new(p.outputs['BSDF'], o.inputs['Surface'])
    gp.data.materials.append(mat)
else:
    gp.data.materials[0] = bpy.data.materials["GroundMat"]

# Ensure camera
if "Camera" in bpy.data.objects:
    cam = bpy.data.objects["Camera"]
else:
    bpy.ops.object.camera_add(location=(0,-2,1))
    cam = bpy.context.active_object
scene.camera = cam
cam.data.clip_end = 100
cam.data.lens = 50

def render(cam_loc, cam_rot, lens, path):
    cam.location = cam_loc
    cam.rotation_euler = cam_rot
    cam.data.lens = lens
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {path}")

outdir="/home/user/tbone_kart/renders"
os.makedirs(outdir, exist_ok=True)

# Hero 3/4 front (actually kart nose front)
render(cam_loc=(0.9, -1.6, 0.75), cam_rot=(math.radians(73),0,math.radians(25)), lens=50, path=os.path.join(outdir,"eevee_hero.png"))
# Rear 3/4 showing license plate
render(cam_loc=(-0.9, 1.6, 0.70), cam_rot=(math.radians(74),0,math.radians(200)), lens=50, path=os.path.join(outdir,"eevee_rear34.png"))
# Side
render(cam_loc=(1.7, 0, 0.60), cam_rot=(math.radians(82),0,math.radians(90)), lens=55, path=os.path.join(outdir,"eevee_side.png"))
# Front straight (nose)
render(cam_loc=(0, -2.0, 0.50), cam_rot=(math.radians(85),0,0), lens=45, path=os.path.join(outdir,"eevee_front.png"))
# Back straight (license)
render(cam_loc=(0, 1.9, 0.55), cam_rot=(math.radians(85),0,math.radians(180)), lens=45, path=os.path.join(outdir,"eevee_back.png"))
# Top
render(cam_loc=(0,0,3.0), cam_rot=(0,0,0), lens=35, path=os.path.join(outdir,"eevee_top.png"))
# Detail wheel
render(cam_loc=(0.6, -0.7, 0.30), cam_rot=(math.radians(82),0,math.radians(40)), lens=60, path=os.path.join(outdir,"eevee_detail.png"))
# Mascot close
render(cam_loc=(0.3, -0.8, 0.65), cam_rot=(math.radians(76),0,math.radians(12)), lens=70, path=os.path.join(outdir,"eevee_mascot.png"))

print("EEVEE renders done")
print(os.listdir(outdir))
