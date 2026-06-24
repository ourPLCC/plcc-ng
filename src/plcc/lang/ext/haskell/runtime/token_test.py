import subprocess
import textwrap
from pathlib import Path

import pytest

TOKEN_HS = Path(__file__).parent / 'Token.hs'


def _build_and_run(tmp_path, main_hs):
    """Compile a minimal cabal project containing Token.hs and run it."""
    (tmp_path / 'Token.hs').write_text(TOKEN_HS.read_text())
    (tmp_path / 'Main.hs').write_text(main_hs)
    (tmp_path / 'test-token.cabal').write_text(textwrap.dedent("""\
        cabal-version: 3.0
        name:          test-token
        version:       0.1.0.0
        executable     test-token
          main-is:          Main.hs
          other-modules:    Token
          build-depends:    base, aeson, bytestring, text
          default-language: Haskell2010
          hs-source-dirs:   .
    """))
    subprocess.run(['cabal', 'build'], cwd=tmp_path, check=True, capture_output=True)
    result = subprocess.run(
        ['cabal', 'run', 'test-token'],
        cwd=tmp_path, capture_output=True, text=True, input=''
    )
    return result.stdout.strip()


def test_token_parses_kind_and_lexeme(tmp_path):
    output = _build_and_run(tmp_path, textwrap.dedent("""\
        module Main where
        import Data.Aeson (decode)
        import qualified Data.ByteString.Lazy.Char8 as BL
        import Token

        main :: IO ()
        main = do
            let Just tok = decode (BL.pack "{\\"name\\":\\"INT\\",\\"lexeme\\":\\"42\\"}") :: Maybe Token
            putStrLn (tokenKind tok)
            putStrLn (lexeme tok)
    """))
    assert output == "INT\n42"


def test_token_show(tmp_path):
    output = _build_and_run(tmp_path, textwrap.dedent("""\
        module Main where
        import Data.Aeson (decode)
        import qualified Data.ByteString.Lazy.Char8 as BL
        import Token

        main :: IO ()
        main = do
            let Just tok = decode (BL.pack "{\\"name\\":\\"INT\\",\\"lexeme\\":\\"42\\"}") :: Maybe Token
            print tok
    """))
    assert 'INT' in output
    assert '42' in output
