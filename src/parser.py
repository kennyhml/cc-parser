import json
import os


class CCParser:

    SCHEMA_FILES = ["settings", "skills", "keybinds", "altcycler"]
    V5_TO_PARSE_FILES = ["settings", "customrotation.json", "acrc.json"]

    def __init__(self) -> None:
        self._load_files_to_parse()

    def _ensure_files_present(self) -> None:
        for f in self.SCHEMA_FILES:
            if not os.path.exists(f"schema/{f}.json"):
                raise FileNotFoundError(f"FATAL: Missing schema '{f}'")

        for f in self.V5_TO_PARSE_FILES:
            if not os.path.exists(f"input/{f}.json"):
                raise FileNotFoundError(f"FATAL: Missing file to parse '{f}'")

    def _load_files_to_parse(self) -> None:
        """Loads all the settings from configs"""
        with open("settings/altcycler.json") as f:
            self.altcycler_data: dict[str, dict] = json.load(f)

        with open("settings/settings.json") as f:
            self.settings_data: dict[str, dict] = json.load(f)

        with open("settings/keybinds.json") as f:
            self.keybinds_data: dict[str, dict] = json.load(f)

        with open("settings/skills.json") as f:
            self.skill_data: dict[str, dict] = json.load(f)

    def _save_parsed_files(self) -> None:
        """Saves all settings to configs"""
        destinations = {
            "settings": self.settings_data,
            "keybinds": self.keybinds_data,
            "altcycler": self.altcycler_data,
            "skills": self.skill_data,
        }
        for file, var in destinations.items():
            with open(f"settings/{file}.json", "w") as f:
                json.dump(var, f, indent=4)
