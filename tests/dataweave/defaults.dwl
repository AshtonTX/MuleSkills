%dw 2.0
output application/json
---
{
  absent: {}.value?,
  explicitNull: {value: null}.value?,
  missingDefault: {}.value default "fallback",
  nullDefault: null default "fallback",
  zero: 0 default 99,
  falseValue: false default true,
  emptyString: "" default "fallback",
  emptyArray: [] default [1],
  // Observed native CLI behavior; Mule compatibility flags may change this.
  invalidNumberDefault: ("abc" as Number) default 0
}
