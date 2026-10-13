%dw 2.0
output application/json
var arr = [10, 20, 30]
var idx = [1]
---
{
  // Single-quoted strings avoid &quot; inside a double-quoted XML attribute.
  singleQuoted: 'a' ++ "b",
  quotesInsideSingle: 'say "hi"',
  // Valid DataWeave can contain the sequence that ends an XML CDATA section.
  cdataEndSequence: arr[idx[0]]>5,
  spacedEquivalent: arr[idx[0]] > 5
}
