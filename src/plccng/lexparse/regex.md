# Regular Expressions

A lexical rule contains a type (e.g., skip or token), a name, and a
pattern. For this discussion we are focused on the pattern.

A pattern is a regular expression that will be given to Python's
`re` package. The question is, what should the syntax for specifying
a regular expression in PLCC?

There are some constraints. First, regular expressions rely on escape
sequences to escape the normal meaning of a character. Here are some
examples

    s       Match the letter s.
    \s      Match a whitespace character.
    a+      Match one or more letter a.
    a\+     Match the letter a followed by a plus character.
    \\+     Match one or more backslash characters.

Second, PLCC allows line comments.

    Content # Hash starts a comment. The rest of the line is a comment.

Why does this matter? If it didn't allow line comments, and if regular
expressions where the last thing on a line, then we could just assume
that all characters following the rule name is a regex. Whitespace
characters would be the only problem.

But since PLCC allows line comments, a regex must be delimited, or
it must allow escaping of #. Delimiters are more traditional.

Third, if we use delimiters, then the delimiter itself needs to be
escaped to allow it to be used in the regex.

    "\""    # Match a quote.

That means you'd have to escape the escape to pass one backslash
to regex. So here are the same regex examples above but in our
quoted strings.

    "s"       Match the letter s.
    "\\s"     Match a whitespace character.
    "a+"      Match one or more letter a.
    "a\\+"    Match the letter a followed by a plus character.
    "\\\\+"   Match one or more backslash characters.

This is necessary because each escaped escape is replaced by a single
escape when "unquoted".

The problem here is that both regex and our quoting syntax use the same
escape character. So this gives us at least two ways out.

1. Use a different escape syntax.
2. Don't support escapes.

In the first, we could use a different character for escaped. Like %.

    "%""    Match one double-quote.
    "%%"    Match one percent.
    "s"     Match one s.
    "\s"    Match one whitespace.
    "a+"    Match one or more a.
    "a\+"   Match one a followed by one plus.
    "\\+"   Match one or more backslash characters.

In the second, we could allow different delimiters.

    "'"     Match one single-quote.
    '"'     Match one double-quote.
    "s"     Match one s.
    "\s"    Match one whitespace.
    "a+"    Match one or more a.
    "a\+"   Match one a followed by one plus.
    "\\+"   Match one or more backslash characters.

Python takes this further and allows triple character delimiters
''' and """.

Sed allows any character to be used as a delimiter to avoid collisions
and eliminate the need for escapes. Here are a few examples. As long
as the first and last character match.

    _'_     Match one single-quote.
    /"/     Match one double-quote.
    qsq     Match one s.
    %\s%    Match one whitespace.
    "a+"    Match one or more a.
    "a\+"   Match one a followed by one plus.
    "\\+"   Match one or more backslash characters.

This greatly simplifies implementation. The regex that matches such beasts
is:

    (\S)(?:(?!\1).)*\1

It matches a non-whitespace character, followed by zero or more of
any character other than that character, followed by that character again.
