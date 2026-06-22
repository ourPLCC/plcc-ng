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

=== "Python"
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
    Python

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

=== "Java"
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
    Java

    Prog
    %%%
    public void _run() {
        System.out.println(exp.eval());
    }
    %%%

    WholeExp
    %%%
    public int eval() {
        return Integer.parseInt(whole.lexeme);
    }
    %%%

    SubExp
    %%%
    public int eval() {
        return exp1.eval() - exp2.eval();
    }
    %%%
    ```

### Build

```bash
plcc-make -s subtract.plcc
```

Exits silently on success.

### Scanner

```bash
plcc-scan -s subtract.plcc samples
```

Expected output:

```text
samples:1:1 WHOLE '3'
samples:3:1 MINUS '-'
samples:3:2 LP '('
samples:3:3 WHOLE '3'
samples:3:4 COMMA ','
samples:3:5 WHOLE '2'
samples:3:6 RP ')'
samples:5:1 MINUS '-'
samples:5:2 LP '('
samples:5:3 MINUS '-'
samples:5:4 LP '('
samples:5:5 WHOLE '4'
samples:5:6 COMMA ','
samples:5:7 WHOLE '1'
samples:5:8 RP ')'
samples:5:9 COMMA ','
samples:5:11 MINUS '-'
samples:5:12 LP '('
samples:5:13 WHOLE '3'
samples:5:14 COMMA ','
samples:5:15 WHOLE '2'
samples:5:16 RP ')'
samples:5:17 RP ')'
```

### Parser

```bash
plcc-parse -s subtract.plcc samples
```

Expected output:

```text
Prog
  WholeExp
    WHOLE '3' [-:1:1]
Prog
  SubExp
    WholeExp
      WHOLE '3' [-:3:3]
    WholeExp
      WHOLE '2' [-:3:5]
Prog
  SubExp
    SubExp
      WholeExp
        WHOLE '4' [-:5:5]
      WholeExp
        WHOLE '1' [-:5:7]
    SubExp
      WholeExp
        WHOLE '3' [-:5:13]
      WholeExp
        WHOLE '2' [-:5:15]
```

### Interpreter

```bash
plcc-rep -s subtract.plcc samples
```

Expected output:

```text
3
1
2
```
