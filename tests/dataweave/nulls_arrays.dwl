%dw 2.0
import * from dw::core::Arrays
output application/json
---
{
  nullMap: null map $,
  nullSize: sizeOf(null),
  emptyReduce: [] reduce ((item, acc) -> item + acc),
  initializedReduce: [] reduce ((item, acc = 0) -> item + acc),
  takeNegative: take([1, 2, 3], -1),
  takePastEnd: take([1, 2, 3], 10),
  dropPastEnd: drop([1, 2, 3], 10),
  negativeSliceEnd: slice([1, 2, 3], 1, -1),
  outOfBoundsRange: [0, 1, 2, 3, 4, 5][3 to 10],
  reversedRange: [0, 1, 2][-1 to 0],
  removeAllMatches: ["a", "b", "a"] - "a"
}
