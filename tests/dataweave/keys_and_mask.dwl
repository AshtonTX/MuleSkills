%dw 2.0
import mask from dw::util::Values
output application/json
---
{
  keyComparison: {a: 1} mapObject ((value, key) -> {
    isString: key is String,
    directMatch: key == "a",
    localNameMatch: (key as String) == "a"
  }),
  masked: {
    scalar: {password: "synthetic"},
    nested: {user: {password: "synthetic"}},
    objectValue: {password: {value: "synthetic"}},
    arrayValue: {password: ["synthetic"]}
  } mask "password" with "*****"
}
