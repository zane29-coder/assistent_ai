import sys


def _selftest() -> int:
    """.exe to'g'ri yig'ilganini tekshirish: barcha modullar yuklanadimi."""
    try:
        import anthropic  # noqa: F401
        import tkinter  # noqa: F401

        import docx  # noqa: F401
        import pptx  # noqa: F401
        import xlrd  # noqa: F401

        from assistent import agent, attachments, computer, gui, hotkeys, tasks_store  # noqa: F401

        computer.Computer().screenshot_block()
        hotkeys.parse("ctrl+alt+s")
        return 0
    except Exception:  # noqa: BLE001
        import traceback

        with open("selftest_error.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        return 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    from assistent.gui import main

    main()
