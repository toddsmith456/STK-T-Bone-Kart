#!/usr/bin/env python3
# Create T-Bone kart in Blender and export for SuperTuxKart
import bpy
import math
import json
import os
import sys

# Clear everything
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Purge orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for mat in bpy.data.materials:
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    for img in bpy.data.images:
        if img.users == 0:
            bpy.data.images.remove(img)

# Enable addons if not enabled
try:
    bpy.ops.preferences.addon_enable(module="io_scene_spm")
    print("Enabled io_scene_spm")
except Exception as e:
    print(f"Enable io_scene_spm failed: {e}")
try:
    bpy.ops.preferences.addon_enable(module="io_antarctica_scene")
    print("Enabled io_antarctica_scene")
except Exception as e:
    print(f"Enable io_antarctica_scene failed: {e}")

clear_scene()

# Set scene properties for STK kart
scene = bpy.context.scene
scene['is_stk_kart'] = 'true'
scene['code'] = 'tbone'
scene['name'] = 'T-Bone'
scene['icon'] = 'tbone_icon.png'
scene['minimap_icon'] = 'tbone_icon.png'
scene['shadow'] = 'tbone_shadow.png'
scene['group'] = 'Add-Ons'
scene['color'] = '90 15 15'  # dark red RGB 0-255
scene['kart_version'] = 3
scene['export_version'] = 3
scene['karttype'] = 'medium'
scene['engine_sfx'] = 'large'
scene['skid_sound'] = 'default'
scene['center_shift'] = -0.05
scene['kartLean'] = '3.0'
scene['exhaust_xml'] = 'kart_exhaust.xml'
# Ensure frame range
scene.frame_start = 0
scene.frame_end = 600

# Clear markers
for m in list(scene.timeline_markers):
    scene.timeline_markers.remove(m)

def add_marker(name, frame):
    m = scene.timeline_markers.new(name, frame=frame)
    return m

# Add required animation markers
add_marker("left", 1)
add_marker("straight", 20)
add_marker("right", 40)
add_marker("backpedal-left", 50)
add_marker("backpedal", 60)
add_marker("backpedal-right", 70)
add_marker("start-winning", 80)
add_marker("start-winning-loop", 120)
add_marker("end-winning", 200)
add_marker("end-winning-straight", 220)
add_marker("start-losing", 240)
add_marker("start-losing-loop", 280)
add_marker("end-losing", 340)
add_marker("end-losing-straight", 360)
add_marker("start-jump", 380)
add_marker("start-jump-loop", 400)
add_marker("end-jump", 460)
add_marker("selection-start", 480)
add_marker("selection-end", 560)

# Helper to create material from image
def create_material(name, image_path):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    # Clear default nodes
    nodes.clear()
    # Create nodes
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (100, 0)
    # Principled defaults
    # For Blender 4.3, Principled BSDF inputs changed
    # Set base color via image
    if image_path and os.path.exists(image_path):
        tex_image = nodes.new(type='ShaderNodeTexImage')
        tex_image.location = (-300, 0)
        try:
            img = bpy.data.images.load(image_path, check_existing=True)
            img.name = os.path.basename(image_path)
            tex_image.image = img
        except Exception as e:
            print(f"Failed to load image {image_path}: {e}")
        links.new(tex_image.outputs['Color'], principled.inputs['Base Color'])
    else:
        print(f"Image not found for material {name}: {image_path}")

    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    # Set some defaults
    try:
        principled.inputs['Roughness'].default_value = 0.6
        principled.inputs['Metallic'].default_value = 0.0
    except:
        pass
    return mat

# Base path for textures
tex_base = "/home/user/tbone_kart/tbone"
# Need to ensure export path will have same textures, but Blender file will use absolute paths
# We'll also copy textures to final export folder (which is same as tex_base)
os.makedirs(tex_base, exist_ok=True)

mat_steak = create_material("Mat_Steak", os.path.join(tex_base, "steak_meat.png"))
mat_bone = create_material("Mat_Bone", os.path.join(tex_base, "bone.png"))
mat_kart_body = create_material("Mat_KartBody", os.path.join(tex_base, "kart_body.png"))
mat_chassis = create_material("Mat_Chassis", os.path.join(tex_base, "kart_chassis.png"))
mat_wheel = create_material("Mat_Wheel", os.path.join(tex_base, "wheel.png"))
mat_seat = create_material("Mat_Seat", os.path.join(tex_base, "seat.png"))
mat_license = create_material("Mat_License", os.path.join(tex_base, "license_plate.png"))
mat_steering = create_material("Mat_Steering", os.path.join(tex_base, "steering.png"))
mat_exhaust = create_material("Mat_Exhaust", os.path.join(tex_base, "exhaust.png"))
mat_headlight = create_material("Mat_Headlight", os.path.join(tex_base, "headlight.png"))

# Also create a dark material for details
mat_black = bpy.data.materials.new(name="Mat_Black")
mat_black.use_nodes = True
mat_black.node_tree.nodes.clear()
out = mat_black.node_tree.nodes.new('ShaderNodeOutputMaterial')
princ = mat_black.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
mat_black.node_tree.links.new(princ.outputs['BSDF'], out.inputs['Surface'])
princ.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1)
try:
    princ.inputs['Roughness'].default_value = 0.9
except:
    pass

# Helper to create mesh from vertices/faces
def create_mesh_object(name, verts, faces, material, smooth=False):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    # Calc normals
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material:
        mesh.materials.append(material)
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True
    # Set origin to geometry center? Keep at 0,0,0
    return obj

def uv_smart_project(obj):
    # Select and unwrap
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
    except Exception as e:
        print(f"UV project failed for {obj.name}: {e}")
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

# --- Load steak outline ---
steak_outline_path = "/tmp/steak_outline.json"
tbone_t_path = "/tmp/tbone_t.json"
steak_pts = json.loads(open(steak_outline_path).read())
# steak_pts are normalized x,y where y maps to Z in Blender, x to X, thickness along Y
# We have about 31 points; we'll use them to create a 2D profile in X-Z plane at Y=0, then extrude along Y
print(f"Steak points: {len(steak_pts)}")
# For kart, we need realistic size: max_dim mapping was 1.0 unit total; but we want steak size ~0.6 wide, 0.7 tall, thickness 0.15
scale_xy = 0.55  # scale factor for X-Z
thickness = 0.14

# Build vertices for steak body: extruded shape
# Create front face and back face vertices + sides
# verts: for each outline point, create two verts: front (Y = thickness/2) and back (Y = -thickness/2)
steak_verts = []
for x,y in steak_pts:
    # x is X, y is Z (height)
    # apply scale_xy
    X = x * scale_xy
    Z = y * scale_xy + 0.55 # elevate steak to sit in kart (center Z 0.55)
    # front
    steak_verts.append((X, thickness/2, Z))
    # back (will build second layer)
    # We'll actually interleave to make faces easier? Let's do front loop then back loop
# Actually we want separate lists
front_verts = []
back_verts = []
for x,y in steak_pts:
    X = x * scale_xy
    Z = y * scale_xy + 0.55
    front_verts.append((X, thickness/2, Z))
    back_verts.append((X, -thickness/2, Z))

# Combine: front first, then back
verts = front_verts + back_verts
n = len(steak_pts)
faces = []
# front face (fan triangulation via ear? Simpler use polygon as ngons? Blender supports n-gon for front face)
# front face is ngons: indices 0..n-1
faces.append(list(range(n)))  # front
# back face: indices n..2n-1 but reversed winding
faces.append(list(reversed(range(n, 2*n))))
# side faces: quads between front and back edges
for i in range(n):
    nxt = (i+1) % n
    # quad: front i -> front nxt -> back nxt -> back i
    faces.append([i, nxt, n+nxt, n+i])

steak_obj = create_mesh_object("SteakBody", verts, faces, mat_steak, smooth=False)
uv_smart_project(steak_obj)
print(f"Created steak body with {len(verts)} verts, {len(faces)} faces")

# --- Create bone T inset (thin plate slightly in front of steak) ---
# Use t_points from file
t_points = json.loads(open(tbone_t_path).read())
# Scale similarly but slightly smaller and raised
bone_scale = scale_xy * 0.95
bone_thickness = 0.02
# Bone sits on front face of steak: Y = thickness/2 + 0.005 + thin
bone_y_front = thickness/2 + 0.008
bone_y_back = thickness/2 + 0.008 + bone_thickness
bone_verts = []
for x,y in t_points:
    X = x * bone_scale
    Z = y * bone_scale + 0.55
    bone_verts.append((X, bone_y_front, Z))
    bone_verts.append((X, bone_y_back, Z)) # not needed extrude? We'll make double-sided thin

# Instead extrude similarly to steak but thinner: front and back
t_front = []
t_back = []
for x,y in t_points:
    X = x * bone_scale
    Z = y * bone_scale + 0.55
    t_front.append((X, bone_y_front, Z))
    t_back.append((X, bone_y_back, Z))

bv_verts = t_front + t_back
m = len(t_points)
bfaces = []
bfaces.append(list(range(m)))
bfaces.append(list(reversed(range(m, 2*m))))
for i in range(m):
    nxt = (i+1)%m
    bfaces.append([i, nxt, m+nxt, m+i])

bone_obj = create_mesh_object("SteakBone", bv_verts, bfaces, mat_bone, smooth=False)
uv_smart_project(bone_obj)

# --- Create arms ---
# Left arm: from shoulder on steak left side to steering wheel left grip
# Shoulder positions:
shoulder_y = 0.0  # mid thickness
shoulder_z = 0.50
left_shoulder_x = -0.21
right_shoulder_x = 0.21

steering_center = (0, 0.38, 0.40) # Y forward 0.38 is slightly in front of steak (steak y thickness/2 =0.07), so good
# steering wheel grips left/right at x +/-0.18, same y,z
left_grip = (-0.16, 0.38, 0.40)
right_grip = (0.16, 0.38, 0.40)

def create_cylinder_between(p1, p2, radius, name, material):
    # Create cylinder between two points
    # We compute length and midpoint, direction
    import mathutils
    v1 = mathutils.Vector(p1)
    v2 = mathutils.Vector(p2)
    mid = (v1+v2)/2
    length = (v2 - v1).length
    direction = (v2 - v1).normalized()
    # Default cylinder along Z; need to align Z to direction
    # Create mesh cube then scale? Easiest: create cylinder primitive and rotate
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, location=mid)
    obj = bpy.context.active_object
    obj.name = name
    # Compute rotation: axis Z to direction
    up = mathutils.Vector((0,0,1))
    if (direction - up).length > 1e-4:
        quat = up.rotation_difference(direction)
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = quat
        obj.rotation_mode = 'XYZ'
    # Assign material
    if material:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(material)
        else:
            obj.data.materials[0] = material
    # Smooth
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj

# Create arms with two segments for elbow bend for nicer look
# Left arm: shoulder -> elbow -> grip
left_elbow = (-0.22, 0.25, 0.45)
right_elbow = (0.22, 0.25, 0.45)

left_arm1 = create_cylinder_between((left_shoulder_x, shoulder_y, shoulder_z), left_elbow, 0.035, "ArmLeftUpper", mat_steak)
left_arm2 = create_cylinder_between(left_elbow, left_grip, 0.028, "ArmLeftLower", mat_steak)
right_arm1 = create_cylinder_between((right_shoulder_x, shoulder_y, shoulder_z), right_elbow, 0.035, "ArmRightUpper", mat_steak)
right_arm2 = create_cylinder_between(right_elbow, right_grip, 0.028, "ArmRightLower", mat_steak)

# Hands - small spheres at grips
def create_sphere(pos, radius, name, material):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=pos, segments=16, ring_count=12)
    obj = bpy.context.active_object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    return obj

left_hand = create_sphere(left_grip, 0.032, "HandLeft", mat_steak)
right_hand = create_sphere(right_grip, 0.032, "HandRight", mat_steak)

# --- Kart chassis ---
# We will create a stylized go-kart body as multiple parts combined into one mesh for SPM
# Main tub shape: let's design with vertices approximating go-kart

# Define kart body vertices in X-Y plane, Z up
# We'll create a low-poly body with rounded nose using sub-divided points
# Outline for top view (X width, Y length):
kart_outline = [
    (-0.42, -0.68), # rear left
    (0.42, -0.68),  # rear right
    (0.44, -0.45),  # rear fender bulge right
    (0.40, -0.10),  # mid right
    (0.36, 0.35),   # front right side before nose taper
    (0.20, 0.60),   # nose right
    (0.0, 0.72),    # nose tip
    (-0.20, 0.60),  # nose left
    (-0.36, 0.35),  # front left
    (-0.40, -0.10), # mid left
    (-0.44, -0.45), # rear fender left
]

# Extrude height layers:
# Bottom plate Z=0.18, top edge Z=0.32, cockpit walls Z=0.38 etc
# We'll create a simple tub with floor and walls, but as single mesh with thickness

# Build bottom face vertices (Z=0.18)
floor_z = 0.18
wall_top_z = 0.35
cockpit_floor_z = 0.22  # lower floor for seat

# Create floor polygon (full outline) at floor_z
floor_verts = [(x, y, floor_z) for x,y in kart_outline]
# Create wall top vertices (same XY, higher Z)
wall_top_verts = [(x, y, wall_top_z) for x,y in kart_outline]

# For cockpit opening: we need inner walls to create hollow cockpit
# Cockpit inner outline: smaller
cockpit_outline = [
    (-0.28, -0.35),
    (0.28, -0.35),
    (0.26, 0.05),
    (0.18, 0.18),
    (0.0, 0.20),
    (-0.18, 0.18),
    (-0.26, 0.05),
]
cockpit_floor_verts = [(x,y, cockpit_floor_z) for x,y in cockpit_outline]
cockpit_wall_top = [(x,y, wall_top_z) for x,y in cockpit_outline] # actually walls top same as outer?

# Build vertices list
verts_kart = []
verts_kart.extend(floor_verts) # 0..10
verts_kart.extend(wall_top_verts) # 11..21
verts_kart.extend(cockpit_floor_verts) # 22..28
verts_kart.extend(cockpit_wall_top) # 29..35

# Faces: we need to construct manifold mesh manually
# 1. Bottom face outer floor (ngon)
faces_kart = []
faces_kart.append(list(range(0, 11)))
# 2. Outer walls: quads between floor and wall top (sides)
n_out = len(kart_outline)
for i in range(n_out):
    nxt = (i+1) % n_out
    # quad: floor i -> floor nxt -> wall_top nxt -> wall_top i
    faces_kart.append([i, (i+1)%n_out, n_out + (i+1)%n_out, n_out + i])

# 3. Cockpit floor (ngon)
c_start = 22
c_n = len(cockpit_outline)
faces_kart.append(list(range(c_start, c_start+c_n)))
# 4. Cockpit inner walls: between cockpit floor and cockpit wall top
c_wall_start = 29
for i in range(c_n):
    nxt = (i+1) % c_n
    faces_kart.append([c_start+i, c_wall_start+i, c_wall_start+nxt, c_start+nxt])

# 5. Top rim bridging outer wall top to inner cockpit wall top: This is a bit complex polygon with hole
# We can create rim as triangulated via simple fans: connect outer outline to inner cockpit outline
# For simplicity, bridge rear section and side sections as quads manually:
# We'll create rim faces using closest correspondences:
# Rough mapping: outer 0-1 rear edge to inner 0-1, etc. We'll craft manual.
# Define mapping for rim: outer indices 0..10, inner indices 29..35
# Create rim quads:
# Rear wall: outer 0-1 top vs inner 0-1 top
faces_kart.append([11+0, 11+1, c_wall_start+1, c_wall_start+0]) # rear top
# Right rear side: outer 1-2-3 etc to inner 1-2
faces_kart.append([11+1, 11+2, c_wall_start+1, c_wall_start+1]) # degenerate? skip detailed - use simpler: just cap with outer top as deck
# Alternative: For simplicity, we skip detailed rim and just close outer top as separate deck with hole boolean not needed
# Instead we already have outer walls; to close top we need deck face that is outer outline minus inner cockpit hole
# We can approximate by creating deck as two polygons: front deck and rear deck
# Front deck: outer nose 5-8 + inner 3-5 forms a quad-like shape
# Let's add front deck face as fan covering nose area:
front_deck_indices = [11+5, 11+6, 11+7, c_wall_start+4, c_wall_start+3] # rough
faces_kart.append(front_deck_indices)
# Side decks (left and right)
right_deck = [11+2, 11+3, 11+4, c_wall_start+2, c_wall_start+1]
faces_kart.append(right_deck)
left_deck = [11+8, 11+9, 11+10, c_wall_start+0, c_wall_start+6, c_wall_start+5]
faces_kart.append(left_deck)
# Rear deck: behind cockpit
rear_deck = [11+0, c_wall_start+0, c_wall_start+1, 11+1]
# already added as rear top, so skip duplicate

kart_body_obj = create_mesh_object("KartBody", verts_kart, faces_kart, mat_kart_body, smooth=False)
# Apply auto smooth? Add subdivision? We'll keep low poly but add bevel modifier for nice edges
mods = kart_body_obj.modifiers.new(name="Bevel", type='BEVEL')
mods.width = 0.02
mods.segments = 2
mods.limit_method = 'ANGLE'
mods.angle_limit = 0.785398

uv_smart_project(kart_body_obj)

# --- Seat ---
# Simple seat block behind driver, with backrest
seat_verts = [
    (-0.26, -0.40, 0.20), # base left rear
    (0.26, -0.40, 0.20),  # base right rear
    (0.26, -0.10, 0.20),  # base right front
    (-0.26, -0.10, 0.20), # base left front
    (-0.26, -0.40, 0.50), # back top left
    (0.26, -0.40, 0.50),  # back top right
    (0.26, -0.38, 0.48),  # back inset
    (-0.26, -0.38, 0.48),
]
seat_faces = [
    [0,1,2,3], # bottom
    [0,4,5,1], # back outward
    [1,5,6,2], # right side
    [2,6,7,3], # front? Actually seat interior
    [3,7,4,0], # left side
    [4,7,6,5], # top back
]
seat_obj = create_mesh_object("Seat", seat_verts, seat_faces, mat_seat, smooth=False)
uv_smart_project(seat_obj)

# --- License plate ---
plate_pos = (0, -0.69, 0.32)
# plate dims 0.30 wide, 0.14 tall
pw = 0.30/2
ph = 0.14/2
plate_verts = [
    (-pw, -0.69, 0.32 - ph),
    (pw, -0.69, 0.32 - ph),
    (pw, -0.69, 0.32 + ph),
    (-pw, -0.69, 0.32 + ph),
]
plate_faces = [[0,1,2,3]]
plate_obj = create_mesh_object("LicensePlate", plate_verts, plate_faces, mat_license, smooth=False)
# Need to set UV to map correctly - planar
# Smart project again
uv_smart_project(plate_obj)

# --- Exhaust pipes (two cylinders at rear) ---
def create_exhaust(pos, direction, length, radius):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, location=pos)
    obj = bpy.context.active_object
    obj.name = "Exhaust"
    # direction along Y (since pos Y is forward)
    # Cylinder default along Z, rotate to align Y
    obj.rotation_euler[0] = math.radians(90)
    # slight upward tilt
    obj.rotation_euler[1] = math.radians(5)
    if mat_exhaust:
        obj.data.materials.append(mat_exhaust)
    return obj

exhaust_left = create_exhaust((-0.18, -0.71, 0.28), (0,1,0), 0.18, 0.035)
exhaust_left.name = "ExhaustLeft"
exhaust_right = create_exhaust((0.18, -0.71, 0.28), (0,1,0), 0.18, 0.035)
exhaust_right.name = "ExhaustRight"

# --- Steering wheel column and wheel ---
# Column: cylinder from dashboard to steering center
col_top = steering_center
col_bottom = (0, 0.30, 0.28)
steer_col = create_cylinder_between(col_bottom, col_top, 0.018, "SteeringColumn", mat_black)

# Steering wheel: torus
bpy.ops.mesh.primitive_torus_add(major_radius=0.14, minor_radius=0.018, major_segments=24, minor_segments=12, location=steering_center)
steer_wheel = bpy.context.active_object
steer_wheel.name = "SteeringWheel"
# Tilt wheel ~ 40 degrees towards driver (rotate around X)
steer_wheel.rotation_euler[0] = math.radians(55)
steer_wheel.rotation_euler[2] = math.radians(0)
if mat_steering:
    steer_wheel.data.materials.append(mat_steering)
# Smooth
for poly in steer_wheel.data.polygons:
    poly.use_smooth = True

# Dashboard/instrument panel small cube
dash_verts = [
    (-0.20, 0.38, 0.32),
    (0.20, 0.38, 0.32),
    (0.18, 0.45, 0.33),
    (-0.18, 0.45, 0.33),
    (-0.20, 0.38, 0.35),
    (0.20, 0.38, 0.35),
    (0.18, 0.45, 0.36),
    (-0.18, 0.45, 0.36),
]
dash_faces = [
    [0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]
]
dash_obj = create_mesh_object("Dashboard", dash_verts, dash_faces, mat_black, smooth=False)
uv_smart_project(dash_obj)

# --- Headlights ---
def create_headlight(pos):
    bpy.ops.mesh.primitive_cube_add(size=0.10, location=pos)
    obj = bpy.context.active_object
    obj.name = "Headlight"
    obj.scale = (1.2, 0.5, 0.8)
    # Add material
    if mat_headlight:
        obj.data.materials.append(mat_headlight)
    # mark as headlight type? We'll set custom property later
    obj["type"] = "HEADLIGHT"
    obj["headlight_color"] = "255 245 200"
    return obj

hl_left = create_headlight((-0.20, 0.68, 0.30))
hl_left.name = "HeadlightLeft"
hl_left["type"] = "HEADLIGHT"
hl_right = create_headlight((0.20, 0.68, 0.30))
hl_right.name = "HeadlightRight"
hl_right["type"] = "HEADLIGHT"

# --- Nitro emitters (small cubes for position) ---
def create_nitro(pos, name):
    bpy.ops.mesh.primitive_cube_add(size=0.04, location=pos)
    obj = bpy.context.active_object
    obj.name = name
    obj.hide_render = True  # not rendered? But exporter includes? We'll keep visible but hidden? Docs say nitro-emitter type
    obj["type"] = "NITRO-EMITTER"
    # Hide in viewport maybe but not needed
    obj.display_type = 'WIRE'
    return obj

nitro_a = create_nitro((0.16, -0.70, 0.30), "NitroA")
nitro_b = create_nitro((-0.16, -0.70, 0.30), "NitroB")

# --- Wheels ---
# Create wheels as cylinders along X axis
def create_wheel(pos, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=0.12, location=pos)
    obj = bpy.context.active_object
    obj.name = name
    # Cylinder aligned along Z, we want axis along X
    obj.rotation_euler[1] = math.radians(90)
    obj.rotation_euler[2] = 0
    # add material
    if mat_wheel:
        obj.data.materials.append(mat_wheel)
    # set STK type
    obj["type"] = "WHEEL"
    # Ensure origin is at center (already)
    return obj

wheel_fl = create_wheel((-0.38, 0.38, 0.16), "WheelFrontLeft")
wheel_fr = create_wheel((0.38, 0.38, 0.16), "WheelFrontRight")
wheel_rl = create_wheel((-0.42, -0.45, 0.16), "WheelRearLeft")
wheel_rr = create_wheel((0.42, -0.45, 0.16), "WheelRearRight")

# --- Front spoiler / splitter (small aero) ---
splitter_verts = [
    (-0.36, 0.68, 0.16),
    (0.36, 0.68, 0.16),
    (0.32, 0.72, 0.17),
    (-0.32, 0.72, 0.17),
    (-0.36, 0.68, 0.20),
    (0.36, 0.68, 0.20),
    (0.32, 0.72, 0.21),
    (-0.32, 0.72, 0.21),
]
splitter_faces = [
    [0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]
]
splitter_obj = create_mesh_object("FrontSplitter", splitter_verts, splitter_faces, mat_chassis, smooth=False)
uv_smart_project(splitter_obj)

# Additional aesthetic: floor shadow catcher? Not needed

print("=== Geometry creation done ===")

# Save blend file
blend_path = "/home/user/tbone_kart/tbone.blend"
try:
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved blend to {blend_path}")
except Exception as e:
    print(f"Save blend failed: {e}")

# Now export kart via addon logic
# We need to set preferences for export path, but we will call exportKart directly

# Ensure output dir exists (same as tex_base)
export_path = tex_base
os.makedirs(export_path, exist_ok=True)
print(f"Export path: {export_path}")

# Import the kart exporter
import importlib.util, pathlib, sys
sys.path.append("/home/user/stk-blender/io_antarctica_scene")
try:
    from io_antarctica_scene import stk_kart, stk_utils
except:
    # Try alternative import
    import stk_kart

# We need to create a dummy operator self with report method to pass to export functions
class DummyOp:
    def report(self, level, msg):
        print(f"{level}: {msg}")

dummy = DummyOp()

# Call exportKart
try:
    # stk_kart.exportKart expects self, path
    stk_kart.exportKart(dummy, export_path)
    print("Kart export completed")
except Exception as e:
    print(f"Export failed: {e}")
    import traceback
    traceback.print_exc()
    # fallback: manually create kart.xml
    print("Creating fallback kart.xml manually")
    kart_xml = f'''<?xml version=\"1.0\" encoding=\"utf-8\"?>
<kart name              = \"T-Bone\"
      version           = \"3\"
      model-file        = \"tbone.spm\"
      icon-file         = \"tbone_icon.png\"
      minimap-icon-file = \"tbone_icon.png\"
      shadow-file       = \"tbone_shadow.png\"
      type              = \"medium\"
      groups            = \"Add-Ons\"
      rgb               = \"0.35 0.06 0.06\" >
  <sounds engine = \"large\">
      <skid name=\"default\"/>
  </sounds>
  <animations left = \"0\"
              straight = \"19\"
              right = \"39\"
              start-winning = \"79\"
              start-winning-loop = \"119\"
              end-winning = \"199\"
              start-losing = \"239\"
              start-losing-loop = \"279\"
              end-losing = \"339\"
              start-jump = \"379\"
              start-jump-loop = \"399\"
              end-jump = \"459\"
              selection-start = \"479\"
              selection-end = \"559\"/>
  <wheels>
    <front-left position = \"-0.380000 0.160000 0.380000\"
                 model    = \"wheel-front-left.spm\"       />
    <front-right position = \"0.380000 0.160000 0.380000\"
                 model    = \"wheel-front-right.spm\"       />
    <rear-left position = \"-0.420000 0.160000 -0.450000\"
                 model    = \"wheel-rear-left.spm\"       />
    <rear-right position = \"0.420000 0.160000 -0.450000\"
                 model    = \"wheel-rear-right.spm\"       />
  </wheels>
  <nitro-emitter>
    <nitro-emitter-a position = \"0.160000 0.300000 -0.700000\" />
    <nitro-emitter-b position = \"-0.160000 0.300000 -0.700000\" />
  </nitro-emitter>
  <headlights>
    <object position=\"-0.200000 0.300000 0.680000\"
            rotation=\"0.000000 -0.000000 0.000000\"
            scale=\"1.000000 1.000000 1.000000\"
            model=\"HeadlightLeft.spm\"/>
    <object position=\"0.200000 0.300000 0.680000\"
            rotation=\"0.000000 -0.000000 0.000000\"
            scale=\"1.000000 1.000000 1.000000\"
            model=\"HeadlightRight.spm\"/>
  </headlights>
  <exhaust file=\"kart_exhaust.xml\"/>
</kart>
'''
    open(os.path.join(export_path, "kart.xml"), "w").write(kart_xml)
    print("Fallback kart.xml written")

print("Done")
# List export dir
import os
print(os.listdir(export_path))
