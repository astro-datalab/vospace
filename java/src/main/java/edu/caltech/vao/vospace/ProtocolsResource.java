
package edu.caltech.vao.vospace;

import java.util.ArrayList;

import edu.noirlab.datalab.xml.Protocol;
import org.apache.log4j.Logger;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;

@Path("protocols")
public class ProtocolsResource extends VOSpaceResource {

    private static Logger log = Logger.getLogger(ProtocolsResource.class);

    public ProtocolsResource() throws VOSpaceException {
        super();
    }

    /**
    * This method retrieves the list of supported protocols
    *
    * @return the list of supported protocols
    */
    @GET
    @Produces(MediaType.APPLICATION_XML)
    public String getProtocols() throws VOSpaceException {
    log.info("getProtocols");
	StringBuffer sbuf = new StringBuffer("<protocols xmlns=\"http://www.ivoa.net/xml/VOSpace/v2.0\"><accepts>");
	addProtocols(sbuf, manager.SPACE_SERVER_PROTOCOLS);
	sbuf.append("</accepts><provides>");
	addProtocols(sbuf, manager.SPACE_CLIENT_PROTOCOLS);
	sbuf.append("</provides></protocols>");
	return sbuf.toString();
    }

    public void addProtocols(StringBuffer sbuf, ArrayList<Protocol> list) throws VOSpaceException {
	for (Protocol protocol: list) {
	    sbuf.append("<protocol uri=\"" + protocol.getURI() + "\"/>");
	}	
    }

}
