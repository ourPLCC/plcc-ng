{-# LANGUAGE OverloadedStrings #-}
module Token where

import Data.Aeson (FromJSON (..), Value (..), withObject, (.:))
import Data.Aeson.Types (Parser)
import Data.Text (unpack)

data Token = Token { tokenKind :: String, lexeme :: String }
    deriving (Show, Eq)

instance FromJSON Token where
    parseJSON = withObject "Token" $ \o ->
        Token <$> o .: "name" <*> o .: "lexeme"

-- | Parse the plcc-ng wire format children array into name-value pairs.
-- children JSON: [["fieldname", value], ...]
parseChildren :: [[Value]] -> [(String, Value)]
parseChildren raw =
    [(unpack k, v) | [String k, v] <- raw]

-- | Look up a named child and parse it.
parseField :: FromJSON a => [(String, Value)] -> String -> Parser a
parseField pairs name =
    case lookup name pairs of
        Nothing -> fail ("missing field: " ++ name)
        Just v  -> parseJSON v
