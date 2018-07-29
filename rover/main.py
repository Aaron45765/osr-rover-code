#!/usr/bin/env python
import time
from osr import Rover
from arguments import Arguments
import json
from websocket import create_connection
import math

'''
This code runs the JPL Open Source Rover. It accepts a few command line arguments for different functionality
   -s : Attempts to connect to a Unix socket for controlling the LED screen. The screen.py script must be running
               previous to this in order to work. It lives at ../led/screen.py
   -x : Attemps to connect to a remote Xbox Controller to recieve drive commands
   -b : Attmpts to connect to a remote Bluetooth device to recieve drive commands

An example line running this script to run the LED screen and with an Xbox controller
    sudo python main.py -s -x
''' 


def main():
    args = Arguments()
    with open('config.json') as f:
        config = json.load(f)

    rover = Rover(config,args.bt_flag,args.xbox_flag,args.unix_flag)
    
    # while True:
    # 	try:
    # 		rover.drive()
    # 		time.sleep(0.1)

    # 	except Exception as e:
    # 		print e
    # 		rover.cleanup()
    # 		time.sleep(0.5)
    # 		rover.connectController()
    ws = create_connection("ws://159.65.105.241:4444/websocket")
    result = None
    points = []
    point = [0,0]
    alone=[]
    while result==None:
        result =  ws.recv()
    ws.close()
    pairs = result.split('|')
    for x in pairs:
        coord = x.split(',')
        alone+=coord
    for x in range(0,len(alone),2):
        points.append([float(alone[x]),float(alone[x+1])])
    print points 
    turning_radius = 2
    # we get these things
    vectors = [[0 for x in range(2)] for x in range(len(points)-1)]
    nvectors = [[0 for x in range(2)] for x in range(len(points)-1)]
    angles = [[0] for x in range(len(points)-2)]
    cosines = [[0] for x in range(len(points)-2)]
    linelengths = [0 for x in range(len(vectors))]
    straightcommands = [0 for x in range(len(vectors))]
    arccommands = [0 for x in range(len(angles))]
    directional = [0 for x in range(len(angles))]
    truncated = [0 for x in range(len(angles))]

    for x in range(1, len(points)):
        vectors[x-1][0]= points[x][0]-points[x-1][0]
        vectors[x-1][1]= points[x][1]-points[x-1][1]
        mag = vectors[x-1][0]**2 + vectors[x-1][1]**2
        mag = math.sqrt(mag)
        nvectors[x-1][0] = vectors[x-1][0]/mag
        nvectors[x-1][1] = vectors[x-1][1]/mag
    for x in range(len(vectors)-1):
        cosines[x] = -nvectors[x][0]*nvectors[x+1][0] -nvectors[x][1]*nvectors[x+1][1]
        angles[x] = math.acos(cosines[x])
    for x in range(len(vectors)):
        linelengths[x] = math.sqrt(vectors[x][0]**2 + vectors[x][1]**2)
    for x in range(len(angles)):
        truncated[x] = turning_radius*math.sqrt(1.0+cosines[x])/(math.sqrt(1.0-cosines[x]))
        for x in range(len(points)-2):
            newvec = [0,0]
            newvec[0] = points[x+2][0]-points[x][0]
            newvec[1] = points[x+2][1]-points[x][1]
        if vectors[x][0]*newvec[1]-vectors[x][1]*newvec[0]>0:
            directional[x]=0
        else:
            directional[x]=1


    for x in range(len(linelengths)):
        if(x == 0):
            firsttruncated = 0
            lasttruncated = truncated[x]
            linelengths[x] -= firsttruncated+lasttruncated
        elif(x == len(linelengths)-1):
            firsttruncated = truncated[len(linelengths)-2]
            lasttruncated = 0
            linelengths[x] -= firsttruncated+lasttruncated
        else:
            firsttruncated = truncated[x-1]
            lasttruncated = truncated[x]
            linelengths[x] -= firsttruncated+lasttruncated

    straightcommands = linelengths

    for x in range(len(arccommands)):
        arccommands[x] = angles[x] * turning_radius

    for x in range(len(arccommands)):
        rover.takeStraight(straightcommands[x])
        rover.takeTurn(arccommands[x], directional[x])
    
    rover.takeStraight(straightcommands[len(straightcommands)-1])
    rover.cleanup()


if __name__ == '__main__':
    main()
