# Backing Platform — Apache Jena Fuseki

`jena-mcp` is a **client** of an Apache Jena **Fuseki** server. This page provides a
Docker recipe for deploying one locally to serve as the target of
`JENA_FUSEKI_URL`. For production topologies, follow the upstream
[Apache Jena Fuseki documentation](https://jena.apache.org/documentation/fuseki2/).

!!! note "Backing-system recipe"
    Each connector in the ecosystem follows the same convention — a
    `docs/platform.md` recipe for the system it integrates with, accompanied by a
    sample Compose stack that mirrors
    [`services/`](https://github.com/Knuckles-Team). Systems offered only as a
    managed service have no local recipe.

## Single-node deployment (Compose)

The following stack runs one Fuseki server on `:3030` with a persistent data volume.
It mirrors the ecosystem service definition at `services/apache-jena/compose.yml`:

```yaml
# docker/fuseki.compose.yml
services:
  fuseki:
    image: secoresearch/fuseki:latest
    container_name: fuseki
    hostname: fuseki
    restart: unless-stopped
    ports:
      - "3030:3030"            # Fuseki HTTP endpoint + admin UI
    environment:
      - ADMIN_PASSWORD=admin
    volumes:
      - fuseki_data:/fuseki

volumes:
  fuseki_data:
```

```bash
docker compose -f docker/fuseki.compose.yml up -d

# Confirm the server is answering
curl -s http://localhost:3030/$/ping
```

## Connect jena-mcp

```bash
export JENA_FUSEKI_URL=http://localhost:3030
export JENA_USERNAME=admin
export JENA_PASSWORD=admin
export JENA_SSL_VERIFY=False           # only if Fuseki sits behind self-signed TLS

jena-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

## Combined deployment

A combined stack places Fuseki and the MCP server on one Docker network, so the
server reaches Fuseki by container name:

```yaml
# docker/stack.compose.yml
services:
  fuseki:
    image: secoresearch/fuseki:latest
    hostname: fuseki
    ports: ["3030:3030"]
    environment:
      - ADMIN_PASSWORD=admin
    volumes: ["fuseki_data:/fuseki"]

  jena-mcp:
    image: knucklessg1/jena-mcp:latest
    depends_on: [fuseki]
    environment:
      - JENA_FUSEKI_URL=http://fuseki:3030
      - JENA_USERNAME=admin
      - JENA_PASSWORD=admin
      - TRANSPORT=streamable-http
      - HOST=0.0.0.0
      - PORT=8000
    ports: ["8000:8000"]

volumes:
  fuseki_data:
```

```bash
docker compose -f docker/stack.compose.yml up -d
```

## Create a dataset

With the server running, create a dataset for SPARQL and Graph Store operations:

```bash
curl -s -u admin:admin -X POST http://localhost:3030/$/datasets \
  --data "dbName=ds&dbType=tdb2"
```

The same operation is available through the [`jena_admin`](usage.md#as-an-mcp-server)
tool (`create_dataset`) and the `JenaApi.create_dataset()` method.
