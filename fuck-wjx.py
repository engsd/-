import ctypes

# Windows High DPI support - fix blurry UI on high-resolution screens
ctypes.windll.shcore.SetProcessDpiAwareness(1)

from wjx.gui import main


if __name__ == "__main__":
    main()
    