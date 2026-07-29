#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v cabal &>/dev/null; then skip "cabal not available"; fi
    cabal update
    SPEC_DIR="${BATS_TEST_TMPDIR}/spec"
    mkdir -p "$SPEC_DIR"
    OUT_DIR="${HASKELL_ROUNDTRIP_OUT_DIR:-${BATS_TEST_TMPDIR}/out}"
    mkdir -p "$OUT_DIR"
    cat > "$SPEC_DIR/arith.plcc" << 'EOF'
token NUM '\d+'
token PLUS '\+'
skip SPACE '\s+'
%
<Program>              ::= <Expr:expr>
<Expr>                 ::= <Term:term> <ExprRest:rest>
<ExprRest:AddRest>     ::= PLUS <Term:term> <ExprRest:rest>
<ExprRest:NilRest>     ::=
<Term>                 ::= <NUM:num>
%
Haskell
Program
%%%
_run :: Program -> String
_run (Program e) = evalExpr e
%%%
Expr
%%%
evalExpr :: Expr -> String
evalExpr (Expr t r) = evalRest r (read (evalTerm t) :: Int)
%%%
ExprRest
%%%
evalRest :: ExprRest -> Int -> String
evalRest (AddRest t r) acc = evalRest r (acc + read (evalTerm t) :: Int)
evalRest NilRest acc = show acc
%%%
Term
%%%
evalTerm :: Term -> String
evalTerm (Term n) = lexeme n
%%%
EOF
}

@test "haskell pipeline: emit-build-run roundtrip" {
    SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"
    MODEL_JSON="${BATS_TEST_TMPDIR}/model.json"
    LL1_JSON="${BATS_TEST_TMPDIR}/ll1.json"

    plcc-spec "$SPEC_DIR/arith.plcc" > "$SPEC_JSON"
    plcc-model "$SPEC_JSON" > "$MODEL_JSON"
    plcc-spec "$SPEC_DIR/arith.plcc" | plcc-ll1 > "$LL1_JSON"
    plcc-haskell-emit --output="$OUT_DIR" < "$MODEL_JSON"
    plcc-haskell-build --output="$OUT_DIR"

    result=$(echo '1 + 2' \
        | plcc-tokens "$SPEC_JSON" \
        | plcc-trees --ll1="$LL1_JSON" \
        | plcc-haskell-run --output="$OUT_DIR")

    echo "$result" | grep -q '"value":"3"'
}
