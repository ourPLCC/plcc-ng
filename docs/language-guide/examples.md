# Examples

## Example: Subtraction language

This end-to-end example implements a small expression language that evaluates
subtraction expressions. It walks through all three grammar sections and shows
the output of each pipeline stage.

### Sample programs

Create a file named `samples`:

```text
3
-(3,2)
-(-(4,1), -(3,2))
```

### Grammar file

Create `subtract.plcc`:

```text
# Subtraction language
skip WHITESPACE '\s+'
token WHOLE     '\d+'
token MINUS     '\-'
token LP        '\('
token RP        '\)'
token COMMA     ','
%
<Prog>         ::= <Exp:exp>
<Exp:WholeExp> ::= <WHOLE:whole>
<Exp:SubExp>   ::= MINUS LP <Exp:exp1> COMMA <Exp:exp2> RP
%
% subtract Python
Prog
%%%
def _run(self):
    print(self.exp.eval())
%%%

WholeExp
%%%
def eval(self):
    return int(self.whole.lexeme)
%%%

SubExp
%%%
def eval(self):
    return self.exp1.eval() - self.exp2.eval()
%%%
```

### Build

```bash
plcc-make -g subtract.plcc
```

<!-- TODO: verify plcc-make output format (below adapted from PLCC's plccmk output) -->
Expected output:

```text
plcc-ng 0.39.2 | subtract.plcc
Nonterminals (* indicates start symbol):
  <Exp>
 *<Prog>

Abstract classes:
  Exp
```

### Scanner

```bash
plcc-scan -g subtract.plcc samples
```

<!-- TODO: verify plcc-scan output format -->
Expected output:

```text
   1: WHOLE '3'
   3: MINUS '-'
   3: LP '('
   3: WHOLE '3'
   3: COMMA ','
   3: WHOLE '2'
   3: RP ')'
   5: MINUS '-'
   5: LP '('
   5: MINUS '-'
   5: LP '('
   5: WHOLE '4'
   5: COMMA ','
   5: WHOLE '1'
   5: RP ')'
   5: COMMA ','
   5: MINUS '-'
   5: LP '('
   5: WHOLE '3'
   5: COMMA ','
   5: WHOLE '2'
   5: RP ')'
   5: RP ')'
```

### Parser

```bash
plcc-parse -g subtract.plcc samples
```

<!-- TODO: verify plcc-parse output format and flags -->
Expected output:

```text
<Prog>
| <Exp:WholeExp>
| | WHOLE "3"
<Prog>
| <Exp:SubExp>
| | MINUS "-"
| | LP "("
| | <Exp:WholeExp>
| | | WHOLE "3"
| | COMMA ","
| | <Exp:WholeExp>
| | | WHOLE "2"
| | RP ")"
<Prog>
| <Exp:SubExp>
...
```

### Interpreter

```bash
plcc-rep -g subtract.plcc --tool=subtract samples
```

<!-- TODO: verify plcc-rep output format -->
Expected output:

```text
3
1
2
```
