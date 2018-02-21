import random
import string
from collections import Counter
import json
import os
import subprocess
import requests as req
import time

NODE_COUNTER = 2
PRINT_HTTP_REQUESTS = False
PRINT_HTTP_RESPONSES = False

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
FAIL = '\033[91m'
ENDC = '\033[0m'

class Node:
    
    def __init__(self, access_port, ip, node_id):
        self.access_port = access_port
        self.ip = ip
        self.id = node_id

    def __repr__(self):
        s = self.ip + " " + self.access_port + " " + self.id[:7]
        return s

def generate_random_keys(n):
    alphabet = string.ascii_lowercase
    keys = []
    for i in range(n):
        key = ''
        for _ in range(10):
            key += alphabet[random.randint(0, len(alphabet) - 1)]
        keys.append(key)
    return keys

def send_get_request(hostname, node, key):
    owner, value = None, None
    try:
        if PRINT_HTTP_REQUESTS:
            print "GET request: http://" + hostname + ":" + node.access_port + "/kvs?key=" + key
        r = req.get("http://" + hostname + ":" + node.access_port + "/kvs?key=" + key)
        if PRINT_HTTP_RESPONSES:
            print "Response:", r.text, r.status_code
        d = r.json()
       # print "http://" + hostname + ":" + node.access_port + "/kvs/" + key
       # print d
        owner = d['owner']
        value = d['value']
    except Exception as e:
        print "THE FOLLOWING GET REQUEST RESULTED IN AN ERROR: http://" + hostname + ":" + node.access_port + "/kvs/" + key
        print "Cannot retrieve key " + str(key) + " that should be present in the kvs"
       # exit(1)
    return owner, value
    
def send_put_request(hostname, node, key, value):
    #print "sending put request " + "http://" + hostname + ":" + node.access_port + "/kvs/" + key
    if PRINT_HTTP_REQUESTS:
        print "PUT request:" + "http://" + hostname + ":" + node.access_port + "/kvs; key " + key +" and value " + str(value)
    r = req.put("http://" + hostname + ":" + node.access_port + "/kvs", data={'key': key, 'value':value})
    if PRINT_HTTP_RESPONSES:
        print "Response:", r.text, r.status_code
    d = r.json()
    #print r.text
    return d['owner'], d['msg']

def add_keys(hostname, nodes, keys, value):
    d = {}
    for n in nodes:
        d[n.ip + ":8080"] = 0
    for key in keys:
        owner, msg = send_put_request(hostname, nodes[random.randint(0, len(nodes) - 1)], key, value)
        #print "Added key " + key  + " to node " + owner 
        d[owner] += 1
    return d

def get_keys_distribution_old(hostname, nodes, keys):
    d = {}
    for n in nodes:
        d[n.ip + ":8080"] = 0
    for key in keys:
        owner, val = send_get_request(hostname, nodes[random.randint(0, len(nodes) - 1)], key)
        if owner is not None:
            d[owner] += 1
    return d

def get_keys_distribution(hostname, nodes, keys):
    d = {}
    for n in nodes:
        request_node = hostname + ":808" + str(n.ip.split(".")[3])
        if PRINT_HTTP_REQUESTS:
            print "GET request: http://" +request_node +"/kvs/get_number_of_keys" 
        res = req.get("http://" +request_node +"/kvs/get_number_of_keys")
        count = res.json()['count']
        d[request_node] = count
    return d
        
def add_node_to_kvs(hostname, cur_node, new_node):
    if PRINT_HTTP_REQUESTS:
        print "PUT request: " + "http://" + hostname + ":" + cur_node.access_port + "/kvs/view_update" + "; data field is " + 'ip_port=' + new_node.ip + ":8080 and type is add"
    r = req.put("http://" + hostname + ":" + cur_node.access_port + "/kvs/view_update", 
            data={'ip_port':new_node.ip + ":8080", "type":"add"})
    if PRINT_HTTP_RESPONSES:
        print "Response:", r.text, r.status_code
    return r.status_code, r.json()['msg']

def delete_node_from_kvs(hostname, cur_node, node_to_delete):
    if PRINT_HTTP_REQUESTS:
        print "PUT request: " + "http://" + hostname + ":" + cur_node.access_port + "/kvs/view_update" + "; data: " + 'ip_port=' + node_to_delete.ip + ":8080 and type is remove"
    r = req.put("http://" + hostname + ":" + cur_node.access_port + "/kvs/view_update?type=remove",
            data={'ip_port':node_to_delete.ip + ":8080", "type":"remove"})
    if PRINT_HTTP_RESPONSES:
        print "Response:", r.text, r.status_code
    return r.status_code, r.json()['msg']

def generate_ip_port():
    global NODE_COUNTER
    NODE_COUNTER += 1
    ip = '10.0.0.' + str(NODE_COUNTER)
    port = str(8080 + NODE_COUNTER)
    return ip, port

def start_kvs(num_nodes, container_name, net='net', sudo='sudo'):
    ip_ports = []
    for i in range(1, num_nodes+1):
        ip, port = generate_ip_port()
        ip_ports.append((ip, port))
    view = ','.join([ip+":8080" for ip, _ in ip_ports])
    nodes = []
    print "Starting nodes"
    for ip, port in ip_ports:
        cmd_str = sudo + ' docker run -d -p ' + port + ":8080 --net=" + net + " --ip=" + ip + " -e VIEW=\"" + view + "\" -e ip_port=\"" + ip + ":8080" + "\" " + container_name
        print cmd_str
        node_id = subprocess.check_output(cmd_str, shell=True).rstrip('\n')
        nodes.append(Node(port, ip, node_id))
    time.sleep(5)
    return nodes

def start_new_node(container_name, net='net', sudo='sudo'):
    ip, port = generate_ip_port()
    cmd_str = sudo + ' docker run -d -p ' + port + ":8080 --net=" + net + " --ip=" + ip + " -e ip_port=\"" + ip + ":8080" + "\" " + container_name
    print cmd_str
    node_id = subprocess.check_output(cmd_str, shell=True).rstrip('\n')
    time.sleep(5)
    return Node(port, ip, node_id)

def stop_all_nodes(sudo):                                           
    print "\nStopping all nodes"
    os.system(sudo + " docker kill $(" + sudo + " docker ps -q)") 

def stop_node(node, sudo='sudo'):
    cmd_str = sudo + " docker kill %s" % node.id
    print cmd_str
    os.system(cmd_str)

def are_counts_balanced(counts, threshold):
    is_balanced = True
    for node, count in counts.iteritems():
        if count < threshold:
            is_balanced = False
    return is_balanced


if __name__ == "__main__":
    # Name of you docker image
    container_name = 'hw3'
    # If you can run docker without using sudo, then make the sudo variable empty string
    sudo = 'sudo'
    # For windows users hostname should be set to the virtual box ip address
    hostname = 'localhost'
    # Number of random keys to generate
    num_keys = 2000
    # If each node contains at least 100 keys then it is considered balanced.
    threshold = 100

    num_nodes = 5
    print OKBLUE + "Starting a KVS with " + str(num_nodes) + " nodes"+ ENDC
    kvs_nodes = start_kvs(num_nodes, container_name, net='mynet', sudo=sudo)
    #print kvs_nodes
    keys = generate_random_keys(num_keys)
    print OKBLUE + "\nAdding " + str(num_keys) + " randomly generated keys "+ ENDC
    counts = add_keys(hostname, kvs_nodes, keys, value = 1)
    if sum([int(val) for _, val in counts.iteritems()]) != num_keys:
        print FAIL + "SOME KEYS WERE NOT ADDDED SUCCESSFULY" + ENDC


    print OKBLUE + "\nTesting whether nodes are balanced"+ ENDC
    counts = get_keys_distribution(hostname, kvs_nodes, keys)

    if not are_counts_balanced(counts, threshold):
        print FAIL + "FAIL: KEYS ARE IMBALANCED" + ENDC
        print counts
    else:
        print OKGREEN + "OK: KEYS ARE BALANCED" + ENDC
        print counts

    print OKBLUE + "\nAdding a new node"+ ENDC
    new_node = start_new_node(container_name, net='mynet', sudo=sudo)
    kvs_nodes.append(new_node)

    print OKBLUE + "\nSending a view update request"+ ENDC
    t1 = time.time()
    status_code, msg = add_node_to_kvs(hostname, kvs_nodes[0], new_node)
    t2 = time.time()
    print HEADER + "TIME TAKEN FOR VIEW UPDATE: " + str(t2-t1) + " seconds"   

    print OKBLUE + "\nTesting whether nodes are balanced"+ ENDC
    counts = get_keys_distribution(hostname, kvs_nodes, keys)
    if not are_counts_balanced(counts, threshold):
        print FAIL + "FAIL: KEYS ARE IMBALANCED AFTER ADDITION OF A NODE" + ENDC
        print counts
    else:
        print OKGREEN + "OK: KEYS ARE BALANCED AFTER ADDITION OF A NODE" + ENDC
        print counts
    if sum([int(val) for _, val in counts.iteritems()]) != num_keys:
        print FAIL + "SOME KEYS WERE LOST AFTER AN ADDITION OF A NODE" + ENDC
    else:    
        print OKGREEN + "OK: NO KEY LOSS AFTER AN ADDITION OF A NODE" + ENDC

    print OKBLUE + "\nDeleting a node"+ ENDC
    delete_node_from_kvs(hostname, kvs_nodes[0], kvs_nodes[1])
    stop_node(kvs_nodes[1], sudo=sudo)
    del kvs_nodes[1]
    counts = add_keys(hostname, kvs_nodes, keys, value = 1)


    print OKBLUE + "\nTesting whether nodes are balanced after removing a node"+ ENDC
    counts = get_keys_distribution(hostname, kvs_nodes, keys)
    if not are_counts_balanced(counts, threshold):
        print FAIL + "FAIL: KEYS ARE IMBALANCED AFTER REMOVING A NODE" + ENDC
        print counts
    else:
        print OKGREEN + "OK: KEYS ARE BALANCED AFTER REMOVING A NODE" + ENDC
        print counts
    if sum([int(val) for _, val in counts.iteritems()]) != num_keys:
        print FAIL + "SOME KEYS WERE LOST AFTER DELETING A NODE" + ENDC
    else:    
        print OKGREEN + "OK: NO KEY LOSS AFTER REMOVING A NODE" + ENDC
    stop_all_nodes(sudo)