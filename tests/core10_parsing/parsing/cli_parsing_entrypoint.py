from core.core10_parsing.cli.registry import command_registry
from core.core10_parsing.cli.simple_parse import simple_parse


if __name__ == '__main__':
    print(command_registry)

    x = command_registry['mgr']['parser'].parse_known_args()
    print(x)

    #command_registry['mgr']['parser'].parse_known_args(['--help'])

    x = command_registry['mgr']['parser'].parse_known_args(['-c', '/etc/x.yml', '--set', 'a=b', '--set', 'c=d', 'config', 'show', '--set', "u=v"])
    print(x)
    print(x[0].__dict__)

    parsed = simple_parse(['mgr', '-c', '/etc/x.yml', '--set', 'a=b', 'config', 'set', '--set', 'c=d', '-sc', 'special'])
    print(parsed)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--foo', action='append')
    parser.add_argument('bar')
    parser.add_argument('--badger', action='append')
    print(parser.parse_known_args(['--foo', 'oo','--badger', 'BAR', 'spam', '--foo', 'x', '-do', 'a', '--badger', 'o']))