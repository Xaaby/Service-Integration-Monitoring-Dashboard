from . import app as root_app  # type: ignore


def main():
    root_app.render_overview()


if __name__ == "__main__":
    main()

