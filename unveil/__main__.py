import sys
import unveil


def main():
    return unveil.cli(auto_envvar_prefix="UNVEIL")


if __name__ == '__main__':
    sys.exit(main())
