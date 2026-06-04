



curl --request POST \
  --url https://mcprwe-production.up.railway.app/mcp \
  --header 'Accept: application/json, text/event-stream' \
  --header 'Content-Type: application/json' \
  --data '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
	"params": {
    "name": "rwe-life-sciences"
  }
}'

