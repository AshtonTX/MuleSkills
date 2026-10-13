%dw 2.0
output application/json
---
// `p` is a Mule function; the standalone CLI does not define it.
p('http.port')
