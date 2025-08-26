
"""
Test VOSpace API interface
"""
import os
import unittest
import requests
import time
from testing.utils import (
    VosHTTP,
    VosFile,
    TestUser,
    VosXML,
    NodeProperty
)

# Register various access details for the service.
SERVICE_PORT = os.environ.get("PUBLISH_PORT", "3002")
SERVICE_ORIGIN = f"http://127.0.0.1:{SERVICE_PORT}"
SERVICE_URL = f"{SERVICE_ORIGIN}/vospace-2.0/vospace"

# Initialize our test API client
REST = VosHTTP(SERVICE_URL)

# this creates a directory for all of our test data to go in, this keeps the
# data nested and out of the way
ROOT_TEST_DIR = f"tests-auto-{VosFile.key()}"
REST.create_container(TestUser("userone"), ROOT_TEST_DIR)


class VOSpace(unittest.TestCase):
    """
    Test VOSpace API endpoints
    """
    def setUp(self):
        """
        These steps get performed before each test
        """
        self.base = SERVICE_URL
        self.user1 = TestUser("userone")
        self.user2 = TestUser("usertwo")
        self.testdir = f"{ROOT_TEST_DIR}/test-{VosFile.key()}"

        # create a container as our working directory for testing
        REST.create_container(self.user1, self.testdir)

    def default_params(self, token: str):
        """
        Return default headers for VOSpace request
        """
        return dict(
            headers={
                'Content-Type': 'application/xml',
                'X-DL-AuthToken': token
            },
            timeout=5000
        )

    def test_availability(self):
        """
        Simple test call to discovery service to make sure it is available
        """
        res = requests.get(SERVICE_URL, timeout=5000)
        self.assertEqual(res.status_code, 200)

    def test_get_node(self):
        """
        Retrieve our main test container
        """
        node_url = f"{SERVICE_URL}/nodes/{self.user1.name}"
        args = self.default_params(self.user1.token)

        # first check a valid node
        res = requests.get(f"{node_url}/{self.testdir}", **args)
        self.assertEqual(res.status_code, 200)
        self.assertIn("vos:ContainerNode", res.text)

        # next make sure a non existent node throws a 404
        res = requests.get(f"{node_url}/some--missing--dir", **args)
        self.assertEqual(res.status_code, 404)
        self.assertNotIn("vos:ContainerNode", res.text)

    def test_create_node(self):
        """
        Test creating a new container node
        """
        new_dir = f"{self.testdir}/test-{VosFile.key()}"
        node_xml = VosXML.container_node(self.user1.name, new_dir)
        res = requests.put(
            f"{SERVICE_URL}/nodes/{self.user1.name}/{new_dir}",
            data=node_xml,
            **self.default_params(self.user1.token)
            )
        self.assertEqual(res.status_code, 201)
        self.assertIn("vos:ContainerNode", res.text)

    def test_delete_node(self):
        """
        Test node deletion
        """
        # first create a node that we can delete
        del_testdir = f"{self.testdir}/del-test-{VosFile.key()}"
        REST.create_container(self.user1, del_testdir)
        node_url = f"{SERVICE_URL}/nodes/{self.user1.name}"
        args = self.default_params(self.user1.token)

        # now delete the node we created
        res = requests.delete(f"{node_url}/{del_testdir}", **args)
        self.assertEqual(res.status_code, 204)

        # next make sure deleting a non existent node throws an error
        res = requests.get(f"{node_url}/some--missing--dir", **args)
        self.assertEqual(res.status_code, 404)

    def test_link_node(self):
        # first create a node that we can link later
        fro_dir = f"{self.testdir}/ln-target-{VosFile.key()}"
        REST.create_container(self.user1, fro_dir)

        # now create the link
        to_dir = f"{self.testdir}/ln-{VosFile.key()}"
        node_xml = VosXML.link_node(self.user1.name, fro_dir, to_dir)
        res = requests.put(
            f"{SERVICE_URL}/nodes/{self.user1.name}/{to_dir}",
            data=node_xml,
            **self.default_params(self.user1.token)
            )

        # ensure the request completed and that the link contains a reference
        # to the target URI
        self.assertEqual(res.status_code, 201)
        to_xml = REST.get_node(self.user1, to_dir)
        self.assertIn("vos:LinkNode", to_xml)
        self.assertIn(fro_dir, to_xml)

    def test_set_property(self):
        """
        Test setting properties on existing nodes
        """
        # configure various settings
        prop = NodeProperty(key="TAG", value="testing_new_tag")
        req_params = self.default_params(self.user1.token)
        testdir = f"{self.testdir}/test-{VosFile.key()}"
        node_url = f"{SERVICE_URL}/nodes/{self.user1.name}/{testdir}"

        # first we'll create a node to use and make sure it doesnt have the
        # target property
        REST.create_container(self.user1, testdir)
        self.assertNotIn(prop.value, REST.get_node(self.user1, testdir))

        # after the container is created use the same container XML with an
        # additional property to update
        new_node = VosXML.container_node(self.user1.name, testdir, [ prop ])
        res = requests.post(
            node_url,
            data=new_node,
            **req_params
            )
        # make sure the request succeeded and the tag exists
        self.assertEqual(res.status_code, 200)
        self.assertIn(prop.value, REST.get_node(self.user1, testdir))

        # Change the property one more time and make sure it persists
        nprop = NodeProperty(key=prop.key, value="updated_tag")
        new_node = VosXML.container_node(self.user1.name, testdir, [ nprop ])
        res = requests.post(
            node_url,
            data=new_node,
            **req_params
            )
        self.assertEqual(res.status_code, 200)
        self.assertIn(nprop.value, REST.get_node(self.user1, testdir))

    def test_move_node(self):
        """
        Tests moving a node via transfer methods
        """
        # first create a node that we can move later, we'll also verify that
        # we can load the created node
        fro_dir = f"{self.testdir}/mv-src-{VosFile.key()}"
        REST.create_container(self.user1, fro_dir)
        REST.get_node(self.user1, fro_dir)

        # now move the created node to the "to_dir"
        to_dir = f"{self.testdir}/mv-dest-{VosFile.key()}"
        transfer_xml = VosXML.transfer(self.user1.name, fro_dir, to_dir)
        res = requests.post(
            f"{SERVICE_URL}/sync",
            data=transfer_xml,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-DL-AuthToken': self.user1.token
            },
            timeout=5000,
            allow_redirects=False
            )

        # we remove the /results/transferDetails from the returned URL
        # and then use that to check the status
        # TODO: This is how we do it in our client, we should verify this
        # is appropriate
        job_url = res.headers.get('Location').replace(
            "/results/transferDetails", "")

        # use a polling method to wait for the job to finish
        phase = REST.transfer_status(self.user1, job_url)
        while phase.upper() not in ["ERROR", "COMPLETED"]:
            time.sleep(0.5)
            phase = REST.transfer_status(self.user1, job_url)
        self.assertEqual(phase, "COMPLETED")

        # once the job succeeds then retrieve the node and make sure it exists
        # and is valid
        moved_node = REST.get_node(self.user1, to_dir)
        self.assertGreater(len(moved_node), 0)
        self.assertIn(to_dir, moved_node)
        # now make sure loading the original node throws an error
        self.assertRaises(
            RuntimeError, lambda x="": REST.get_node(self.user1, fro_dir)
            )

    def test_lock_node(self):
        """
        Tests locking a node
        """

    def test_transfer(self):
        """
        Various transfer creation tests
        """

    def test_copy_node(self):
        """
        Tests copying a node via transfer methods
        """

if __name__ == "__main__":
    unittest.main()
