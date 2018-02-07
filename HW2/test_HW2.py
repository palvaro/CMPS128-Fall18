import unittest
import subprocess
import requests
import sys
import random
import time

hostname = 'localhost' #Windows and Mac users can change this to the docker vm ip
contname = 'assignment2' #Set your container name here
sudo = '' #Make the value of this variable sudo if you need sudo to start containers 

class TestHW2(unittest.TestCase):

    '''
    Creating a subnet:
        sudo docker network create --subnet=10.0.0.0/16 mynet
    '''
    ip_addresses = ['10.0.0.20','10.0.0.21','10.0.0.22']
    host_ports = ['8083', '8084', '8085']
    node_ids = []
    nodes_address = []
    has_been_run_once = False
    all_tests_done = False
    key1 = '_yJnRhMUqNHXlUvxTie9jfQ0n6DX2of2ET13aW1LGLnvF9ZBxowE5NluZ3bH0Ctlw65S6XjYftCIzIIWDRd8bS5ykWKZvZGVvQDvakcODw___yiN8purA8Xfl_9WOzCLGYyJF4K2q3yOaOnd6Iu9SEo_hOBInXYkTHBTiGPPPAgt360RGaExts2_gyR8Xg0u8HVZgXrpWjWrRMTBN78Zj7INR2YnsJYzXWooTyU_tOV49O7xDYsgiS6MD'
    key2 = '6TLxbmwMTN4hX7L0QX5_NflWH0QKfrTlzcuM5PUQHS52___lCzKbEMxLZHhtfww3KcMoboDLjB6mw_wFfEz5v_TtHqvGOZnk4_8aqHga79BaHXzpU9_IRbdjYdQutAU0HEuji6Ny1Ol_MSaBF4JdT0aiG_N7xAkoPH3AlmVqDN45KDGBz7_YHrLnbLEK11SQxZcKXbFomh9JpH_sbqXIaifqOy4g06Ab0q3WkNfVzx7H0hGhNlkINf5PF1'
    key3 = '6TLxbmwMTN4hX7L0QX5_NflWH0QKfrTlzcuM5PUQHS52___lCizKbEMxLZHhtfww3KcMoboDLjB6mw_wFfEz5v_TtHqvGOZnk4_8aqHga79BaHXzpU9_IRbdjYdQutAU0HEuji6Ny1Ol_MSaBF4JdT0aiG_N7xAkoPH3AlmVqDN45KDGBz7_YHrLnbLEK11SQxZcKXbFomh9JpH_sbqXIaifqOy4g06Ab0q3WkNfVzx7H0hGhNlkINf5PF12'
    val1 = 'aaaasjdhvksadjfbakdjs'
    val2 = 'asjdhvksadjfbakdjs'
    val3 = 'bknsdfnbKSKJDBVKpnkjgbsnk'                

    def spin_up_nodes(self):

        exec_string_main = sudo +" docker run -p 8083:8080 --net=mynet --ip=10.0.0.20 -d %s" % contname
        print exec_string_main
        self.__class__.node_ids.append(subprocess.check_output(exec_string_main, shell=True).strip('\n'))

        exec_string_forw1 = sudo +" docker run -p 8084:8080 --net=mynet -e MAINIP=10.0.0.20:8080 -d %s" % contname
        print exec_string_forw1
        self.__class__.node_ids.append(subprocess.check_output(exec_string_forw1, shell=True).strip('\n'))

        exec_string_forw2 = sudo +" docker run -p 8085:8080 --net=mynet -e MAINIP=10.0.0.20:8080 -d %s" % contname
        print exec_string_forw2
        self.__class__.node_ids.append(subprocess.check_output(exec_string_forw2, shell=True).strip('\n'))

        self.__class__.nodes_address = ['http://' + hostname + ":" + x for x in self.__class__.host_ports]
        # print(self.__class__.node_ids)

    def setUp(self):
        
        if not self.__class__.has_been_run_once:
            self.__class__.has_been_run_once = True   
            self.spin_up_nodes()
            print "Sleeping for 10 seconds to let servers bootup"
            time.sleep(10)

    def test_a_put_nonexistent_key(self):
        res = requests.put(self.__class__.nodes_address[0]+'/kvs',data = {'value':'bart', 'key':'foo'})
        d = res.json()
        self.assertEqual(res.status_code,201)
        self.assertEqual(int(d['replaced']),0)
        self.assertEqual(d['msg'],'success')

    def test_b_put_existing_key(self):
        res = requests.put(self.__class__.nodes_address[1]+'/kvs',data= {'value':'bart', 'key':'foo'})
        d = res.json()
        self.assertEqual(d['replaced'],1)
        self.assertEqual(d['msg'],'success')

    def test_c_get_nonexistent_key(self):
        res = requests.get(self.__class__.nodes_address[2]+'/kvs?key=faa')
        d = res.json()
        self.assertEqual(res.status_code,404)
        self.assertEqual(d['msg'],'error')
        self.assertEqual(d['error'],'key does not exist')

    def test_d_get_existing_key(self):
        res = requests.get(self.__class__.nodes_address[2]+'/kvs?key=foo')
        d = res.json()
        self.assertEqual(d['msg'],'success')
        self.assertEqual(d['value'],'bart')

    def test_e_del_nonexistent_key(self):
        res = requests.delete(self.__class__.nodes_address[0]+'/kvs?key=faa')
        d = res.json()  
        self.assertEqual(res.status_code,404)
        self.assertEqual(d['msg'],'error')
        self.assertEqual(d['error'],'key does not exist')

    def test_f_del_existing_key(self):
        res = requests.delete(self.__class__.nodes_address[1]+'/kvs?key=foo')
        d = res.json()
        self.assertEqual(d['msg'],'success')

    def test_g_get_deleted_key(self):
        res = requests.get(self.__class__.nodes_address[0]+'/kvs?key=foo')
        d = res.json()
        self.assertEqual(res.status_code,404)
        self.assertEqual(d['msg'],'error')
        self.assertEqual(d['error'],'key does not exist')

    def test_h_put_deleted_key(self):
        res = requests.put(self.__class__.nodes_address[2]+'/kvs',data= {'value':'bart', 'key':'foo'})
        d = res.json()
        self.assertEqual(res.status_code,201)
        self.assertEqual(d['replaced'],0)
        self.assertEqual(d['msg'],'success')

    def test_i_put_nonexistent_key(self):
        res = requests.put(self.__class__.nodes_address[1]+'/kvs',data = {'value':self.__class__.val1, 'key':self.__class__.key1})
        d = res.json()
        self.assertEqual(res.status_code,201)
        self.assertEqual(d['replaced'],0)
        self.assertEqual(d['msg'],'success')

    def test_j_put_existing_key(self):
        res = requests.put(self.__class__.nodes_address[0]+'/kvs',data = {'value':self.__class__.val2, 'key':self.__class__.key1})
        d = res.json()
        self.assertEqual(d['replaced'],1)
        self.assertEqual(d['msg'],'success')

    def test_k_get_nonexistent_key(self):
        res = requests.get(self.__class__.nodes_address[1]+'/kvs?key='+self.__class__.key2)
        d = res.json()
        self.assertEqual(res.status_code,404)
        self.assertEqual(d['msg'],'error')
        self.assertEqual(d['error'],'key does not exist')

    def test_l_get_existing_key(self):
        res = requests.get(self.__class__.nodes_address[2]+'/kvs?key='+self.__class__.key1)
        d = res.json()
        self.assertEqual(d['msg'],'success')
        self.assertEqual(d['value'],self.__class__.val2)

    def test_m_put_key_too_long(self):
        res = requests.put(self.__class__.nodes_address[0]+'/kvs',data = {'value':self.__class__.val2, 'key':self.__class__.key3})
        d = res.json()
        self.assertNotEqual(res.status_code,200)
        self.assertNotEqual(res.status_code,201)
        self.assertEqual(d['msg'],'error')
        #self.assertEqual(d['error'],'key too long')

    def test_n_put_key_too_long_on_forwarding_instance(self):
        res = requests.put(self.__class__.nodes_address[1]+'/kvs',data = {'value':self.__class__.val2, 'key':self.__class__.key3})
        d = res.json()
        self.assertNotEqual(res.status_code,200)
        self.assertNotEqual(res.status_code,201)
        self.assertEqual(d['msg'],'error')
        #self.assertEqual(d['error'],'key too long')

    def test_o_put_key_without_value(self):
        res = requests.put(self.__class__.nodes_address[0]+'/kvs',data = {'key':self.__class__.key1})
        d = res.json()
        self.assertNotEqual(res.status_code,200)
        self.assertNotEqual(res.status_code,201)
        self.assertEqual(d['msg'],'error')

    def test_p_put_key_without_value_on_forwarding_instance(self):
        res = requests.put(self.__class__.nodes_address[2]+'/kvs',data = {'key':self.__class__.key1})
        d = res.json()
        self.assertNotEqual(res.status_code,200)
        self.assertNotEqual(res.status_code,201)
        self.assertEqual(d['msg'],'error')        

    def test_q_taking_down_secondary_instance(self):
        shell_command = "docker stop " + str(self.__class__.node_ids[1])
        subprocess.check_output(shell_command, shell=True)        
        res = requests.get(self.__class__.nodes_address[2]+'/kvs?key='+self.__class__.key1)
        d = res.json()
        self.assertEqual(d['msg'],'success')
        self.assertEqual(d['value'],self.__class__.val2)

    def test_r_taking_down_primary_instance(self):
        self.__class__.all_tests_done = True
        shell_command = "docker stop " + str(self.__class__.node_ids[0])
        subprocess.check_output(shell_command, shell=True)        
        res = requests.get(self.__class__.nodes_address[1]+'/kvs/'+self.__class__.key1)
        d = res.json()
        self.assertEqual(d['msg'],'error')
        self.assertEqual(d['error'],'service is not available')              

    def tearDown(self):
        if self.__class__.all_tests_done:
            print("\nKilling all alive nodes.")
            shell_command = "docker stop $(docker ps -q)"
            subprocess.check_output(shell_command, shell=True)

if __name__ == '__main__':
    unittest.main()
