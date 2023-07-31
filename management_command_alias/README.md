Simple Management Command Aliases
=================================

July 2023


A simple way to add management command aliases can be to simply map the argv inputs to `execute_from_command_line()` in
`manage.py`:

```python
def alias_map(argv):
    if len(argv) > 1:
        argv[1:2] = [settings.COMMAND_ALIASES.get(argv[1], argv[1])]
    return argv

if __name__ == "__main__":
    execute_from_command_line(alias_map(sys.argv))
```

then in your settings:

```python
COMMAND_ALIASES = {
    "mm": "makemigrations",
    "sp": "shell_plus",
}
```
