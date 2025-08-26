# VOSpace
Datalab server implementation of [VOSpace 2.0 specification](https://ivoa.net/documents/VOSpace/20130329/REC-VOSpace-2.0-20130329.html)


## System description
Our instantiation of the specification is done in a Java REST API over a tomcat server. 

The VOSpace code uses a mysql database, usually running in the same machine as the Tomcat server does.
The code connects to it via unix socket. (Typically when connecting to a database if the host is `localhost`
as opposed to an ip address even if the identity 127.0.0.1, the client will try to use the unix socket 
file, which is much faster.)
Archival data storage and accounts folders are mounted over NFS.

Also access to the VOSpace instance happens over proxy from the main web server.

We use the [Apache Wink](http://wink.incubator.apache.org/index.html) RESTful framework to facilitate 
some of the work that normally goes into the WEB-INF/web.xml file. The Apache Wink project has been 
retired since 2017. The code is very stable but if at some point it creates a problem we can always
move the REST bindings to the web.xml file.

With Wink, instead of defining each of the REST APIs as entries in the web.xml, we use a text
 file: `WEB-INF/application` that lists all the available resources that implement the REST
bindings.

`E.g.`\

| REST Binding | Resource |
| ------------ | -------- |
|/data | edu.caltech.vao.vospace.DataResource |
|/nodes | edu.caltech.vao.vospace.NodeResource |
|/properties | edu.caltech.vao.vospace.PropertiesResource |
|/protocols | edu.caltech.vao.vospace.ProtocolsResource |
|/register | edu.caltech.vao.vospace.RegisterResource |
|/resutls | edu.caltech.vao.vospace.ResultsResource |
|/sync | edu.caltech.vao.vospace.SyncResource |
|/transfers | edu.caltech.vao.vospace.TransferResource |
|/views | edu.caltech.vao.vospace.ViewsResource |
| N/A | edu.caltech.vao.vospace.VOSpaceExceptionMapper |
| N/A | edu.caltech.vao.vospace.NodeMessageBodyWriter |
| N/A | edu.caltech.vao.vospace.NodeMessageBodyReader |
| N/A | edu.noirlab.datalab.vos.NodeMessageBodyWriter |
| N/A | edu.caltech.vao.vospace.NodeMessageBodyReader



Notice the NodeMessageBodyWriter and NodeMessageBodyReader java classes at the end of the list. 
These are used to serialize/deserialize the xml load to and from java objects. Something the WINK
framework does automatically behind the scenes.

``Note:`` The new [VOSpace specification v. 2.1](https://www.ivoa.net/documents/VOSpace/20180620/REC-VOSpace-2.1.html) 
is very similar to [v. 2.0](https://ivoa.net/documents/VOSpace/20130329/REC-VOSpace-2.0-20130329.html) except that it includes
 some improvements to the protocols and transfers but for the most part it is the same.

## VOSpace Data Model

![](https://ivoa.net/documents/VOSpace/20130329/vospace-node-hierarchy.png)

### Database
The VOSpace database is pretty simple and follows the data model, with only a handful of tables.

Main tables:\
* `nodes`\
Contains an entry for every file type on disk, which are referred as `nodes`.
The most relevant attributes in a `nodes` entry are:
  * *URI/identifier*: A unique identifier for the node.
  * *owner*: owner of the node
  * *location*: where the node is actually on disk
  * *depth*: The subdirectory level

* `properties`\
Contains an entry for every file type/node on disk. The relation between the `properties` and `nodes` table are 1:1\
The attributes in this table are meta information on the node, such as read/write permissions, ctime, mtime, etc
  
* `addl_props`\
Additional metadata information.
  
* `capabilities`\
Matches a node with a capability. A capability is another service interface that can handle the node or its contents
  in a particular way. For instance, it might be a cutout service that knows how to cut images in a particular way.
  
* `transfers` and `results`\
When a job is requested these two tables will keep the transfer uri and state.
  

## Improvements / TODO
### 08/31/2021
We've performed the following improvements on the code, see git commits:
- `34867f6a`,`821a5394`,`ccea0c77`,`529d7c5b`\
  Logging 
- `dfc8781a`,`dfc8781a`\
  SQL improvements
- `37733d4d`\
  Ignoring MD5 attribute
- `5074907c`\
  Duplicate copying effort bug
- `7df247d7`,`d265ddf6`,`ef81b369`,`0e8bbc76`,`b25a4b7d1be`\
  XML serialization performance improvement
- `d59eb094`\
  Improving transfer DB and SQL inner workings.
  
### Further improvements / TODO
There still a few more things it can be done:
* In the `nodes` & `properties` table:
  * create a column with a shorter unique identifier:\
    `i.e` 8 byte numeric key  and use that column to:
    * join against the properties table and other tables instead of using the very long `identifier` column.
    * ability to set the parent on nodes. I will make easier/faster to find a node's children.
  * shorten the `identifier` column and make its index more compact by 
    removing the vospace + owner prefix, 30+ characters of
    redundant information.
* Make the `properties` table more compact by using integers, instead of characters, to 
  describe the node permissions.
* Having a background job that calculates and sets each node/file MD5/SHA checksum
    
## System requirements
- java 1.8
- tomcat 5.5 and above

## Build and Installation

### Apache ANT
Under the ./java directory there is a `build.xml` *ant* file.

To list available *ant* commands/targets do:

```
ant -p
Buildfile: ./vospace/java/build.xml

        Ant build file for VOSpace 2.0

Main targets:

 clean    clean up
 compile  compile the source
 deploy   deploy to Tomcat webapps directory
 dist     generate the distribution
Default target: dist
```

by running `ant` or `ant dist` a `vospace-2.0.war` will be created. Then simply copy/drop
that file into your tomcat webapps directory and restart tomcat server.

#### ANT with Docker
There is a Docker file available for those that do not have a local Java environment. To run Apache Ant with docker first build the image and then run the desired the commands.
1. If you do not have a local image for ANT first build it
```
docker build -f Dockerfile.ApacheAnt -t apache-ant .
```
2. Now run various ANT commands using the image above:
```
docker run --rm  -v ./java:/app apache-ant [command]
```

## Testing

### Use a direct call to the API
```curl -v 'http://vostest.datalab.noirlab.edu:8080/vospace-2.0/vospace/nodes/ls_dr8?detail=min&uri=vos://datalab.noao!vospace/ls_dr8/south/tractor/275'```

returns:
```
   <node xmlns="http://www.ivoa.net/xml/VOSpace/v2.0" 
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:type="vos:ContainerNode"
         uri="vos://datalab.noao!vospace/ls_dr8"
         busy="false">
         <properties />
         <nodes />
   </node>
```
### Test scripts
See `README` file in the `test` directory for more information about how to run these tests.
