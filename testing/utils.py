"""
Various utility classes for the VOS test suite
"""
import re
from dataclasses import dataclass
from datetime import datetime
import requests


class TestUser:
    """
    Represents a file service user for testing purposes
    """
    def __init__(self, username: str):
        self.name = username
        self.token = f"${self.name}.123.123.faketoken"

@dataclass
class NodeProperty:
    """
    Represents a single node property
    """
    key: str
    value: str

class VosXML:
    """
    Provides various methods for generating VOS XML resources
    """
    std_namespace = "http://www.w3.org/2001/XMLSchema-instance"
    namespace = "http://www.ivoa.net/xml/VOSpace/v2.0"
    base_uri = "vos://datalab.noirlab!vospace"

    @staticmethod
    def properties(props: list[NodeProperty]=None):
        """
        Generate node properties as XML
        """
        props_str = "<properties/>"
        if props and (len(props) > 0):
            props_str = "<properties>"
            for p in props:
                props_str += f"<property uri=\"{p.key}\">{p.value}</property>"
            props_str += "</properties>"
        return props_str

    @staticmethod
    def container_node(user: str, dirname: str, props: list[NodeProperty]=None):
        """
        Return the XML to generate a new container node
        """
        schema_type = "vos:ContainerNode"
        uri = f"{VosXML.base_uri}/{user}/{dirname}"

        return (
            f"<node \
                xmlns:xsi='{VosXML.std_namespace}' \
                xmlns='{VosXML.namespace}' \
                xsi:type='{schema_type}' \
                uri='{uri}'>\
                    {VosXML.properties(props)}\
                    <accepts/><provides/><capabilities/><nodes/>\
            </node>"
        )

    @staticmethod
    def link_node(user: str, target: str, link: str, props: list[NodeProperty]=None):
        """
        Return the XML to generate a new link node
        """
        schema_type = "vos:LinkNode"
        target_uri = f"{VosXML.base_uri}/{user}/{target}"
        link_uri = f"{VosXML.base_uri}/{user}/{link}"

        return (
            f"<node \
                xmlns:xsi='{VosXML.std_namespace}' \
                xmlns='{VosXML.namespace}' \
                xsi:type='{schema_type}' \
                uri='{link_uri}'>\
                    {VosXML.properties(props)}\
                    <accepts/><provides/><capabilities/>\
                <target>{target_uri}</target>\
            </node>"
        )

    @staticmethod
    def transfer(user: str, source: str, dest: str):
        """
        Return the XML to generate a new transfer
        """
        target_uri = f"{VosXML.base_uri}/{user}/{source}"
        dest_uri = f"{VosXML.base_uri}/{user}/{dest}"

        return (
            f"<vos:transfer xmlns:vos='http://www.ivoa.net/xml/VOSpace/v2.0'>\
                <vos:target>{target_uri}</vos:target>\
                <vos:direction>{dest_uri}</vos:direction>\
                <vos:view uri='ivo://ivoa.net/vospace/core#defaultview' original='True'/>\
                <vos:protocol uri=''/>\
                <vos:keepBytes>False</vos:keepBytes>\
            </vos:transfer>"
        )

class VosHTTP:
    """
    Provides various methods for calling VOS API endpoints
    """
    def __init__(self, baseUrl):
        self.baseUrl = baseUrl

    def create_container(self, user: TestUser, dir):
        """
        Create a container node or throw an error
        """
        node_xml = VosXML.container_node(user.name, dir)
        res = requests.put(
            f"{self.baseUrl}/nodes/{user.name}/{dir}",
            data=node_xml,
            headers={
                'Content-Type': 'application/xml',
                'X-DL-AuthToken': user.token
            },
            timeout=5000
            )
        if res.status_code != 201:
            raise RuntimeError("Error creating container node")
        return True

    def get_node(self, user: TestUser, dirname: str):
        """
        Return XML for an existing node
        """
        res = requests.get(
            f"{self.baseUrl}/nodes/{user.name}/{dirname}",
            timeout=5000,
            headers={
                'Content-Type': 'application/xml',
                'X-DL-AuthToken': user.token
            })
        if res.status_code != 200:
            raise RuntimeError(f"Error loading node with uri {dirname}")
        return res.text

    def transfer_status(self, user: TestUser, url: str):
        """
        Return the status of a transfer
        """
        job_status = requests.get(
            url,
            timeout=5000,
            headers={
                'X-DL-AuthToken': user.token
            }
            )
        raw_xml = job_status.text
        phase = "QUEUED"
        if m := re.findall(r".+\<phase\>(\w+)<.+", raw_xml, flags=re.M):
            phase = m[0]
        return phase

class VosFile:
    """
    Various useful methods for creating and dealing with file references
    """
    @staticmethod
    def key():
        """
        Return a unique key which can be used within file names to prevent test
        conflicts.
        """
        return datetime.now().strftime('%Y-%m-%d-%M-%S-%f')
