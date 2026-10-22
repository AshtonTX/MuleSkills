# DataWeave correctness details

Reference for [the DataWeave rules](../../../instructions/dataweave.instructions.md). Read the section that applies before writing that code. Items marked (documented) are stated in MuleSoft documentation; items marked (CLI) were observed with the DataWeave CLI (runtime 2.12.2, language levels 2.4–2.9) and should be confirmed on the project's runtime when they decide the outcome.

## DataWeave inside Mule XML

Most scripts in a Mule project sit in the flow file, in a Transform Message or an inline `#[...]` expression. Leave each script where the project keeps it: do not move an inline script to a `.dwl` file, or back, unless that is the task.

- A Transform Message holds one script per output: `ee:set-payload` and `ee:set-attributes` under `ee:message`, and `ee:set-variable` under `ee:variables`. Each is either inline in `<![CDATA[ ... ]]>` or an external file named by `resource`, which is resolved statically and cannot use `${...}` placeholders. Change only the output the task concerns. See [Transform Message XML](https://docs.mulesoft.com/mule-runtime/4.9/transform-dataweave-xml-reference).
- An inline expression has no header unless it is written on one line with `---`, for example `#[output application/json --- payload]`. With no `output` directive the format follows the inputs: `application/java` when there is no input, the shared MIME type when all inputs agree, and an error when they differ (documented). Do not assume JSON; keep or add the directive where the consumer needs a specific format. See [DataWeave header](https://docs.mulesoft.com/dataweave/2.9/dataweave-language-introduction#dw_header).
- Keep `%dw 2.0`, the `output` directive and its writer properties when changing a script body, unless the task is to change the output.

## Values and defaults

- Use `default` only when the contract intentionally treats missing or null values alike; it does not replace `false`, `0`, empty strings, arrays or objects. `isEmpty` is true for `null`, `""`, `[]` and `{}`. When absent and explicit null differ, check key presence (`payload.field?` is true for an explicit null) separately from the value. Do not silently convert malformed amounts or dates into valid-looking defaults. `("abc" as Number) default 0` returned `0` at levels 2.4–2.9 in the native CLI, but this is not portable exception handling: MuleSoft documents `com.mulesoft.dw.defaultOperator.disableExceptionHandling=true` from level 2.5, which disables catching runtime exceptions. Validate malformed input explicitly and verify recovery behavior on the actual runtime and compatibility settings. See [system properties](https://docs.mulesoft.com/dataweave/2.9/dataweave-system-properties) and [DataWeave defaults](https://docs.mulesoft.com/dataweave/2.9/dataweave-cookbook-defaults).
- Every `if` needs an `else`, and every branch or `match` case should return a value the output contract allows, not an accidental `null`.
- Compare with `==` unless the contract allows cross-type equality; `~=` coerces (`1 ~= "1"` is true). See [operators](https://docs.mulesoft.com/dataweave/2.9/dw-operators).
- Overloaded functions resolve to the first declaration that accepts the arguments, so declare specific types before `Any`. See [functions](https://docs.mulesoft.com/dataweave/2.9/dataweave-functions).
- `readUrl` on a network URL makes a real call that processor mocks do not intercept; use `classpath://` resources in tests or isolate the call.
- Preserve required order and duplicates. Do not apply sorting, deduplication, trimming, or case conversion unless the contract calls for them.

## Numbers and money

- Preserve exact decimal values through parsing, arithmetic, Java/connector boundaries and comparison; a binary floating-point round trip can lose money precision.
- `as Number` is more lenient than most contracts (CLI): it accepts `.5`, `5.`, `+5`, `0012` and exponents (`"1e3"` becomes `1E+3`), and rejects surrounding spaces, `1,000` and `NaN`. When the contract defines the allowed format of numeric strings, check the string against it before coercing.
- Scale is not kept: `1.10` becomes `1.1` after arithmetic, `as String`, and in CSV or XML output; only an unchanged input number passes through JSON as written (CLI). Trailing zeros are stripped from language level 2.5 (Mule 4.5); at 2.4 the literal `1.10` stayed `1.10` (CLI; documented as `com.mulesoft.dw.stripTrailingZeroes`), so a `minMuleVersion` upgrade can change output. Format explicitly when output needs fixed decimals (`as String {format: "0.00"}`).
- Division keeps 34 significant digits, so `(10 / 3) * 3` is not `10`; multiply before dividing and round once at the end. `avg([])` and division by zero fail (CLI).
- Avoid locale-dependent formats unless the contract names a locale (`locale: "de"` writes `1.234,50`).

## Dates and times

- With a `format`, the default parsing mode silently turns `02/30/2026` into `02/28/2026` (CLI). If invalid dates must fail, use `mode: "STRICT"` with `uuuu` for the year; `STRICT` with `yyyy` rejected valid dates (CLI). Never use `YYYY` for a calendar year: it is the week-based year (`2026-12-29` formats as `2027-12-29`, CLI). See [type coercion](https://docs.mulesoft.com/dataweave/2.9/dataweave-types-coercion).
- Say whether a value is an instant or a local time, and in which zone. A string without an offset coerced `as DateTime` became UTC whatever the machine's time zone (CLI); parse it as `LocalDateTime` and attach the zone the contract defines. Date-times with different offsets compare by instant (CLI). Adding `|P1M|` to January 31 gives February 28. In `America/Chicago`, a time in the spring-forward gap moved forward an hour and a repeated autumn time took the earlier, daylight offset (CLI); state how gaps and repeated hours are handled when local times matter.

## Nulls and objects

- `map`, `filter`, `joinBy` and `sizeOf` on `null` return `null` rather than an empty result (CLI). Decide whether a null collection means an empty one.
- Give `reduce` an initial accumulator (`(item, acc = 0) -> ...`); otherwise the first element becomes the accumulator, which can change the result type, and an empty array returns `null`. See [reduce](https://docs.mulesoft.com/dataweave/2.9/dw-core-functions-reduce).
- Whole-object equality is key-order sensitive: `{a: 1, b: 2} == {b: 2, a: 1}` is false, and `distinctBy $` and `contains` also treat reordered objects as different (CLI). Compare or deduplicate by the relevant fields.

## Selectors, keys, joins and ordering

- On objects, `payload.key` returns only the first matching key; use `.*key` when duplicates must all be read, and `..*key` for every nested match including duplicate keys. On XML input, single-value selection can depend on sibling shape and compatibility settings: a simple repeated `<name>` returned the first value, but mapping across differently shaped `<user>` elements returned the second name for one user (CLI). Use `.*key` and choose explicitly when elements can repeat; do not rely on a universal first/second outcome from `.key`. See `com.mulesoft.dw.valueSelector.selectsAlwaysFirst` in the [system properties](https://docs.mulesoft.com/dataweave/2.9/dataweave-system-properties). Null handling differs between functions (for example `upper(null)` is `null`, `contains(null, x)` is `false`). See [selectors](https://docs.mulesoft.com/dataweave/2.9/dataweave-selectors).
- Object keys are DataWeave `Key` values with a local name, namespace and attributes. Use `key as String` when intentionally comparing only the local name; a key is not equal to a String under `==` (CLI). See [Object type](https://docs.mulesoft.com/dataweave/2.9/dataweave-types#dw_type_object). Wrap computed keys in parentheses (`obj[("k" ++ id)]`).
- `join`, `leftJoin` and `outerJoin` from `dw::core::Arrays` return `{l, r}` pairs in the left list's order, one per match, so a left item with two matches appears twice. An unmatched item has no `r` (or `l`) key at all, so test with `pair.r?`. Keys are compared as strings: numeric `1` matched string `"1"` (CLI).
- `orderBy` keeps ties in input order and compares strings by code point (`"A"`, `"B"`, `"a"`, `"b"`; `"10"` before `"9"`). It failed on `null` sort keys. At language levels 2.4–2.9 it coerced mixed strings and numbers with only a warning (`[5, 1, "10"]` gave `[1, "10", 5]`), while the native CLI's default level rejected them (CLI). This does not establish every later Mule engine's behavior; see `com.mulesoft.dw.stableOrderBy` in the version's [system properties](https://docs.mulesoft.com/dataweave/2.9/dataweave-system-properties). Convert sort keys to one type and handle nulls first.

## Maintainability

- Prefer readable transformations with small named functions or variables when they remove meaningful duplication. Put functions reused across scripts in a module under `src/main/resources` (for example `modules/`, imported as `modules::Name`) following the project's layout. Do not introduce a folder named `dw`: it shares the `dw::` prefix with the built-in modules. Logic shared across applications belongs in a DataWeave library published to Exchange and added as a pinned dependency, not copied. See [custom modules](https://docs.mulesoft.com/dataweave/2.9/dataweave-create-module).
- Declare `input`/`output` directives with MIME types where the format matters. Type annotations on variables, parameters and return values, and named types for contract shapes, surface mismatches earlier; they do not replace the null and malformed-value checks.
