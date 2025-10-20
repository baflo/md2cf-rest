# Client-Generierung für md2cf REST API

Die md2cf REST API nutzt **OpenAPI 3.1** (Swagger), um automatisch Clients für verschiedene Plattformen zu generieren.

## OpenAPI Schema exportieren

```bash
# Server muss laufen
curl http://localhost:8000/openapi.json > openapi.json

# Oder mit Python
python -c "
from md2cf.rest_api import app
import json

schema = app.openapi()
print(json.dumps(schema, indent=2))
" > openapi.json
```

## Client-Generierung mit OpenAPI Generator

### Installation

```bash
# Via npm
npm install @openapitools/openapi-generator-cli -g

# Via Docker
docker pull openapitools/openapi-generator-cli
```

### 1. Java/Kotlin Client

```bash
# Java
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g java \
  -o ./clients/java \
  --additional-properties=library=okhttp-gson,artifactId=md2cf-client,groupId=com.example

# Kotlin
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g kotlin \
  -o ./clients/kotlin \
  --additional-properties=library=jvm-okhttp4
```

**Verwendung:**
```java
import com.example.md2cf.ApiClient;
import com.example.md2cf.api.DefaultApi;
import com.example.md2cf.model.*;

public class Example {
    public static void main(String[] args) {
        ApiClient client = new ApiClient();
        client.setBasePath("http://localhost:8000");

        DefaultApi api = new DefaultApi(client);

        ConvertRequest request = new ConvertRequest()
            .markdown("# Hello World\n\nThis is **bold**.");

        ConvertResponse response = api.convertMarkdown(request);
        System.out.println(response.getConfluenceStorageFormat());
    }
}
```

### 2. TypeScript/JavaScript Client

```bash
# TypeScript/Axios
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o ./clients/typescript-axios

# TypeScript/Fetch
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-fetch \
  -o ./clients/typescript-fetch

# JavaScript/Node
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g javascript \
  -o ./clients/javascript
```

**Verwendung (TypeScript):**
```typescript
import { DefaultApi, Configuration, ConvertRequest } from './clients/typescript-axios';

const config = new Configuration({
  basePath: 'http://localhost:8000'
});

const api = new DefaultApi(config);

const request: ConvertRequest = {
  markdown: '# Hello World\n\nThis is **bold**.'
};

const response = await api.convertMarkdown(request);
console.log(response.data.confluence_storage_format);
```

### 3. C# / .NET Client

```bash
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g csharp \
  -o ./clients/csharp \
  --additional-properties=targetFramework=net6.0,packageName=Md2cf.Client
```

**Verwendung:**
```csharp
using Md2cf.Client.Api;
using Md2cf.Client.Model;

var api = new DefaultApi("http://localhost:8000");

var request = new ConvertRequest
{
    Markdown = "# Hello World\n\nThis is **bold**."
};

var response = api.ConvertMarkdown(request);
Console.WriteLine(response.ConfluenceStorageFormat);
```

### 4. Go Client

```bash
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g go \
  -o ./clients/go \
  --additional-properties=packageName=md2cf
```

**Verwendung:**
```go
package main

import (
    "context"
    "fmt"
    "github.com/example/md2cf"
)

func main() {
    cfg := md2cf.NewConfiguration()
    cfg.Servers = md2cf.ServerConfigurations{
        {URL: "http://localhost:8000"},
    }

    client := md2cf.NewAPIClient(cfg)

    request := md2cf.ConvertRequest{
        Markdown: "# Hello World\n\nThis is **bold**.",
    }

    response, _, err := client.DefaultAPI.ConvertMarkdown(context.Background()).
        ConvertRequest(request).Execute()

    if err != nil {
        panic(err)
    }

    fmt.Println(response.GetConfluenceStorageFormat())
}
```

### 5. PHP Client

```bash
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g php \
  -o ./clients/php \
  --additional-properties=packageName=Md2cfClient
```

**Verwendung:**
```php
<?php
require_once(__DIR__ . '/vendor/autoload.php');

$config = Md2cfClient\Configuration::getDefaultConfiguration()
    ->setHost('http://localhost:8000');

$apiInstance = new Md2cfClient\Api\DefaultApi(
    new GuzzleHttp\Client(),
    $config
);

$request = new \Md2cfClient\Model\ConvertRequest([
    'markdown' => '# Hello World\n\nThis is **bold**.'
]);

try {
    $result = $apiInstance->convertMarkdown($request);
    print_r($result->getConfluenceStorageFormat());
} catch (Exception $e) {
    echo 'Exception: ', $e->getMessage(), PHP_EOL;
}
```

### 6. Ruby Client

```bash
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g ruby \
  -o ./clients/ruby \
  --additional-properties=gemName=md2cf_client
```

**Verwendung:**
```ruby
require 'md2cf_client'

Md2cfClient.configure do |config|
  config.host = 'localhost:8000'
  config.scheme = 'http'
end

api_instance = Md2cfClient::DefaultApi.new

request = Md2cfClient::ConvertRequest.new(
  markdown: '# Hello World\n\nThis is **bold**.'
)

begin
  result = api_instance.convert_markdown(request)
  puts result.confluence_storage_format
rescue Md2cfClient::ApiError => e
  puts "Error: #{e}"
end
```

### 7. Rust Client

```bash
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g rust \
  -o ./clients/rust \
  --additional-properties=packageName=md2cf_client
```

**Verwendung:**
```rust
use md2cf_client::{apis::configuration::Configuration, apis::default_api, models::ConvertRequest};

#[tokio::main]
async fn main() {
    let config = Configuration {
        base_path: "http://localhost:8000".to_string(),
        ..Default::default()
    };

    let request = ConvertRequest {
        markdown: "# Hello World\n\nThis is **bold**.".to_string(),
    };

    match default_api::convert_markdown(&config, request).await {
        Ok(response) => println!("{}", response.confluence_storage_format),
        Err(e) => eprintln!("Error: {:?}", e),
    }
}
```

## Swagger Codegen (Alternative)

```bash
# Installation
npm install -g swagger-codegen

# Client generieren
swagger-codegen generate \
  -i http://localhost:8000/openapi.json \
  -l typescript-axios \
  -o ./clients/swagger-typescript
```

## Postman Collection

```bash
# OpenAPI zu Postman konvertieren
npm install -g openapi-to-postmanv2

openapi2postmanv2 \
  -s openapi.json \
  -o md2cf-postman-collection.json \
  -p

# In Postman importieren: File > Import > md2cf-postman-collection.json
```

## Docker-basierte Generierung

```bash
# Funktion für einfache Nutzung
generate_client() {
  local LANG=$1
  docker run --rm \
    -v ${PWD}:/local \
    openapitools/openapi-generator-cli generate \
    -i http://host.docker.internal:8000/openapi.json \
    -g $LANG \
    -o /local/clients/$LANG
}

# Verwendung
generate_client java
generate_client typescript-axios
generate_client go
generate_client csharp
```

## Verfügbare Generatoren

Liste aller verfügbaren Generatoren:

```bash
openapi-generator-cli list
```

Wichtige Generatoren:
- `java` - Java mit verschiedenen Libraries (okhttp-gson, retrofit2, etc.)
- `kotlin` - Kotlin
- `typescript-axios` - TypeScript mit Axios
- `typescript-fetch` - TypeScript mit Fetch API
- `javascript` - JavaScript/Node.js
- `csharp` - C# / .NET
- `go` - Go
- `php` - PHP
- `ruby` - Ruby
- `rust` - Rust
- `python` - Python
- `swift5` - Swift 5
- `dart` - Dart/Flutter
- `android` - Android (Kotlin)
- `cpp-restsdk` - C++

## Python Client (Alternative zu direkter Nutzung)

```bash
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./clients/python \
  --additional-properties=packageName=md2cf_client,projectName=md2cf-client
```

## Automatisches Build-Script

```bash
#!/bin/bash
# generate-all-clients.sh

set -e

API_URL="http://localhost:8000/openapi.json"
OUTPUT_DIR="./clients"

echo "Generating clients for md2cf REST API..."

# Exportiere OpenAPI Schema
curl -s $API_URL > openapi.json

# Definiere zu generierende Clients
declare -a LANGUAGES=(
  "java"
  "kotlin"
  "typescript-axios"
  "javascript"
  "csharp"
  "go"
  "php"
  "ruby"
  "rust"
  "swift5"
)

# Generiere jeden Client
for LANG in "${LANGUAGES[@]}"; do
  echo "Generating $LANG client..."
  openapi-generator-cli generate \
    -i openapi.json \
    -g $LANG \
    -o $OUTPUT_DIR/$LANG \
    --skip-validate-spec
done

echo "Client generation complete!"
echo "Clients are in: $OUTPUT_DIR/"
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Generate API Clients

on:
  push:
    branches: [ main ]
    paths:
      - 'md2cf/rest_api.py'

jobs:
  generate-clients:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e ".[rest]"

      - name: Start API server
        run: |
          python -m uvicorn md2cf.rest_api:app --host 0.0.0.0 --port 8000 &
          sleep 5

      - name: Export OpenAPI schema
        run: |
          curl http://localhost:8000/openapi.json > openapi.json

      - name: Generate TypeScript client
        uses: openapi-generators/openapitools-generator-action@v1
        with:
          generator: typescript-axios
          openapi-file: openapi.json
          config-file: .openapi-generator/typescript-config.json

      - name: Commit generated clients
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add clients/
          git commit -m "Auto-generate API clients" || true
          git push
```

## Best Practices

1. **Versionierung**: Taggen Sie OpenAPI Schemas mit der API-Version
2. **Dokumentation**: Fügen Sie ausführliche Beschreibungen in den Pydantic-Modellen hinzu
3. **Beispiele**: Nutzen Sie `Config.json_schema_extra` für Beispiel-Requests
4. **Validierung**: Validieren Sie das Schema regelmäßig
5. **Testing**: Testen Sie generierte Clients automatisch

## Verbesserung der OpenAPI-Dokumentation

```python
# In md2cf/rest_api.py

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="md2cf REST API",
        version="0.1.0",
        description="""
## Markdown to Confluence Converter API

Diese API konvertiert Markdown zu Confluence Storage Format und ermöglicht
direktes Publizieren zu Confluence.

### Features
- ✅ Vollständige Markdown-Unterstützung
- ✅ XHTML-konformes Output
- ✅ Direkte Confluence-Integration
- ✅ OpenAPI 3.1 Schema

### Authentifizierung
Für `/publish` Endpoint wird ein Confluence API Token benötigt.
        """,
        routes=app.routes,
        tags=[
            {
                "name": "conversion",
                "description": "Markdown conversion operations"
            },
            {
                "name": "publishing",
                "description": "Confluence publishing operations"
            }
        ]
    )

    # Füge zusätzliche Metadaten hinzu
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "email": "support@example.com"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

## Weiterführende Tools

- **Stoplight Studio**: Visueller OpenAPI Editor
- **Swagger Editor**: Online OpenAPI Editor
- **Redocly**: Erweiterte API-Dokumentation
- **API Platform**: Automatische API-Generierung

## Support

Für weitere Informationen:
- OpenAPI Generator: https://openapi-generator.tech/
- FastAPI OpenAPI: https://fastapi.tiangolo.com/advanced/extending-openapi/
