module LanguageError where

import Control.Exception (Exception)

newtype LanguageError = LanguageError String deriving Show

instance Exception LanguageError
