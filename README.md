# VOSpace Server

![tests](https://github.com/astro-datalab/vospace/actions/workflows/test.yml/badge.svg)
[![Package (pre-release)](https://github.com/astro-datalab/vospace/actions/workflows/package.yml/badge.svg)](https://github.com/astro-datalab/vospace/actions/workflows/package.yml)
[![Version Release](https://github.com/astro-datalab/vospace/actions/workflows/release.yml/badge.svg)](https://github.com/astro-datalab/vospace/actions/workflows/release.yml/badge.svg)

The VOSpace server is a Java based REST API that implements the [VOSpace 2.0 specification](https://ivoa.net/documents/VOSpace/20130329/REC-VOSpace-2.0-20130329.html). For more information about the VOSpace protocol see the [official specification](https://ivoa.net/documents/VOSpace/20130329/REC-VOSpace-2.0-20130329.html) on the IVOA website. For detailed information about the VOSpace server software including database schema and rest bindings see the [VOSpace server documentation](./docs/VOSpace.md). The VOSpace server provides the VOSpace implementation for the [Astro Data Lab Science platform](https://datalab.noirlab.edu/) but can be configured to serve your own distributed storage.

## System Requirements

| Name          | Required Version |
|---------------|------------------|
| Docker Engine | `23.0+`          |
-or-
| Java | `8+`          |
| Apache ANT | `1.10.14+`          |

## Usage

### Docker Run (without database)

To connect to an existing MySQL database simply start a VOSpace container with your configured environment file
and while mounting the appropriate storage directories.

```sh
docker run \
    -it --rm \
    --env-file .env \
    --name vos-api \
    -p "3000:8080" \
    -v "/net/filestore:/net/filestore" \
    ghcr.io/astro-datalab/vospace/vospace:latest
```

### Docker Compose

A docker compose file is provided which can be used to easily startup the VOSpace API with an included MySQL database.
Use the following command to start VOSpace with compose.

```
docker compose up
```

To initialize the database schema on first startup you can use the `vospace_create.sh` script. eg:

```
./scripts/db/vospace_create.sh "$MYSQL_DB_NAME" "$MYSQL_USER" "$MYSQL_PW" vos-mysql
```

### Environment Settings

Various environment settings can be configured in a `.env` file. See the `.env.example` file
for an example of how to configure your environment.  

**Note**: The database settings should match your database configuration when using a standalone database.
**Note**: The storage settings should match your host environment when mounting a network file system.

| Variable Name          | Description                                           | Example                                               |
|------------------------|-------------------------------------------------------|-------------------------------------------------------|
| `DATA_URL`             | External address of the data URL                      | `http://localhost:8080/vospace-2.0/vospace/data`      |
| `TRANSFER_URL`         | External address of the transfers URL                 | `http://localhost:8080/vospace-2.0/vospace/transfers` |
| `AUTH_BASE_URL`        | Base URL of the auth service                          | `http://auth-mock:8000`                               |
| `MYSQL_DB_URL`         | Database url in the form of [host]/[db_name]          | `vos-mysql/vospace_dev`                               |
| `MYSQL_DB_NAME`        | Name of the mysql database                            | `vospace_dev`                                         |
| `MYSQL_USER`           | Name of the mysql user                                | `testuser`                                            |
| `MYSQL_PW`             | The password for the mysql user                       | `[secret]`                                            |
| `MYSQL_ROOT_PW`        | The root password for mysql                           | `[secret]`                                            |
| `PORT`                 | The port of the service in the container              | `8080`                                                |
| `PUBLISH_PORT`         | The port to publish when using compose                | `8002`                                                |
| `STORAGE_ROOT`         | Root location of the file store                       | `/net/dl2/vospace/users`                              |
| `STAGING_ROOT`         | Root location for staged data                         | `/net/dl2/vospace/tmp`                                |
| `STORAGE_USER`         | User for the file store (this should match the host)  | `example_owner`                                       |
| `STORAGE_UID`          | UID for the file store (this should match the host)   | `1001`                                                |
| `STORAGE_GROUP`        | Group for the file store (this should match the host) | `example_group`                                       |
| `STORAGE_GID`          | GID for the file store (this should match the host)   | `1001`                                                |
| `VOS_IDENTIFIER`       | Set the VOS identifier                                | `ivo://datalab.noirlab/vospace`                       |
| `ROOT_NODE_IDENTIFIER` | Set the identifier of the root node                   | `vos://datalab.noirlab!vospace`                       |
| `CAPS_IDENTIFIER`      | Set the identifier of the VOS capabilities            | `ivo://datalab.noirlab/vospace/capabilities`          |
| `DEBUG`                | Enable debugging                                      | `false`                                               |

### Hooks

Various hooks are registered and some configuration is available via the environment settings.

#### `/isValidToken`
___
For each protected request an authentication hook will be called. You should configure your
auth service to accommodate this request. **Note**: the token will be loaded from the `X-DL-AuthToken`
request header (at the moment this isn't configurable). Additional details of the request are provided below:  

**URL:** `${AUTH_BASE_URL}/isValidToken`  
**Method:** `GET`  
**URL Params:**  

- `token`: the token to validate

**Headers:**  

- `X-DL-AuthToken`: the provided auth token

**Expected Responses:**

- Response Status: `200`  
  Response Body: `True`  
  _Indicates successful authentication_

- Response Status: `401`  
  Response Body: `False`  
  _Indicates an error during authentication_

Example request as curl

```
curl "http://authservice/isValidToken?token=example_owner.1.1.notarealtoken"
```

#### `/hasAccess`  
---
For each request to a node resource an authorization hook will be called. You should configure your
auth service to accommodate this request. **Note**: the token will be loaded from the `X-DL-AuthToken`
request header (at the moment this isn't configurable). Additional details of the request are provided below:

**URL:** `${AUTH_BASE_URL}/hasAccess`  
**Method:** `GET`  
**URL Params:**  

- `owner`: the registered owner of node  
- `group`: the registered group of the node

**Headers:**  

- `X-DL-AuthToken`: the provided auth token

**Expected Responses:**

- Response Status: `200`  
  Response Body: `OK`  
  _Indicates that the user has access to the resource based on the user and group settings_  

- Response Status: `401`  
  _Indicates that the user does not have access to the resource_

Example request as curl

```
curl -H 'X-DL-AuthToken: example_owner.1.1.notarealtoken' "http://authservice/hasAccess?owner=example_owner&group=example_group"
```

## Development

The main application code resides in the `java/` directory. We primarily use Docker but the application build files
can be used and deployed directly if desired.

### Installation

#### Docker

1. clone this repository into some directory  
```git clone git@github.com:astro-datalab/vospace.git .```
2. create the `.env` file and add the appropriate settings. (see `.env.example`)
3. generate a build with ANT  
```docker run --rm  -v ./java:/app apache-ant dist```  
**Note:** If you do not have an ANT image you can build it with  
```docker build -f Dockerfile.ApacheAnt -t apache-ant .```
4. start the services with compose  
```docker compose -f compose.dev.yml up```
5. Seed the database with test data (this setup the schema and add some test nodes)  
```./scripts/dev/seedTestData.sh .env```
6. navigate to `http://localhost:3000/vospace-2.0/vospace/` (or the host and port you used)

#### ANT+Java

If you prefer to not use the provided Docker tools you can also build this application directly
with ANT. This approach will not populate the `vospace.properties` file so you must
fill in the values of the file prior to build.

1. clone this repository into some directory  
```git clone git@github.com:astro-datalab/vospace.git .```
2. generate a build with Apache ANT  
```ant build```
3. Deploy your `.war` file to a compatible environment (such as with Tomcat)

### Testing

Various tests are provided in the `testing/` directory and are written in Python. These
tests cover the REST interface itself and not the underlying system components.

To run the test suite, ensure you have an instance running usually at the default
port of 8002 (you can also change the port using a SERVICE_PORT environment variable.)

```sh
python3 -m unittest testing/*.py
```

If your service is on a different port pass a `SERVICE_PORT` setting to the command:

```sh
PUBLISH_PORT=3002 python3 -m unittest testing/*.py
```

### Notes for Legacy Users

This repository has been refactored to heavily rely on Docker. You can use this
repository without Docker but there are a couple of things to make note of when
migrating from older versions of the codebase.

**Properties Files**  
The previous host specific `vospace.properties` files no longer exist. These now
get populated from the environment at runtime (only when using Docker). If you
build the application without Docker you will need to populate the properties
file yourself. See the legacy branch for an example of an old properties file:
<https://github.com/astro-datalab/vospace/blob/legacy/java/vospace.properties.gp04>

  You can also use this snippet to replace the properties file with your current
environment settings (see `.env.example` for example environment):

  ```sh
  envsubst < java/vospace.properties > java/vospace.properties
  ```

**Scripts**  
Various host specific scripts have been moved into `archived/` directories and will
either be restored or retired in the future. If you need to use these
scripts keep in mind that their directory might be different and you might need
to restore them to their original directory (`/java`). Additionally, some of these
scripts may not be compatible with the new Docker version of the service. Archived
scripts can be found at `./scripts/archived`.

**Testing**  
The old integration and load test suites were moved into the `testing/archived`
directory in favor of a test suite which focuses solely on the VOS REST interface
itself. This test suite will be evaluated in the future and restored or moved as
appropriate. You can still run this integration and scale test but note that
the files have moved and might need some adjustment. If you want to test the
VOSpace server, refer to the testing section above.
