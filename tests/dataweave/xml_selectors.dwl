%dw 2.0
output application/json
var simple = read('<root><name>first</name><name>second</name></root>', "application/xml")
// Different sibling shapes reproduce the compatibility-property docs example.
var mixed = read('<root><users><user><lname>last</lname><name>first</name></user><user><name>first</name><name>second</name></user></users></root>', "application/xml")
---
{
  simpleSingle: simple.root.name,
  simpleMultiple: simple.root.*name,
  mixedSingle: mixed.root.users.*user map $.name,
  mixedMultiple: mixed.root.users.*user map $.*name,
  explicitFirst: mixed.root.users.*user map ($.*name)[0]
}
