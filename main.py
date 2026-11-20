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

        # Oynani yaratib, maxfiylik chegarasi chizig'ini ko'rsatib-yashirib ko'ramiz.
        import tkinter as tk

        root = tk.Tk()
        app = gui.App(root, selftest=True)
        mon = computer.primary_monitor()
        view = computer.region_to_view([100, 100, 400, 300], mon)
        app.border.show(view, mon)
        root.update()
        assert len(app.border.parts) == 4
        c = computer.Computer(region=[100, 100, 400, 300])
        assert c.restricted and c.img_size() == (400, 300)
        try:
            c.to_screen([500, 10])
            raise AssertionError("chegaradan tashqari koordinata rad etilmadi")
        except computer.ActionError:
            pass
        app.border.hide()
        app.hotkeys.stop()
        root.destroy()
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
