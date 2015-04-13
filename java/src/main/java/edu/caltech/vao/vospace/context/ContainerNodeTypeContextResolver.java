/*******************************************************************************
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *  
 *   http://www.apache.org/licenses/LICENSE-2.0
 *  
 *  Unless required by applicable law or agreed to in writing,
 *  software distributed under the License is distributed on an
 *  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 *  KIND, either express or implied.  See the License for the
 *  specific language governing permissions and limitations
 *  under the License.
 *  
 *******************************************************************************/

package edu.caltech.vao.vospace.context;

import javax.ws.rs.ext.ContextResolver;
import javax.ws.rs.ext.Provider;
import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBException;

import edu.caltech.vao.vospace.resource.ContainerNodeType;
import edu.caltech.vao.vospace.resource.DataNodeType;
import edu.caltech.vao.vospace.resource.NodeType;

/**
 * Context provider for providing the JAXBContext for the Person JAXB object
 */
@Provider
public class ContainerNodeTypeContextResolver implements ContextResolver<JAXBContext> {

    private static JAXBContext context;
    static {
        try {
            context = JAXBContext.newInstance("edu.caltech.vao.vospace.resource");
        } catch (JAXBException e) {
            throw new RuntimeException(e);
        }
    }

    public JAXBContext getContext(Class<?> type) {
	System.out.println(type);
        if (NodeType.class.equals(type)) {
	    System.out.println("Matching");
            return context;
        }
        return null;
    }
}
