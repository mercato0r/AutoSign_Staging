"""Entry point utama untuk menjalankan AutoSign Pro."""

from autosign.ui.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
