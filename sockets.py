#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import flask
from flask import Flask, request
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()
        
    def add_set_listener(self, listener):
        self.listeners.append( listener )

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners( entity )

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners( entity )

    def update_listeners(self, entity):
        '''update the set listeners'''
        for listener in self.listeners:
            listener(entity, self.get(entity))

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self):
        return self.space




#the client stuff was taken from Abram Hindle's webSocket Examples at
#https://github.com/abramhindle/WebSocketsExamples
class Client:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, data):
        self.queue.put_nowait(data)

    def get(self):
        return self.queue.get()




myWorld = World() 
clientList = list()

def set_listener( entity, data ):
    ''' do something with the update ! '''
    #data should have the id and the new value
	#myWorld.update(entity, data.Keys()[0], data)  


myWorld.add_set_listener( set_listener )
        
@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    return flask.redirect("/static/index.html")

def read_ws(ws,client):
    '''A greenlet function that reads from the websocket and updates the world'''
    # XXX: TODO IMPLEMENT ME
    #read the msg from ws and set the variables appropriately in world 

    '''A greenlet function that reads from the websocket'''
    try:
        while True:
            msg = ws.receive()
            print "WS RECV: %s" % msg
            if (msg is not None):
                if(msg == "newConnection"):
                    client.put(json.dumps(myWorld.world()))
                    #if it's a new client give them the whole world
                    #so they can see it 

                else:
                    packet = json.loads(msg)
                    for key in packet.keys():
                        for attribute in packet[key].keys():
                            myWorld.update(key, attribute, packet[key][attribute])

                    for client in clientList:
                        client.put(json.dumps(packet))
                
            else:
                break
    except:
        '''Done'''    

    return None

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    # XXX: TODO IMPLEMENT ME
    client = Client()
    clientList.append(client)
    g = gevent.spawn( read_ws, ws, client )    
    try:
        while True:
            # block here
            msg = client.get()
            ws.send(msg)
    except Exception as e:# WebSocketError as e:
        print "WS Error %s" % e
    finally:
        clients.remove(client)
        gevent.kill(g)		

def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data != ''):
        return json.loads(request.data)
    else:
        return json.loads(request.form.keys()[0])

@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    jsonData = flask_post_json()
    if request.method == 'PUT':
        myWorld.set(entity,jsonData)

    if request.method == "POST":
        print jsonData
        for key in jsonData.keys():
            myWorld.update(entity,key,jsonData[key])

    result = myWorld.get(entity)
    return json.dumps(result)

@app.route("/world", methods=['POST','GET'])    
def world():
    '''you should probably return the world here'''
    return flask.jsonify(myWorld.world())

@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    return flask.jsonify(myWorld.get(entity))


@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    myWorld.clear()
    return flask.jsonify(myWorld.world())

if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
