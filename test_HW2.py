import unittest
import subprocess
import requests
import sys
import random
import time

hostname = 'localhost'  # Windows and Mac users can change this to the docker vm ip
contname = 'assignment2'  # Set your container name here
sudo = ''  # Make the value of this variable sudo if you need sudo to start containers


class TestHW2(unittest.TestCase):
    '''
    Creating a subnet:
        sudo docker network create --subnet=10.0.0.0/16 mynet
    '''
    ip_addresses = ['10.0.0.20', '10.0.0.21', '10.0.0.22']
    host_ports = ['8083', '8084', '8085']
    node_ids = []
    nodes_address = []
    has_been_run_once = False
    all_tests_done = False
    key1 = '_yJnRhMUqNHXlUvxTie9jfQ0n6DX2of2ET13aW1LGLnvF9ZBxowE5NluZ3bH0Ctlw65S6XjYftCIzIIWDRd8bS5ykWKZvZGVvQDvakcODw___yiN8purA8Xfl_9WOzCLGYyJF4K2q3yOaOnd6Iu9SEo'
    key2 = '6TLxbmwMTN4hX7L0QX5_NflWH0QKfrTlzcuM5PUQHS52___lCzKbEMxLZHhtfww3KcMoboDLjB6mw_wFfEz5v_TtHqvGOZnk4_8aqHga79BaHXzpU9_IRbdjYdQutAU0HEuji6Ny1Ol'
    key3 = '6TLxbmwMTN4hX7L0QX5_NflWH0QKfrTlzcuM5PUQHS52___lCizKbEMxLZHhtfww3KcMoboDLjB6mw_wFfEz5v_TtHqvGOZnk4_8aqHga79BaHXzpU9_IRbdjYdQutAU0HEuji6Ny1Ol_MSaBF4JdT0aiG_N7xAkoPH3AlmVqDN45KDGBz7_YHrLnbLEK11SQxZcKXbFomh9JpH_sbqXIaifqOy4g06Ab0q3WkNfVzx7H0hGhNlkINf5PF12'
    val1 = 'aaaasjdhvksadjfbakdjs'
    val2 = 'asjdhvksadjfbakdjs'
    val3 = 'bknsdfnbKSKJDBVKpnkjgbsnk'

    def spin_up_nodes(self):

        exec_string_main = sudo + " docker run -p 8083:8080 --net=mynet --ip=10.0.0.20 -d %s" % contname
        print(exec_string_main)
        self.__class__.node_ids.append(subprocess.check_output(exec_string_main, shell=True).strip('\n'))

        exec_string_forw1 = sudo + " docker run -p 8084:8080 --net=mynet -e MAINIP=10.0.0.20:8080 -d %s" % contname
        print(exec_string_forw1)
        self.__class__.node_ids.append(subprocess.check_output(exec_string_forw1, shell=True).strip('\n'))

        exec_string_forw2 = sudo + " docker run -p 8085:8080 --net=mynet -e MAINIP=10.0.0.20:8080 -d %s" % contname
        print(exec_string_forw2)
        self.__class__.node_ids.append(subprocess.check_output(exec_string_forw2, shell=True).strip('\n'))

        self.__class__.nodes_address = ['http://' + hostname + ":" + x for x in self.__class__.host_ports]
        # print(self.__class__.node_ids)

    def setUp(self):

        if not self.__class__.has_been_run_once:
            self.__class__.has_been_run_once = True
            self.spin_up_nodes()
            print("Sleeping for 10 seconds to let servers bootup")
            time.sleep(10)

    
    def test_a_put_nonexistent_key(self):
        res = requests.put(self.__class__.nodes_address[0] + '/keyValue-store/subject', data = {'val': 'Distributed System'})
        d = res.json()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(int(d['replaced']), 0)
        self.assertEqual(d['msg'], 'Added successfully')

    
    def test_b_get_existing_key(self):
        res = requests.get(self.__class__.nodes_address[2] + '/keyValue-store/subject')
        d = res.json()
        self.assertEqual(d['msg'], 'Success')
        self.assertEqual(d['value'], 'Distributed System')

    
    def test_c_put_existing_key(self):
        res = requests.put(self.__class__.nodes_address[1] + '/keyValue-store/subject',  data = {'val': 'Data Structures'})
        d = res.json()
        self.assertEqual(d['replaced'], 1)
        self.assertEqual(d['msg'], 'Updated successfully')

    
    def test_d_get_nonexistent_key(self):
        res = requests.get(self.__class__.nodes_address[2] + '/keyValue-store/subject2')
        d = res.json()
        self.assertEqual(res.status_code, 404)
        self.assertEqual(d['msg'], 'Error')
        self.assertEqual(d['error'], 'Key does not exist')

    
    def test_e_get_existing_key(self):
        res = requests.get(self.__class__.nodes_address[2] + '/keyValue-store/subject')
        d = res.json()
        self.assertEqual(d['msg'], 'Success')
        self.assertEqual(d['value'], 'Data Structures')

    
    def test_f_search_nonexistent_key(self):
        res = requests.get(self.__class__.nodes_address[2] + '/keyValue-store/search/subject2')
        d = res.json()
        self.assertEqual(res.status_code, 404)
        self.assertEqual(d['msg'], 'Error')
        self.assertEqual(d['isExist'], 'false')

   
    def test_g_search_existing_key(self):
        res = requests.get(self.__class__.nodes_address[2] + '/keyValue-store/search/subject')
        d = res.json()
        self.assertEqual(d['msg'], 'Success')
        self.assertEqual(d['isExist'], 'true')

    
    def test_h_del_nonexistent_key(self):
        res = requests.delete(self.__class__.nodes_address[0] + '/keyValue-store/subject2')
        d = res.json()
        self.assertEqual(res.status_code, 404)
        self.assertEqual(d['msg'], 'Error')
        self.assertEqual(d['error'], 'Key does not exist')

    
    def test_i_del_existing_key(self):
        res = requests.delete(self.__class__.nodes_address[1] + '/keyValue-store/subject')
        d = res.json()
        self.assertEqual(d['msg'], 'Success')


    def test_j_get_deleted_key(self):
        res = requests.get(self.__class__.nodes_address[0] + '/keyValue-store/subject')
        d = res.json()
        self.assertEqual(res.status_code, 404)
        self.assertEqual(d['msg'], 'Error')
        self.assertEqual(d['error'], 'Key does not exist')

    
    def test_k_put_deleted_key(self):
        res = requests.put(self.__class__.nodes_address[2] + '/keyValue-store/subject', data={'val': 'Distributed System'})
        d = res.json()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(d['replaced'], 0)
        self.assertEqual(d['msg'], 'Added successfully')

    
    def test_l_put_nonexistent_key(self):
        res = requests.put(self.__class__.nodes_address[1] + '/keyValue-store/'+ self.__class__.key1,
                           data={'val': self.__class__.val1,})
        d = res.json()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(d['replaced'], 0)
        self.assertEqual(d['msg'], 'Added successfully')

    
    def test_m_put_existing_key(self):
        res = requests.put(self.__class__.nodes_address[0] + '/keyValue-store/subject', data={'val': self.__class__.val2})
        d = res.json()
        self.assertEqual(d['replaced'], 1)
        self.assertEqual(d['msg'], 'Updated successfully')

    
    def test_n_get_nonexistent_key(self):
        res = requests.get(self.__class__.nodes_address[1] + '/keyValue-store/' + self.__class__.key2)
        d = res.json()
        self.assertEqual(res.status_code, 404)
        self.assertEqual(d['msg'], 'Error')
        self.assertEqual(d['error'], 'Key does not exist')

    def test_o_get_existing_key(self):
        res = requests.get(self.__class__.nodes_address[2] + '/keyValue-store/' + self.__class__.key1)
        d = res.json()
        self.assertEqual(d['msg'], 'Success')
        self.assertEqual(d['value'], self.__class__.val1)

    def test_p_put_key_too_long(self):
        res = requests.put(self.__class__.nodes_address[0] + '/keyValue-store/'+self.__class__.key3, data={'val':self.__class__.val2})

        d = res.json()
        self.assertNotEqual(res.status_code, 200)
        self.assertNotEqual(res.status_code, 201)
        self.assertEqual(d['msg'], 'Error')
        self.assertEqual(d['error'],'Key not valid')

    def test_q_put_key_too_long_on_forwarding_instance(self):
        res = requests.put(self.__class__.nodes_address[1] + '/keyValue-store/'+self.__class__.key3, data={'val':self.__class__.val2})

        d = res.json()
        self.assertNotEqual(res.status_code, 200)
        self.assertNotEqual(res.status_code, 201)
        self.assertEqual(d['msg'], 'Error')
        self.assertEqual(d['error'],'Key not valid')


    def test_r_put_key_without_value(self):
        res = requests.put(self.__class__.nodes_address[0] + '/keyValue-store/'+self.__class__.key1)
        d = res.json()
        self.assertNotEqual(res.status_code, 200)
        self.assertNotEqual(res.status_code, 201)
        self.assertEqual(d['msg'], 'Error')
        self.assertEqual(d['error'], 'Value is missing')

    
    def tearDown(self):
        if self.__class__.all_tests_done:
            print("\nKilling all alive nodes.")
            shell_command = "docker stop $(docker ps -q)"
            subprocess.check_output(shell_command, shell=True)


if __name__ == '__main__':
    unittest.main()
