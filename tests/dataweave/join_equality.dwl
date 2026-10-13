%dw 2.0
import join from dw::core::Arrays
output application/json
var left = [{id: 1}]
var right = [{id: "1"}]
---
{
  strictFilterCounts: left map (l) -> sizeOf(right filter (r) -> r.id == l.id),
  joinCount: sizeOf(join(left, right, (l) -> l.id, (r) -> r.id))
}
