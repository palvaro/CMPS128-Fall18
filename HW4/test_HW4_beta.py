from multiprocessing import Pool
import random
import string
from collections import Counter
import json
import os
import subprocess
import requests as req
import time
import traceback
import sys

NODE_COUNTER = 2
PRINT_HTTP_REQUESTS = False
PRINT_HTTP_RESPONSES = False
AVAILABILITY_THRESHOLD = 1 
TB = 5

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
        return self.ip

def generate_ip_port():
    global NODE_COUNTER
    NODE_COUNTER += 1
    ip = '10.0.0.' + str(NODE_COUNTER)
    port = str(8080 + NODE_COUNTER)
    return ip, port

def generate_random_keys(n):
    alphabet = string.ascii_lowercase
    keys = []
    for i in range(n):
        key = ''
        for _ in range(10):
            key += alphabet[random.randint(0, len(alphabet) - 1)]
        keys.append(key)
    return keys

def send_get_request(hostname, node, key, causal_payload=''):
    d = None
    get_str = "http://" + hostname + ":" + str(node.access_port) + "/kvs?key=" + key + "&causal_payload=" + causal_payload 
    try:
        if PRINT_HTTP_REQUESTS:
            print "Get request: " + get_str
        start_time = time.time()
        r = req.get(get_str)
        end_time = time.time()
        if end_time - start_time > AVAILABILITY_THRESHOLD:
            print "THE SYSTEM IS NOT AVAILABLE: GET request took too long to execute : %s seconds" % (end_time - start_time)
        if PRINT_HTTP_RESPONSES:
            print "Response:", r.text, r.status_code
        d = r.json()
        for field in ['msg', 'value', 'partition_id', 'causal_payload', 'timestamp']:
            if not d.has_key(field):
                raise Exception("Field \"" + field + "\" is not present in response " + str(d))
    except Exception as e:
        print "THE FOLLOWING GET REQUEST RESULTED IN AN ERROR: ",
        print get_str
        print "Cannot retrieve key " + str(key) + " that should be present in the kvs"
        print e
    return d

def send_put_request(hostname, node, key, value, causal_payload=''):
    d = None
    put_str = "http://" + hostname + ":" + str(node.access_port) + "/kvs"
    data = {'value':value, 'causal_payload':causal_payload, 'key':key}
    try:
        if PRINT_HTTP_REQUESTS:
            print "PUT request:" + put_str + ' data field:' + str(data)
        start_time = time.time()
        r = req.put(put_str, data=data)
        end_time = time.time()
        if end_time - start_time > AVAILABILITY_THRESHOLD:
            print "THE SYSTEM IS NO AVAILABLE: PUT request took too long to execute : %s seconds" % (end_time - start_time)
        if PRINT_HTTP_RESPONSES:
            print "Response:", r.text, r.status_code
        d = r.json()
        for field in ['msg', 'partition_id', 'causal_payload', 'timestamp']:
            if not d.has_key(field):
                raise Exception("Field \"" + field + "\" is not present in response " + str(d))
    except Exception as e:
        print "THE FOLLOWING PUT REQUEST RESULTED IN AN ERROR: ",
        print put_str + ' data field ' +  str(data)
        print e
    return d                

def start_kvs(num_nodes, container_name, K=2, net='net', sudo='sudo'):
    ip_ports = []
    for i in range(1, num_nodes+1):
        ip, port = generate_ip_port()
        ip_ports.append((ip, port))
    view = ','.join([ip+":8080" for ip, _ in ip_ports])
    nodes = []
    print "Starting nodes"
    for ip, port in ip_ports:
        cmd_str = sudo + ' docker run -d -p ' + port + ":8080 --net=" + net + " -e K=" + str(K) + " --ip=" + ip + " -e VIEW=\"" + view + "\" -e ip_port=\"" + ip + ":8080" + "\" " + container_name
        print cmd_str
        node_id = subprocess.check_output(cmd_str, shell=True).rstrip('\n')
        nodes.append(Node(port, ip, node_id))
    time.sleep(5)
    return nodes

def start_new_node(container_name, K=2, net='net', sudo='sudo'):
    ip, port = generate_ip_port()
    cmd_str = sudo + ' docker run -d -p ' + port + ":8080 --net=" + net + " -e K=" + str(K) + " --ip=" + ip + " -e IPPORT=\"" + ip + ":8080" + "\" " + container_name
    print cmd_str
    node_id = subprocess.check_output(cmd_str, shell=True).rstrip('\n')
    time.sleep(5)
    return Node(port, ip, node_id)    

def add_keys(hostname, nodes, keys, value):
    d = {}
    for key in keys:
        resp_dict = send_put_request(hostname, nodes[random.randint(0, len(nodes) - 1)], key, value)
        partition_id = resp_dict['partition_id']
        if not d.has_key(partition_id):
            d[partition_id] = 0
        d[partition_id] += 1
    return d   #returns number of keys in each partition.             

def get_keys_distribution(hostname, nodes, keys):
    d = {}
    for key in keys:
        resp_dict = send_get_request(hostname, nodes[random.randint(0, len(nodes) - 1)], key)
        partition_id = resp_dict['partition_id']
        if not d.has_key(partition_id):
            d[partition_id] = 0
        d[partition_id] += 1
    return d #Returns the number in each partition

def stop_all_nodes(sudo):                                           
    # running_containers = subprocess.check_output([sudo, 'docker',  'ps', '-q'])
    # if len(running_containers):
    print "Stopping all nodes"
    os.system(sudo + " docker kill $(" + sudo + " docker ps -q)") 

def stop_node(node, sudo='sudo'):
    cmd_str = sudo + " docker kill %s" % node.id
    print cmd_str
    os.system(cmd_str)
    time.sleep(0.5)

def find_node(nodes, ip_port):
    ip = ip_port.split(":")[0]
    for n in nodes:
        if n.ip == ip:
            return n
    return None

def disconnect_node(node, network, sudo):
    cmd_str = sudo + " docker network disconnect " + network + " " + node.id
    print cmd_str
    time.sleep(0.5)
    os.system(cmd_str)
    time.sleep(0.5)

def connect_node(node, network, sudo):
    cmd_str = sudo + " docker network connect " + network + " --ip=" + node.ip + ' ' + node.id
    print cmd_str
   # r = subprocess.check_output(cmd_str.split())
   # print r
    time.sleep(0.5)
    os.system(cmd_str)
    time.sleep(0.5)

def add_node_to_kvs(hostname, cur_node, new_node):
    d = None
    put_str = "http://" + hostname + ":" + str(cur_node.access_port) + "/kvs/view_update"
    data = {'ip_port':new_node.ip + ":8080", 'type':'add'}
    try:
        if PRINT_HTTP_REQUESTS:
            print "PUT request:" + put_str + " data field " + str(data)
        r = req.put(put_str, data=data)
        if PRINT_HTTP_RESPONSES:
            print "Response:", r.text, r.status_code
        d = r.json()
        if r.status_code not in [200, 201, '200', '201']:
            raise Exception("Error, status code %s is not 200 or 201" % r.status_code)
        for field in ['msg', 'partition_id', 'number_of_partitions']:
            if not d.has_key(field):
                raise Exception("Field \"" + field + "\" is not present in response " + str(d))
    except Exception as e:
        print "ERROR IN ADDING A NODE TO THE KEY-VALUE STORE:",
        print e
    return d


def delete_node_from_kvs(hostname, cur_node, node_to_delete):
    d = None
    put_str = "http://" + hostname + ":" + str(cur_node.access_port) + "/kvs/view_update"
    data = {'ip_port':node_to_delete.ip + ":8080", 'type':'remove'}
    try:
        if PRINT_HTTP_REQUESTS:
            print "PUT request: " + put_str + " data field " + str(data)
        r = req.put(put_str, data=data)
        if PRINT_HTTP_RESPONSES:
            print "Response:", r.text, r.status_code
        d = r.json()
        if r.status_code not in [200, 201, '200', '201']:
            raise Exception("Error, status code %s is not 200 or 201" % r.status_code)
        for field in ['msg', 'number_of_partitions']:
            if not d.has_key(field):
                raise Exception("Field \"" + field + "\" is not present in response " + str(d))
    except Exception as e:
        print "ERROR IN DELETING A NODE TO THE KEY-VALUE STORE:",
        print e
    return d

def get_partition_id_for_key(node, key):
    resp_dict = send_get_request(hostname, node, key, causal_payload='')
    return resp_dict['partition_id']

def get_all_partitions_ids(node):
    get_str = "http://" + hostname + ":" + str(node.access_port) + "/kvs/get_all_partition_ids"
    try:
        if PRINT_HTTP_REQUESTS:
            print "Get request: " + get_str
        r = req.get(get_str)
        if PRINT_HTTP_RESPONSES:
            print "Response:", r.text, r.status_code
        d = r.json()
        for field in ['msg', 'partition_id_list']:
            if not d.has_key(field):
                raise Exception("Field \"" + field + "\" is not present in response " + str(d))
    except Exception as e:
        print "THE FOLLOWING GET REQUEST RESULTED IN AN ERROR: ",
        print get_str 
        print e
    return d['partition_id_list'] # returns the current partition ID list of the KVS

def get_partition_id_for_node(node):
    get_str = "http://" + hostname + ":" + str(node.access_port) + "/kvs/get_partition_id"
    try:
        if PRINT_HTTP_REQUESTS:
            print "Get request: " + get_str
        r = req.get(get_str)
        if PRINT_HTTP_RESPONSES:
            print "Response:", r.text, r.status_code
        d = r.json()
        for field in ['msg', 'partition_id']:
            if not d.has_key(field):
                raise Exception("Field \"" + field + "\" is not present in response " + str(d))
    except Exception as e:
        print "THE FOLLOWING GET REQUEST RESULTED IN AN ERROR: ",
        print get_str
        print e
    return d['partition_id']    

def get_partition_members(node, partition_id):
    get_str = "http://" + hostname + ":" + str(node.access_port) + "/kvs/get_partition_members?partition_id=" + str(partition_id)
    d = None
    try:
        if PRINT_HTTP_REQUESTS:
            print "Get request: " + get_str
        r = req.get(get_str)
        if PRINT_HTTP_RESPONSES:
            print "Response:", r.text, r.status_code
        d = r.json()
        for field in ['msg', 'partition_members']:
            if not d.has_key(field):
                raise Exception("Field \"" + field + "\" is not present in response " + str(d))
    except Exception as e:
        print "THE FOLLOWING GET REQUEST RESULTED IN AN ERROR: ",
        print get_str
        print e
    return d['partition_members']    

if __name__ == "__main__":
    container_name = 'hw3'
    hostname = 'localhost'
    network = 'mynet'
    sudo = 'sudo'
    tests_to_run = [1,2,3] #  

    if 1 in tests_to_run:
        try: # Test 1
            test_description = "Test 1: Basic functionality for obtaining information about partitions; tests the following GET requests get_all_partitions_ids, get_partition_memebrs and get_partition_id."
            print HEADER + "" + test_description  + ENDC
            nodes = start_kvs(4, container_name, K=2, net=network, sudo=sudo)
            keys = generate_random_keys(60)
            dist = add_keys(hostname, nodes, keys, 1)
            partition_id_list =  get_all_partitions_ids(nodes[0])
            if len(partition_id_list) != 2:
                raise Exception("ERROR: the number of partitions should be 2")
            for part_id in partition_id_list:
                if part_id not in dist:
                    raise Exception("ERROR: No keys are added to the partition %s" % part_id)
            
            print "Obtaining partition id for key ", keys[0]
            partition_id_for_key = get_partition_id_for_key(nodes[0], keys[0])
            print "Obtaining partition members for partition ", partition_id_for_key
            members = get_partition_members(nodes[0], partition_id_for_key)
            if len(members) != 2:
                raise Exception("ERROR: the size of a partition %d should be 2, but it is %d" % (partition_id_for_key, len(members)))
            
            part_nodes = []
            for ip_port in members:
                n = find_node(nodes, ip_port)
                if n is None:
                    raise Exception("ERROR: mismatch in the node ids (likely bug in the test script)")
                part_nodes.append(n)
            print "Asking nodes directly about their partition id. Information should be consistent"
            for i in range(len(part_nodes)):
                part_id = get_partition_id_for_node(part_nodes[i])
                if part_id != partition_id_for_key:
                    raise Exception("ERRR: inconsistent information about partition ids!")
            print "Ok, killing all the nodes in the partition ", partition_id_for_key
            print "Verifying that we cannot access the key using other partitions"
            for node in part_nodes:
                stop_node(node, sudo=sudo)
            other_nodes = [n for n in nodes if n not in part_nodes]

            get_str = "http://" + hostname + ":" + other_nodes[0].access_port + "/kvs?key=" + keys[0] + "&causal_payload=" + "" 
            if PRINT_HTTP_REQUESTS:
                print "Get request: " + get_str
            r = req.get(get_str)
            if PRINT_HTTP_RESPONSES:
                print "Response:", r.text, r.status_code
            if r.status_code in [200, 201, '200', '201']:
                raise Exception("ERROR: A KEY %s SHOULD NOT BE AVAILABLE AS ITS PARTITION IS DOWN!!!" % keys[0])
            print "OK, functionality for obtaining information about partitions looks good!"
        except Exception as e:
            print "Exception in test 1"
            print e
            traceback.print_exc(file=sys.stdout)
        stop_all_nodes(sudo)

    if 2 in tests_to_run:
        try: # Test 2
            test_description = "Test2: Node additions/deletions. A kvs consists of 2 partitions with 2 replicas each. I add 3 new nodes. The number of partitions should become 4. Then I delete a node.The number of partitions should become 3. I then delete 2 more nodes. Now the number of partitions should be back to 2." 
            print HEADER + "" + test_description  + ENDC
            print 
            print "Starting kvs ..."
            nodes = start_kvs(4, container_name, K=2, net=network, sudo=sudo)

            print "Adding 3 nodes"
            n1 = start_new_node(container_name, K=2, net=network, sudo=sudo)
            n2 = start_new_node(container_name, K=2, net=network, sudo=sudo)
            n3 = start_new_node(container_name, K=2, net=network, sudo=sudo)

            resp_dict = add_node_to_kvs(hostname, nodes[0], n1)
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 3:
                print "ERROR: the number of partitions should be 3, but it is " + str(number_of_partitions)
            else:
                print "OK, the number of partitions is 3"
            resp_dict = add_node_to_kvs(hostname, nodes[2], n2)
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 3:
                print "ERROR: the number of partitions should be 3, but it is " + str(number_of_partitions)
            else:
                print "OK, the number of partitions is 3"
            resp_dict = add_node_to_kvs(hostname, n1, n3)
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 4:
                print "ERROR: the number of partitions should be 4, but it is " + str(number_of_partitions)
            else:
                print "OK, the number of partitions is 4"

            print "Deleting nodes ..."
            resp_dict = delete_node_from_kvs(hostname, n3, nodes[0])
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 3:
                print "ERROR: the number of partitions should be 3, but it is " + str(number_of_partitions)
            else:
                print "OK, the number of partitions is 3"
            resp_dict = delete_node_from_kvs(hostname, n3, nodes[2])
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 3:
                print "ERROR: the number of partitions should be 3, but it is " + str(number_of_partitions)
            else:
                print "OK, the number of partitions is 3"
            resp_dict = delete_node_from_kvs(hostname, n3, n2)
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 2:
                print "ERROR: the number of partitions should be 2, but it is " + str(number_of_partitions)
            else:
                print "OK, the number of partitions is 2"
            print "Stopping the kvs"
        except Exception as e:
            print "Exception in test 2"
            print e
            traceback.print_exc(file=sys.stdout)

    if 3 in tests_to_run:
        try: # Test 3
            test_description = "Test 3: A very simple test to verify that after we disconnect/connect a node, the kvs works as it is supposed to. This kvs consists of only one partition."
            print HEADER + "" + test_description  + ENDC
            nodes = start_kvs(2, container_name, K=2, net=network, sudo=sudo)
            node1 = nodes[0]
            node2 = nodes[1]
            d = send_put_request(hostname, node1, 'dog', 'pupper', causal_payload='')
            d = send_get_request(hostname, node2, 'dog', causal_payload=d['causal_payload'])
            if d['value'] != 'pupper':
                raise Exception("ERROR: The kvs did not store value pupper for key dog")
            print "Disconnecting one of the nodes..."    
            disconnect_node(node1, network, sudo)
            time.sleep(1)
            print "Creating a new key by sending request to the other alive node"
            d = send_put_request(hostname, node2, 'doggo', 'pupperino', causal_payload='')
            print "Merging the network..."    
            connect_node(node1, network, sudo)
            time.sleep(TB)

            d = send_get_request(hostname, node1, 'doggo', causal_payload=d['causal_payload'])
            if not d.has_key('value')  or d['value'] != 'pupperino':
                raise Exception("ERROR: the kvs is not working after network healed.")

            print "OK, the kvs works after we disconnected the node and connected it back."
        except Exception as e:
            print "Exception in test 3"
            print e
            traceback.print_exc(file=sys.stdout)      
