from .run import run
from docopt import docopt

def test_print_errors(fs, capfd):
    createFile(fs, contents="this will make a lexerror")
    string = "scan --spec=specfile"
    args = docopt(getDocString(), string)
    run(args)
    captured = capfd.readouterr()
    assert captured.out == 'NameExpected: None:1:1\nthis will make a lexerror\n^\nNames begin with capital or underscore and contain only capitals, numbers, and underscore.\n\n'

def createFile(fs, name="specfile", contents="token MINUS '-'"):
    fs.create_file(name, contents=contents)

def getDocString():
    return "Usage: plccng scan --spec=<specfile> [<file> ...]"
