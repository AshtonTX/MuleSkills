%dw 2.0
import mergeWith from dw::core::Objects
output application/json
var duplicates = {a: 1, b: 2} ++ {a: 3}
var grouped = [{id: 201, name: "A"}, {id: 202, name: "B"}] groupBy $.id
---
{
  firstDuplicate: duplicates.a,
  allDuplicates: duplicates.*a,
  mergedValue: ({a: 1, b: 2} mergeWith {a: 3}).a,
  reorderedEquality: {a: 1, b: 2} == {b: 2, a: 1},
  numericIndex: grouped[201],
  stringKey: grouped["201"][0].name
}
