import numpy as np
import socket
import struct
from multiprocessing import Process, Queue
import pyqtgraph as pg
from pylsl import StreamInlet, resolve_byprop
import traceback

import time


def dataReaderLSL(streamName, q):
    while True:
        print("Waiting for LSL stream")
        try:
            results = resolve_byprop(prop='name', value=streamName)
            while len(results) == 0:
                time.sleep(0.25)
            info = results[0]
            inlet = StreamInlet(info, recover=False)
            print("Streaming...")
            # Read data in forever
            try:
                while True:
                    data = inlet.pull_sample()
                    if data:
                        q.put(np.array(data[0]))
                    time.sleep(1/200)
            except Exception as e:
                print(e)
                pass
        except Exception as e:
            print(e)
            pass

def dataReaderLSLChunk(streamName, q):
    while True:
        print("Waiting for LSL stream")
        try:
            results = resolve_byprop(prop='name', value=streamName)
            while len(results) == 0:
                time.sleep(0.25)
            info = results[0]
            inlet = StreamInlet(info, recover=False)
            print("Streaming...")
            # Read data in forever
            try:
                while True:
                    chunk, timestamps = inlet.pull_chunk()
                    if len(chunk) > 0:
                        q.put(np.array(chunk[len(chunk) - 1]))
                    time.sleep(1/120)
            except Exception as e:
                print(e)
                pass
        except Exception as e:
            print(e)
            pass

def dataReaderLSLWithChannelInfo(streamName, q, channelLabels):
    while True:
        print("Waiting for LSL stream")
        try:
            results = resolve_byprop(prop='name', value=streamName)
            while len(results) == 0:
                results = resolve_byprop(prop='name', value=streamName)
                time.sleep(0.25)
            info = results[0]
            inlet = StreamInlet(info, recover=False)

            info = inlet.info()
            ch = info.desc().child("channels").child("channel")
            for k in range(info.channel_count()):
                channelLabels.append(ch.child_value("label"))
                ch = ch.next_sibling()

            #print("In dataReader: ")
            #print(channelLabels)
            print("Streaming...")
            # Read data in forever
            try:
                while True:   
                    data = inlet.pull_sample()
                    if data:
                        q.put(np.array(data[0]))
                    time.sleep(1/1000000)
            except Exception as e:
                print(e)
                pass
        except Exception as e:
            print(traceback.format_exc())
            pass


def dataReaderTCP(ip, port, n, q):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip, port)
    sock.bind(server_address)
    sock.listen(1)
    print("Waiting for a TCP connection")
    connection, client_address = sock.accept()
    print("Streaming...")
    unpacker = struct.Struct("!"+str(n) + "d")
    try:
        while True:
            try:
                print("Waiting for sample")
                print(unpacker.size)
                data = connection.recv(unpacker.size)
                values = unpacker.unpack(data)
                q.put(values)
                print(q.qsize())
            except Exception as e:
                print(e)
                pass
    finally:
        connection.close()