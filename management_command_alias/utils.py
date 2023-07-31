from django.conf import settings


def alias_map(argv):
    if len(argv) > 1:
        argv[1:2] = [getattr(settings, "COMMAND_ALIASES", {}).get(argv[1], argv[1])]
    return argv
