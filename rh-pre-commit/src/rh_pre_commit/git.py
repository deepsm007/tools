import subprocess  # nosec


def run(*args, **kwargs):
    """
    A small wrapper around git to avoid duplicating this code
    """
    kwargs_with_defaults = {"timeout": 3600}
    kwargs_with_defaults.update(kwargs)

    return subprocess.run(  # nosec
        ["git", *args],
        shell=False,
        check=False,
        **kwargs_with_defaults,
    )


def config(name, value=None, flags=None):
    args = ["config"] + [f"--{flag}" for flag in flags or []] + [name]

    if value:
        args.append(value)

    return run(
        *args,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )


def init_template_dir(value=None):
    """
    Get/set the init template dir

    Returns:
        if setting:
            success := (True|False)
        if getting:
            path := (current dir string|None)
    """
    proc = config("init.templateDir", value, flags=["global"])
    success = proc.returncode == 0

    if value:
        return success

    if success:
        return proc.stdout.decode().strip()

    return None
