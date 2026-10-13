%dw 2.0
output application/json
---
{
  decimalSum: 0.1 + 0.2,
  thirdsDoNotRoundTrip: (10 / 3) * 3 != 10,
  halfUp: 2.345 as String {format: "0.00"},
  halfEven: 2.5 as String {format: "0", roundMode: "HALF_EVEN"},
  negativeRound: round(-2.5),
  fixedScale: 1.1 as String {format: "0.00"},
  strictValidDate: ("02/15/2026" as Date {format: "MM/dd/uuuu", mode: "STRICT"}) as String,
  smartInvalidDate: ("02/30/2026" as Date {format: "MM/dd/uuuu"}) as String
}
