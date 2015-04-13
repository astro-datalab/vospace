/**
 * Docker.java
 * Author: Matthew Graham (NOAO)
 * Version: Original (0.1) - 1 April 2015
 */

package edu.caltech.vao.vospace.capability;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Properties;

import edu.caltech.vao.vospace.NodeType;
import edu.caltech.vao.vospace.VOSpaceException;
import edu.caltech.vao.vospace.xml.Param;


/**
 * This interface represents the implementation details of a capability 
 * on a container which contains a Docker and executes it 
 */
public class Docker implements Capability {

    private static final NodeType[] domain = new NodeType[] {NodeType.CONTAINER_NODE};
    
    /*
     * Return the registered identifier for this capability
     */
    public String getUri() {
	return "ivo://datalab.noao.edu/vospace/capabilities#docker";
    }


    /*
     * Return nodal applicability of this capability
     */
    public List<NodeType> getApplicability() {
	return Arrays.asList(domain);
    }

    
    /*
     * Set the parameters for the capability
     */
    public void setParams(Param[] params) {

    }

     
    /*
     * Invoke the capability of the parent container on the specified
     * location
     */
    public boolean invoke(String location) throws VOSpaceException {
	boolean success = false;
	try {
	    Properties config = parseConfig(location.substring(0, location.lastIndexOf("/")) + "/docker_cap.conf");



	    success = true;
	} catch (Exception e) {
	    e.printStackTrace(System.err);
	    throw new VOSpaceException(VOSpaceException.INTERNAL_SERVER_ERROR, e.getMessage());
	}
	return success;
    }

    
    /*
     * Parse the configuration file
     */
    private Properties parseConfig(String configFile) throws IOException {
        Properties props = new Properties();
        props.load(new FileInputStream(configFile.substring(7)));
	return props;
    }
     
}
