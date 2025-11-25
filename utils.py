def _print(message):
    try:
        message = str(message)

    except ValueError:
        return
    return print(f"===== {message} =====")