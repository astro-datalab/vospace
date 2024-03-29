/**
 * HttpGetProtocolHandler.java
 * Author: Matthew Graham (Caltech)
 * Version: Original (0.1) - 31 July 2006
 */

package edu.caltech.vao.vospace.protocol;

import edu.caltech.vao.vospace.VOSpaceException;
import edu.caltech.vao.vospace.VOSpaceManager;
import edu.caltech.vao.vospace.storage.StorageManager;

import java.io.InputStream;
import java.io.IOException;
import java.util.UUID;
import java.util.regex.Pattern;

import org.apache.commons.httpclient.HttpClient;
import org.apache.commons.httpclient.HttpStatus;
import org.apache.commons.httpclient.methods.GetMethod;
import org.apache.log4j.Logger;

import static edu.noirlab.datalab.vos.Utils.log_error;
import edu.noirlab.datalab.xml.Protocol;

/**
 * This class handles the implementation details for the HTTP 1.1 GET protocol
 */
public class HttpGetProtocolHandler implements ProtocolHandler {
	private static Logger logger = Logger.getLogger(VOSpaceManager.class.getName());

	private static String BASE_URL = "http://localhost:7007";

    /*
     * Return the registered identifier for this protocol
     */
    public String getUri() {
	return "ivo://ivoa.net/vospace/core#httpget";
    }

    /*
     * Set the base url for the protocol
     */
    public void setBaseUrl(String baseUrl) {
        BASE_URL = baseUrl;
    }

    /*
     * Fill in the details for a ProtocolType
     */
	public Protocol admin(String nodeUri, Protocol protocol, int mode) throws VOSpaceException {
		try {
			if (mode == SERVER) {
				protocol.setEndpoint(BASE_URL + "/" + UUID.randomUUID());
			} else {
				// Check url is valid
				if (!Pattern.matches("^http\\://[a-zA-Z0-9\\-\\.]+\\.[a-zA-Z]{2,3}(/\\S*)?$", protocol.getEndpoint()))
					throw new VOSpaceException(VOSpaceException.VOFault.InternalFault, "Destination URI is invalid", nodeUri);
			}
			return protocol;
		} catch (VOSpaceException ve) {
			log_error(logger, ve);
			throw ve;
		} catch (Exception e) {
			log_error(logger, e);
			throw new VOSpaceException(e, nodeUri);
		}
	}

    /*
     * Invoke the protocol handler and transfer data
     */
    public boolean invoke(Protocol protocol, String location, StorageManager backend) throws IOException {
	boolean success = false;
	try {
	    HttpClient client = new HttpClient();
	    GetMethod get = new GetMethod(protocol.getEndpoint());
 	    int statusCode = client.executeMethod(get);
	    if (statusCode != HttpStatus.SC_OK) {
			IOException ioe = new IOException(get.getStatusLine().toString());
			logger.error(ioe.toString());
			throw ioe;
		}
	    //	    URI uri = new URI(location);
	    InputStream in = get.getResponseBodyAsStream();
	    backend.putBytes(location, in);
            /*
	    BufferedInputStream bis = new BufferedInputStream(in);
	    FileOutputStream fos = new FileOutputStream(uri.getPath());
            byte[] buffer = new byte[8192];
            int count = bis.read(buffer);
            while (count != -1 && count <= 8192) {
                fos.write(buffer, 0, count);
                count = bis.read(buffer);
            }
            if (count != -1) {
                fos.write(buffer, 0, count);
            }
	    fos.close();
	    bis.close();
	    */
	    get.releaseConnection();
	    success = true;
	    //	} catch (URISyntaxException e) {
	    //	    throw new IOException(e.getMessage());
	} catch (VOSpaceException e) {
		log_error(logger, e);
	    throw new IOException(e.getMessage());
	}
	return success;
    }

}
