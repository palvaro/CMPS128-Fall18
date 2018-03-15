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

def send_simple_get_request(hostname, node, key, causal_payload=''):
    """ The function does not check any conditions on the response object.
    It returns raw request."""
    get_str = "http://" + hostname + ":" + str(node.access_port) + "/kvs?key=" + key + "&causal_payload=" + causal_payload
    if PRINT_HTTP_REQUESTS:
        print "Get request: " + get_str
    r = req.get(get_str)
    if PRINT_HTTP_RESPONSES:
        print r.text, r.status_code
    return r

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
    cmd_str = sudo + ' docker run -d -p ' + port + ":8080 --net=" + net + " -e K=" + str(K) + " --ip=" + ip + " -e ip_port=\"" + ip + ":8080" + "\" " + container_name
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
    tests_to_run = [1,2,3,4,5,6,7,8] #  

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
            
            print OKBLUE + "Obtaining partition id for key: " + keys[0] + ENDC
            partition_id_for_key = get_partition_id_for_key(nodes[0], keys[0])
            print OKBLUE + "Obtaining partition members for partition " + partition_id_for_key  + ENDC
            members = get_partition_members(nodes[0], partition_id_for_key)
            if len(members) != 2:
                raise Exception("ERROR: the size of a partition %d should be 2, but it is %d" % (partition_id_for_key, len(members)))
            
            part_nodes = []
            for ip_port in members:
                n = find_node(nodes, ip_port)
                if n is None:
                    raise Exception("ERROR: mismatch in the node ids (likely bug in the test script)")
                part_nodes.append(n)
            print OKBLUE + "Asking nodes directly about their partition id. Information should be consistent" + ENDC
            for i in range(len(part_nodes)):
                part_id = get_partition_id_for_node(part_nodes[i])
                if part_id != partition_id_for_key:
                    raise Exception("ERRR: inconsistent information about partition ids!")
            print OKBLUE + "Ok, killing all the nodes in the partition " + partition_id_for_key + ENDC
            for node in part_nodes:
                stop_node(node, sudo=sudo)
            other_nodes = [n for n in nodes if n not in part_nodes]

            print OKBLUE + "Verifying that we cannot access the key using other partitions" + ENDC
            get_str = "http://" + hostname + ":" + other_nodes[0].access_port + "/kvs?key=" + keys[0] + "&causal_payload=" + "" 
            if PRINT_HTTP_REQUESTS:
                print "Get request: " + get_str
            r = req.get(get_str)
            if PRINT_HTTP_RESPONSES:
                print "Response:", r.text, r.status_code
            if r.status_code in [200, 201, '200', '201']:
                raise Exception("ERROR: A KEY %s SHOULD NOT BE AVAILABLE AS ITS PARTITION IS DOWN!!!" % keys[0])
            print OKGREEN + "OK, functionality for obtaining information about partitions looks good!" + ENDC
        except Exception as e:
            print FAIL + "Exception in test 1" + ENDC
            print FAIL + e + ENDC
            traceback.print_exc(file=sys.stdout)
        stop_all_nodes(sudo)

    if 2 in tests_to_run:
        try: # Test 2
            test_description = "Test2: Node additions/deletions. A kvs consists of 2 partitions with 2 replicas each. I add 3 new nodes. The number of partitions should become 4. Then I delete a node.The number of partitions should become 3. I then delete 2 more nodes. Now the number of partitions should be back to 2." 
            print HEADER + "" + test_description  + ENDC
            print 
            print OKBLUE + "Starting kvs ..." + ENDC
            nodes = start_kvs(4, container_name, K=2, net=network, sudo=sudo)

            print OKBLUE + "Adding 3 nodes" + ENDC
            n1 = start_new_node(container_name, K=2, net=network, sudo=sudo)
            n2 = start_new_node(container_name, K=2, net=network, sudo=sudo)
            n3 = start_new_node(container_name, K=2, net=network, sudo=sudo)

            resp_dict = add_node_to_kvs(hostname, nodes[0], n1)
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 3:
                print FAIL + "ERROR: the number of partitions should be 3, but it is " + str(number_of_partitions) + ENDC
            else:
                print OKGREEN + "OK, the number of partitions is 3" + ENDC
            resp_dict = add_node_to_kvs(hostname, nodes[2], n2)
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 3:
                print FAIL + "ERROR: the number of partitions should be 3, but it is " + str(number_of_partitions) + ENDC
            else:
                print OKGREEN + "OK, the number of partitions is 3" + ENDC
            resp_dict = add_node_to_kvs(hostname, n1, n3)
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 4:
                print FAIL + "ERROR: the number of partitions should be 4, but it is " + str(number_of_partitions) + ENDC
            else:
                print OKGREEN + "OK, the number of partitions is 4" + ENDC

            print OKBLUE + "Deleting nodes ..." + ENDC
            resp_dict = delete_node_from_kvs(hostname, n3, nodes[0])
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 3:
                print FAIL + "ERROR: the number of partitions should be 3, but it is " + str(number_of_partitions) + ENDC
            else:
                print OKGREEN + "OK, the number of partitions is 3" + ENDC
            resp_dict = delete_node_from_kvs(hostname, n3, nodes[2])
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 3:
                print FAIL + "ERROR: the number of partitions should be 3, but it is " + str(number_of_partitions) + ENDC
            else:
                print OKGREEN + "OK, the number of partitions is 3" + ENDC
            resp_dict = delete_node_from_kvs(hostname, n3, n2)
            number_of_partitions = resp_dict.get('number_of_partitions')
            if number_of_partitions != 2:
                print FAIL + "ERROR: the number of partitions should be 2, but it is " + str(number_of_partitions) + ENDC
            else:
                print OKGREEN + "OK, the number of partitions is 2" + ENDC
            print OKBLUE + "Stopping the kvs" + ENDC
        except Exception as e:
            print FAIL + "Exception in test 2" + ENDC
            print FAIL + e + ENDC
            traceback.print_exc(file=sys.stdout)
        stop_all_nodes(sudo)            

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
            print OKBLUE + "Disconnecting one of the nodes..." + ENDC    
            disconnect_node(node1, network, sudo)
            time.sleep(1)
            print OKBLUE + "Creating a new key by sending request to the other alive node" + ENDC
            d = send_put_request(hostname, node2, 'doggo', 'pupperino', causal_payload='')
            print OKBLUE + "Merging the network..." + ENDC
            connect_node(node1, network, sudo)
            time.sleep(TB)

            d = send_get_request(hostname, node1, 'doggo', causal_payload=d['causal_payload'])
            if not d.has_key('value')  or d['value'] != 'pupperino':
                raise Exception("ERROR: the kvs is not working after network healed.")

            print OKGREEN + "OK, the kvs works after we disconnected the node and connected it back." + ENDC
        except Exception as e:
            print FAIL + "Exception in test 3" + ENDC
            print FAIL + e + ENDC
            traceback.print_exc(file=sys.stdout)
        stop_all_nodes(sudo)            

    if 4 in tests_to_run:
        try: # Test 4
            num_keys = 3
            test_description = "Test 4: Start 4 nodes with K=2. Generate random keys. I send a get request to one key to get the partition it is from. I then disconnect all the replicas in that partition. In this case, the key should be unavailable. I then connect one replica back and the key should available."
            print HEADER + "" + test_description  + ENDC
            nodes = start_kvs(4, container_name, K=2, net=network, sudo=sudo)
            keys = generate_random_keys(num_keys)
            add_keys(hostname, nodes, keys, -1)
            partition_id = get_partition_id_for_key(nodes[0], keys[0])
            members = get_partition_members(nodes[0], partition_id)
            part_nodes = [find_node(nodes, ip_port) for ip_port in members]
            print OKBLUE + "key %s belongs to partition %d with nodes %s and %s" % (keys[0], partition_id, part_nodes[0], part_nodes[1]) + ENDC
            
            print OKBLUE + "Disconnecting both nodes to verify that the key is unavailable" + ENDC
            disconnect_node(part_nodes[0], network, sudo)
            disconnect_node(part_nodes[1], network, sudo)

            other_nodes = [n for n in nodes if n not in part_nodes]
            r = send_simple_get_request(hostname, other_nodes[0], keys[0], causal_payload='')
            if r.status_code in [200, 201, '200', '201']:
                raise Exception("ERROR: A KEY %s SHOULD NOT BE AVAILABLE AS ITS PARTITION IS DOWN!!!" % keys[0])
            print OKGREEN + "Good, the key is unavailable" + ENDC

            print OKBLUE + "Connecting one node back and verifying that the key is accessible" + ENDC
            connect_node(part_nodes[1], network, sudo)
            time.sleep(TB)
            r = send_simple_get_request(hostname, other_nodes[0], keys[0], causal_payload='')
            d = r.json()
            print d
            if not d.has_key('value') or int(d['value']) != -1:
                raise Exception("ERROR: service is unavailable or the value of the key changed after the network healed")
            print OKGREEN + "Good, the key is available" + ENDC

        except Exception as e:
            print FAIL + "Exception in test 4" + ENDC
            print FAIL + e + ENDC
            traceback.print_exc(file=sys.stdout)
        stop_all_nodes(sudo)

    if 5 in tests_to_run:
        try: # Test 5
            num_keys = 3
            test_description = "Test 5: Start 4 nodes with K=2. Generate random keys. I send a get request to one key to get the partition it is from. I then disconnect one of the nodes in the partitions. I send a request to the other partition to update the same key. Then I connect the node back, wait for 5 seconds for network to heal and disconnect the other node in partition."
            print HEADER + "" + test_description  + ENDC
            nodes = start_kvs(4, container_name, K=2, net=network, sudo=sudo)
            keys = generate_random_keys(num_keys)
            add_keys(hostname, nodes, keys, 7)
            partition_id = get_partition_id_for_key(nodes[0], keys[0])
            members = get_partition_members(nodes[0], partition_id)
            part_nodes = [find_node(nodes, ip_port) for ip_port in members]
            print OKBLUE + "key %s belongs to partition %d with nodes %s and %s" % (keys[0], partition_id, part_nodes[0], part_nodes[1]) + ENDC
            
            print OKBLUE + "Disconnecting one of the nodes in the partition" + ENDC
            disconnect_node(part_nodes[0], network, sudo)

            print OKBLUE + "Updating the key..." + ENDC
            d = send_put_request(hostname, other_nodes[0],  keys[0], 17, causal_payload=d['causal_payload'])

            print OKBLUE + "Connecting back the nodeand disconnecting other node in the partition" + ENDC
            connect_node(part_nodes[0], network, sudo)
            time.sleep(TB)
            disconnect_node(part_nodes[1], network, sudo)
            time.sleep(1)
            d = send_get_request(hostname, other_nodes[1], keys[0], causal_payload=d['causal_payload'])
            if int(d['value']) != 17:
                raise Exception("ERROR: THE VALUE IS STALE AFTER THE NETWORK WAS HEALED AND A %d SECOND THRESHOLD!" % TB)
            print OKGREEN + "OK, the value is up to date!" + ENDC
        except Exception as e:
            print FAIL + "Exception in test 5" + ENDC
            print FAIL + e + ENDC
            traceback.print_exc(file=sys.stdout)
        stop_all_nodes(sudo)

    if 6 in tests_to_run:
        try: # Test 6
            num_keys = 3
            test_description = "Test 6: Test for data replication. Failing of this test indicates the data replication hasn't been implemented correctly." 
            print HEADER + "" + test_description  + ENDC
            nodes = start_kvs(6, container_name, K=3, net=network, sudo=sudo)
            keys = generate_random_keys(num_keys)
            add_keys(hostname, nodes, keys, -1)
            partition_id = get_partition_id_for_key(nodes[0], keys[0])
            members = get_partition_members(nodes[0], partition_id)
            part_nodes = [find_node(nodes, ip_port) for ip_port in members]
            print OKBLUE + "key %s belongs to partition %d with nodes %s, %s and %s" % (keys[0], partition_id, part_nodes[0], part_nodes[1], part_nodes[2]) + ENDC
            
            r = send_simple_get_request(hostname, part_nodes[0], keys[0], causal_payload='')
            d = r.json()
            d = send_put_request(hostname, part_nodes[1],  keys[0], 15, causal_payload=d['causal_payload'])
            r = send_simple_get_request(hostname, part_nodes[2],  keys[0], causal_payload=d['causal_payload'])
            d = r.json()
            if int(d['value']) != 15:
                raise Exception("ERROR: THE VALUE IS STALE!. DATA REPLICATION NOT IMPLEMENTED CORRECTLY")
            print OKGREEN + "OK, the value is up to date!" + ENDC
        except Exception as e:
            print FAIL + "Exception in test 6" + ENDC
            print FAIL + e + ENDC
            traceback.print_exc(file=sys.stdout)
        stop_all_nodes(sudo)

    if 7 in tests_to_run:
        try: # Test 7
            test_description = "Test 7: A kvs consists of 2 partitions with 2 replicas each. I send 60 randomly generated keys to the kvs. I add 2 nodes to the kvs. No keys should be dropped. Then, I kill a node and send a view_change request to remove the faulty instance. Again, no keys should be dropped."
            print HEADER + "" + test_description  + ENDC
            nodes = start_kvs(4, container_name, K=2, net=network, sudo=sudo)
            keys = generate_random_keys(60)
            add_keys(hostname, nodes, keys, 1)
     
            print OKBLUE + "Adding 2 nodes..." + ENDC
            n1 = start_new_node(container_name, K=2, net=network, sudo=sudo)
            n2 = start_new_node(container_name, K=2, net=network, sudo=sudo)

            resp_dict1 = add_node_to_kvs(hostname, nodes[0], n1)
            time.sleep(2)
            resp_dict2 = add_node_to_kvs(hostname, nodes[2], n2)
            time.sleep(2)

            if not (resp_dict1 is not None and resp_dict2 is not None and 
                resp_dict1['msg'] == 'success' and resp_dict2['msg'] == 'success'):
                raise Exception("Problems with adding 2 new nodes")
            print OKGREEN + "Nodes were successfully added." + ENDC

            hm = {} # Dictionary of partition and its respective nodes
            for x in range(len(nodes)):
                part_id = get_partition_id_for_node(nodes[i])
                if part_id not in hm:
                    hm[part_id] = []
                hm[part_id].append(nodes[i])

            part_id1 = resp_dict1["partition_id"]
            new_part_id = part_id1       
            if part_id1 not in hm:
                hm[part_id1] = []
            hm[part_id1].append(n1)
            part_id2 = resp_dict2["partition_id"]
            hm[part_id2].append(n2)

            print OKBLUE + "Verifying that no keys were dropped..." + ENDC
            total_keys = 0
            for key in hm.keys():
                get_str = "http://" + hostname + ":" + str(hm[key][0].access_port) + "/kvs/get_number_of_keys"
                r = req.get(get_str)
                d = r.json()
                total_keys = total_keys + d["count"]                
            if total_keys != len(keys):
                raise Exception("Total number of keys in KVS are not equal to ones added initially")
            else:
                print OKGREEN + "OK, no keys were dropped after adding new nodes." + ENDC

            print OKBLUE + "Stopping a node." + ENDC
            removed_node = hm[new_part_id].pop(0) 
            stop_node(removed_node, sudo=sudo)
            print OKBLUE + "Sending a request to remove the faulty node from the key-value store." + ENDC
            resp_dict = delete_node_from_kvs(hostname, nodes[0],removed_node)
            if not (resp_dict is not None and resp_dict['msg'] == 'success'):
                raise Exception("Problems with deleting a node")
            print OKGREEN + "A node was successfully deleted." + ENDC
            
            print OKBLUE + "Verifying that no keys were dropped..." + ENDC
            total_keys = 0
            for key in hm.keys():
                get_str = "http://" + hostname + ":" + str(hm[key][0].access_port) + "/kvs/get_number_of_keys"
                r = req.get(get_str)
                d = r.json()
                total_keys = total_keys + d["count"]                
            if total_keys != len(keys):
                raise Exception("Total number of keys in KVS are not equal to ones added initially")
            else:
                print OKGREEN + "OK, no keys were dropped after adding new nodes." + ENDC
        except Exception as e:
            print FAIL + "Exception in test 7" + ENDC
            print FAIL + e + ENDC
            traceback.print_exc(file=sys.stdout)
        stop_all_nodes(sudo)

    if 8 in tests_to_run:
        try: # Test 8
            test_description = "Test 8: Similar to Test case 7. Here I delete a partition (2 nodes) and check if no keys are dropped."
            print HEADER + "" + test_description  + ENDC
            nodes = start_kvs(6, container_name, K=2, net=network, sudo=sudo)
            keys = generate_random_keys(60)
            add_keys(hostname, nodes, keys, 1)

            hm = {} # Dictionary of partition and its respective nodes
            for x in range(len(nodes)):
                part_id = get_partition_id_for_node(nodes[i])
                if part_id not in hm:
                    hm[part_id] = []
                hm[part_id].append(nodes[i])

            l = hm.keys()
            part_id_to_be_deleted = l[0]
            other_part_id = l[1]      
            
            #Cheking if partition to be deleted has two nodes 
            if not len(hm[part_id_to_be_deleted]) == 2:
                raise Exception("Every partition should have had 2 nodes")

            print OKBLUE + "Sending a remove node request to all nodes in partition: " + str(part_id_to_be_deleted) + ENDC
            removed_node = hm[part_id_to_be_deleted].pop() 
            delete_node_from_kvs(hostname, hm[other_part_id][0], removed_node)
            time.sleep(1)
            removed_node = hm[part_id_to_be_deleted].pop() 
            delete_node_from_kvs(hostname, hm[other_part_id][0], removed_node)
            time.sleep(1)
            hm.pop(part_id_to_be_deleted) #Removing partition from Dict

            print OKBLUE + "Verifying that no keys were dropped..." + ENDC
            total_keys = 0
            for key in hm.keys():
                get_str = "http://" + hostname + ":" + str(hm[key][0].access_port) + "/kvs/get_number_of_keys"
                r = req.get(get_str)
                d = r.json()
                total_keys = total_keys + d["count"]                
            if total_keys != len(keys):
                raise Exception("Total number of keys in KVS are not equal to ones added initially")
            else:
                print OKGREEN + "OK, no keys were removing partition." + ENDC
        except Exception as e:
            print FAIL + "Exception in test 8" + ENDC
            print FAIL + e + ENDC
            traceback.print_exc(file=sys.stdout)
        stop_all_nodes(sudo) 