echo "********************************************************"
echo INITIALIZE
echo "********************************************************"

curl --request POST \
  --url https://mcprwe-production.up.railway.app/mcp \
  --header 'Accept: application/json, text/event-stream' \
  --header 'Content-Type: application/json' \
  --data '{
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged" : "True"},
                    "sampling": {},
                    "elicitation": {}
                },
                "clientInfo": {
                    "name": "Agentic Gateway",
                    "title": "Agentic Gateway",
                    "version": "1.0.0"
                }
            }
        }'
