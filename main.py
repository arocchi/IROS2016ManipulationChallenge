from klampt import *
from klampt import visualization
from klampt import resource
from klampt.simulation import *
from klampt.glrobotprogram import *
import importlib
import os
import time


moving_base_template_fn = 'data/robots/moving_base_template.rob'
object_template_fn = 'data/objects/object_template.obj'
objects = {}
objects['ycb'] = [f for f in os.listdir('data/objects/ycb')]
objects['apc2015'] = [f for f in os.listdir('data/objects/apc2015')]
robots = ['reflex_col', 'soft_hand', 'reflex']

object_geom_file_patterns = {
	'ycb':'data/objects/ycb/%s/meshes/tsdf_mesh.stl',
	'apc2015':'data/objects/apc2015/%s/textured_meshes/optimized_tsdf_textured_mesh.ply'
}
#default mass for objects whose masses are not specified, in kg
default_object_mass = 0.5
object_masses = {
	'ycb':dict(),
	'apc2015':dict(),
}
robot_files = {
	'reflex_col':'data/robots/reflex_col.rob',
	'soft_hand':'data/robots/soft_hand.urdf',
	'reflex':'data/robots/reflex.rob'
}


def mkdir_p(path):
	"""Quietly makes the directories in path"""
	import os, errno
	try:
		os.makedirs(path)
	except OSError as exc: # Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else: raise

def make_object(object_set,objectname,world):
	"""Adds an object to the world using its geometry / mass properties
	and places it in a default location (x,y)=(0,0) and resting on plane."""
	objfile = object_geom_file_patterns[object_set]%(objectname,)
	objmass = object_masses[object_set].get('mass',default_object_mass)
	f = open(object_template_fn,'r')
	pattern = ''.join(f.readlines())
	f.close()
	f2 = open("temp.obj",'w')
	f2.write(pattern % (objfile,objmass))
	f2.close()
	world.loadElement('temp.obj')
	obj = world.rigidObject(world.numRigidObjects()-1)
	bmin,bmax = obj.geometry().getBB()
	T = obj.getTransform()
	spacing = 0.005
	T = (T[0],vectorops.add(T[1],(-(bmin[0]+bmax[0])*0.5,-(bmin[1]+bmax[1])*0.5,-bmin[2]+spacing)))
	obj.setTransform(*T)
	obj.appearance().setColor(0.2,0.5,0.7,1.0)
	return obj

def make_moving_base_robot(robotname,world):
	"""Converts the given fixed-base robot into a moving base robot
	and loads it into the given world.
	"""
	f = open(moving_base_template_fn,'r')
	pattern = ''.join(f.readlines())
	f.close()
	f2 = open("temp.rob",'w')
	f2.write(pattern 
		% (robot_files[robotname],robotname))
	f2.close()
	world.loadElement("temp.rob")
	return world.robot(world.numRobots()-1)

def set_moving_base_xform(robot,R,t):
	"""For a moving base robot model, set the current base rotation
	matrix R and translation t.  (Note: if you are controlling a robot
	during simulation, use send_moving_base_xform_command)
	"""
	q = robot.getConfig()
	for i in range(3):
		q[i] = t[i]
	roll,pitch,yaw = so3.rpy(R)
	q[3]=yaw
	q[4]=pitch
	q[5]=roll
	robot.setConfig(q)

def send_moving_base_xform_linear(controller,R,t,dt):
	"""For a moving base robot model, send a command to move to the
	rotation matrix R and translation t using linear interpolation
	over the duration dt.

	Note: with the reflex model, can't currently set hand commands
	and linear base commands simultaneously
	"""
	q = controller.getCommandedConfig()
	for i in range(3):
		q[i] = t[i]
	roll,pitch,yaw = so3.rpy(R)
	q[3]=yaw
	q[4]=pitch
	q[5]=roll
	controller.setLinear(q,dt)

def send_moving_base_xform_PID(controller,R,t):
	"""For a moving base robot model, send a command to move to the
	rotation matrix R and translation t by setting the PID setpoint

	Note: with the reflex model, can't currently set hand commands
	and linear base commands simultaneously
	"""
	q = controller.getCommandedConfig()
	for i in range(3):
		q[i] = t[i]
	roll,pitch,yaw = so3.rpy(R)
	q[3]=yaw
	q[4]=pitch
	q[5]=roll
	v = controller.getCommandedVelocity()
	controller.setPIDCommand(q,v)

def launch_simple(robotname,object_set,objectname):
	world = WorldModel()
	world.loadElement("data/terrains/plane.env")
	robot = make_moving_base_robot(robotname,world)
	object = make_object(object_set,objectname,world)
	doedit = True
	xform = resource.get("%s/default_initial_%s.xform"%(object_set,robotname),description="Initial hand transform",default=robot.link(5).getTransform(),world=world)
	set_moving_base_xform(robot,xform[0],xform[1])
	xform = resource.get("%s/initial_%s_%s.xform"%(object_set,robotname,objectname),description="Initial hand transform",default=robot.link(5).getTransform(),world=world,doedit=False)
	if xform:
		set_moving_base_xform(robot,xform[0],xform[1])
	xform = resource.get("%s/initial_%s_%s.xform"%(object_set,robotname,objectname),description="Initial hand transform",default=robot.link(5).getTransform(),world=world,doedit=doedit)
	if not xform:
		print "User quit the program"
		return
	#this sets the initial condition for the simulation
	set_moving_base_xform(robot,xform[0],xform[1])

	#now the simulation is launched
	program = GLSimulationProgram(world)
	sim = program.sim
	#create a hand emulator from the given robot name
	module = importlib.import_module('plugins.'+robotname)
	#emulator takes the robot index (0), start link index (6), and start driver index (6)
	hand = module.HandEmulator(sim,0,6,6)
	sim.addEmulator(0,hand)

	#setup some simulation parameters
	visPreshrink = True
	for l in range(robot.numLinks()):
		sim.body(robot.link(l)).setCollisionPreshrink(visPreshrink)
	for l in range(world.numRigidObjects()):
		sim.body(world.rigidObject(l)).setCollisionPreshrink(visPreshrink)

	#By running this program you get a little more control over the simulation run, but it is
	#incompatible with the Qt resource editor...
	#program.run()
	#start the simulation
	visualization.add("world",world)
	visualization.show()

	print "waiting for the user to prepare for recording"
	time.sleep(10)

	if robotname in ['reflex_col', 'reflex']:
		# send a command to the hand: f1,f2,f3,preshape
		hand.setCommand([0.2, 0.2, 0.2, 0])
	elif robotname == 'soft_hand':
		# send a command to the hand: synergy
		hand.setCommand([0.8])

	t_lift = 1.5
	lift_traj_duration = 0.5
	wait_after_start = 5.0
	t0 = time.time()

	program.saveScreenshots = True
	program.nextScreenshotTime = sim.getTime()
	print "Started recording"

	while visualization.shown():
		if sim.getTime() > t_lift:
			if robotname == 'reflex_col':
				desired = se3.mul((so3.identity(), [0, 0, 0.10]), xform)
				send_moving_base_xform_linear(sim.controller(0),desired[0],desired[1],lift_traj_duration)
			elif robotname in ['soft_hand', 'reflex']:
				t_traj = min(1, max(0, (sim.getTime()-t_lift)/lift_traj_duration))
				desired = se3.mul((so3.identity(), [0, 0, 0.10*t_traj]), xform)
				send_moving_base_xform_PID(sim.controller(0), desired[0], desired[1])

		if sim.getTime() >= wait_after_start and program.saveScreenshots:
			program.saveScreenshots = False
			print "Stopped recording"

		visualization.lock()
		sim.simulate(0.01)
		sim.updateWorld()

		if program.saveScreenshots and sim.getTime() >= program.nextScreenshotTime:
			program.save_screen("image%04d.ppm" % (program.screenshotCount))
			program.screenshotCount += 1
			program.nextScreenshotTime += 1.0 / 30.0;

		visualization.unlock()
		t1 = time.time()
		time.sleep(max(0.01-(t1-t0),0.001))
		t0 = t1

import random
try:
	dataset = sys.argv[1]
except IndexError:
	dataset = random.choice(objects.keys())
try:
	index = int(sys.argv[2])
except IndexError:
	index = random.randint(0,len(objects[dataset])-1)
try:
	robotname = sys.argv[3]
	if robotname not in robots:
		print "unknown robot", robotname
		robotname = "reflex_col"

except IndexError:
	robotname = "reflex_col"
launch_simple(robotname, dataset, objects[dataset][index])
visualization.kill()
