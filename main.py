from src.parser import CCParser

if __name__ == "__main__":
    parser = CCParser()
    parser.parse_settings()
    parser.parse_presets()
    parser.parse_keybinds()