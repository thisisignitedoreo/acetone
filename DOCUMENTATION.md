
# acetone docs

## syntax
acetone's syntax is a little bit different than some other programming languages.

1. everything is case insensetive (e.g. `inbox` = `InBox` = `INBOX`)
2. statement arguments are delimited by nothing, they just have to be different
   tokens
3. there are only 7 token types:<br/>
   3.1. TOKEN_WORD: any word: `word`<br/>
   3.3. TOKEN_REFWORD: any word reference: `[variable]`<br/>
   3.1. TOKEN_STRING: any string: `"stringy\r\n\t\\"`<br/>
   3.2. TOKEN_NUMBER: any number (no floating point magic): `123`<br/>
   3.3. TOKEN_REFNUMBER: any number reference: `[0]`<br/>
   3.4. TOKEN_OCURLY: `{`<br/>
   3.5. TOKEN_CCURLY: `}`<br/>
   3.6. TOKEN_SEMICOLON: `;`<br/>
   3.7. TOKEN_EQUALS: `=`<br/>
   also note: word tokens can have not only alphanumeric symbols, but also some
   specials, since they are not used in any way: `_+-:/!?`<br/>
   but, they have to not start with a number: `aword`, `bump+`, `++--`, `???`
   are all a valid words.

every statement ends with a semicolon<br/>
blocks of code are enclosed in curly braces (`{` and `}`)

comments start with a double slash (`//`)

## variables
you can define variables like this:
```dart
name = 0
```

those can only be numbers

note: you can dereference variable like this:
```dart
copy [ref] outbox;
```

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
- `copy A B`</br>
  copy from A (either `inbox`, number or pointer) to B (either `outbox`, number
  or pointer)
- `break`</br>
  break from current loop
- `continue`</br>
  go to start of a current loop
- `call`</br>
  either call a macro (inline it) or go to a section (does **not** go back to
  where it was called)
- `addlabel X text`</br>
  create label with text on X

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

times is a directive which will repeat code snippet n times, while setting variable
to iteration.

```dart

// from 0 to 2 step 1
times 0 3 n {
    copy inbox n;
}

```


---

ig that is all
