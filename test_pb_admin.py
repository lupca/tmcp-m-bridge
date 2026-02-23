from client import PocketBaseClient
import json

c = PocketBaseClient("http://127.0.0.1:8090", "admin@admin.com", "123qweasdzxc")
c.authenticate()
schema = c.get_collection_schema("worksheets")
print(json.dumps(schema, indent=2))
