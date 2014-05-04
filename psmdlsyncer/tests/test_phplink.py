from psmdlsyncer.php import CallPHP


if __name__ == "__main__":
    p = CallPHP()
    here=""
    while here.strip() != "quit":
        here = input()
        p.command(here.strip(), '')
