
# acetone docs

## syntax
acetone's syntax is a little bit different than some other programming languages.

1. everything is case insensetive (e.g. `inbox` = `InBox` = `INBOX`)
2. statement arguments are delimited by nothing, they just have to be different
   tokens
3. there are only 7 token types:
   3.1. TOKEN_WORD: any word: `word`
   3.2. TOKEN_NUMBER: any number (no floating point magic): `123`
   3.3. TOKEN_REFNUMBER: any pointer (e.g. number reference): `[0]`
   3.4. TOKEN_OCURLY: `{`
   3.5. TOKEN_CCURLY: `}`
   3.6. TOKEN_SEMICOLON: `;`
   3.7. TOKEN_EQUALS: `=` _(unused yet)_
   also note: word tokens can have not only alphanumeric symbols, but also some
   specials, since they are not used in any way: `_+-:/!?`<br/>
   but, they have to not start with a number: `aword`, `bump+`, `++--`, `???`
   are all a valid words.

every statement ends with a semicolon<br/>
blocks of code are enclosed in curly braces (`{` and `}`)

comments start with a double slash (`//`)

## internal statements
a handful of statements are just in-game commands:
- `inbox`
- `outbox`
- `copyfrom X`
- `copyto X`
- `add X`
- `sub X`
- `bump+ X`
- `bump- X`
- `jump L`
- `jumpz L`
- `jumpn L`
all others are either shortcuts or interface logic:
- `copy A B`
  copy from A (either `inbox`, number or pointer) to B (either `outbox`, number
  or pointer)
- `break`
  break from current loop
- `continue`
  go to start of a current loop
- `call`
  either call a macro (inline it) or go to section (does **not** go back to
  where it was called)

## ifs, loops, macros

`if`s use jumpz and jumpn logic:<br/>
a sample if statement:
```dart
if <CONDITION> {
    // do stuff
} else { // completely optional
    // do other stuff
}
```
a `<CONDITION>` is:
- `zero`
- `not zero`
- `positive`
- `negative`

while loops are alike the if statements, but in the end the go back if condition
is true:
```dart
while <CONDITION> {
    // do stuff multiple times
}
```

`<CONDITION>` is alike the `if` one, but can be empty: then the loop will be
unconditional (infinite)

macro is a chunk of code that isn't written anywhere in the assembly by itself,
however, is inlined on every call.

```dart
macro some_macro {
    inbox;
    inbox;
    inbox;
}

call some_macro;
call some_macro;
call some_macro;
// this will result in 6 inboxes in resulting assembly
```

section is a chunk of code that usually is skipped, but on call is executed, and
then program cursor goes to code that is next to section, **not back to call 
location**:

```dart
section yes {
    copy 4 outbox;
}

section no {
    copy 5 outbox;
}

inbox;
if zero { call yes; }
else { call no; }
// note: this results in an infinite loop
```

note that both section and macro names are case sensetive.

---

ig that is all
