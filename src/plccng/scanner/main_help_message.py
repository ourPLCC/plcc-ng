helpMessage = '''
    Arguments:

        <specfile>      A path to a file containing a JSON formatted lexical spec.

        <file>          A path to an input file. If no files given, read from stdin.
                        If <file> is '-', read from stdin. When EOF is read, process
                        next file.

    <specfile> Format:

        [
            {
                "Type": "Skip",
                "Name": "WHITESPACE",
                "Regex": "\\s+"  // Backslash is escape char in JSON. Then \\ is a single backslash; which is regex's escape char.
            },
            {
                "Type": "Token",
                "Name": "NUMBER",
                "Regex": "\\d+"
            }
        ]

    Skip Format

        {
            "Type": "Skip",
            "Name": "WHITESPACE",
            "Lexeme": "         ",
            "File": "/workspace/cool/prog.cool",
            "Line": 3,
            "Column": 1
        }

    Token Format:

        {
            "Type": "Token",
            "Name": "NUMBER",
            "Lexeme": "42",
            "File": "/workspace/cool/prog.cool",
            "Line": 3,
            "Column": 10
        }

    LexError Format:

        {
            "Type": "LexError",
            "Unmatched": "+12=54"
            "File": "/workspace/cool/prog.cool",
            "Line": 3,
            "Column": 13
        }'''
