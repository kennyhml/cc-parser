import json
from pathlib import Path

from .log import logging as lg


class CCParser:
    """A helper class that provides the ability to take deprecated cc v5
    settings and parse them into the new config format of v6.

    Attributes
    ----------
    SCHEMA_FILES :class:`list[str]`:
        A list of expected schema files needed to parse the data

    V5_TO_PARSE_FILES :class:`list[str]`:
        A list of expected files to be parsed, rgb.json will be discarded


    PARSE_MAPPING :class:`dict[str, str]`:
        A dictionary mapping new keys to their equivalent in v5
    """

    SCHEMA_FILES = ["settings", "skills", "keybinds", "altcycler"]
    V5_TO_PARSE_FILES = ["settings", "customrotation", "acrc"]
    PARSE_MAPPING: dict[str, str] = {
        "selected_character": "current_char",
        "main_character": "main_char_position",
        "allow_potions": "use_potion",
        "allow_speciality": "use_transform",
        "allow_gold_portal_skills": "gold_portal_skills",
        "stage_1_focus": "focus_enemies_s1",
        "heal_at": "hp_value",
        "game_class": "class",
        "map": "map_key",
        "interact": "interact_key",
        "potion": "potion_key",
        "aura_potion": "aura_potion_key",
        "inventory": "inventory_key",
        "speciality": "transform_key",
        "speciality_2": "switch_gun_key",
        "integrated_dungeon_1": "chaos_ui_alt",
        "integrated_dungeon_2": "chaos_ui_q",
        "pet_ui_1": "pet_alt",
        "pet_ui_2": "pet_p",
        "quest_ui_1": "quest_alt",
        "quest_ui_2": "quest_j",
        "guild_ui_1": "guild_ui_alt",
        "guild_ui_2": "guild_ui_u",
        "bifrost_ui_1": "bifrost_alt",
        "bifrost_ui_2": "bifrost_w",
    }

    def __init__(self) -> None:
        self._ensure_files_present()
        self._load_files_to_parse()
        self._load_schema_files()
        self._create_parsed_data()

    def parse_keybinds(self) -> None:
        """Parses all the keybinds into the new keybinds.json.

        In v5 configs, keybinds were contained in the global keys section of
        the settings.json file, so it will parse them from there.

        First checks if any pairs retained their original key, if so the pair
        will be added to the data right away.
        Otherwise the `PARSE_MAPPING` dictionary is used to check if we can
        find any new versions of deprecated keys in the data to parse and once
        again add the value to that key.
        """
        lg.info("Parsing keybinds...")
        data_to_parse = self.settings_data["global_keys"]
        schema = self.keybinds_schema

        self._add_retained_keys(self.parsed_keybinds, data_to_parse, schema)
        self._add_parse_map_keys(self.parsed_keybinds, data_to_parse, schema)

        lg.info("Adding static values...")
        mouse_key = data_to_parse["move_with"].split("-")[0]
        self.parsed_keybinds["primary_mouse"] = mouse_key

        lg.info(
            f"Parsing keybinds complete. Total keys: {len(self.parsed_keybinds)}, schema keys: {len(schema.keys())}"
        )

    def parse_settings(self) -> None:
        """Parses all the global keys from a v5 config into the different
        sections of v6.

        This is achieved by first checking whether any pairs in the data to
        parse still use the same key as the new data uses, if so that pair
        will just be added right away.

        Otherwise the `PARSE_MAPPING` dictionary is used to check if we can
        find any new versions of deprecated keys in the data to parse and once
        again add the value to that key.
        """
        # all data we need for the sections is in the global keys in v5
        to_parse = self.settings_data["global_keys"]

        for section in ["global", "chaos", "discord", "altcycler"]:
            schema = self.settings_schema[section]
            parsed = self.parsed_settings_data[section] = {}

            self._add_retained_keys(parsed, to_parse, schema)
            self._add_parse_map_keys(parsed, to_parse, schema)

            lg.info(
                f"Parsing '{section}' complete. "
                f"Total keys: {len(parsed)}, schema keys: {len(schema.keys())}. "
                f"Keys not parsed: {set(schema.keys()).difference(parsed.keys())}"
            )

    @staticmethod
    def _add_retained_keys(new_dict: dict, to_parse: dict, schema: dict) -> None:
        """Adds all retained keys to the new dictionary that are still in the
        dictionary to parse and are part of the dictionary schema.

        Parameters
        ----------
        new_dict :class:`dict`:
            The dictionary to parse the data into

        to_parse :class:`dict`:
            The dictionary containing the data to be parsed

        schema :class:`dict`:
            The dictionary containing the schema for the new parsed data
        """
        lg.info("Checking for retained keys...")
        for k, v in to_parse.items():
            if k in schema.keys():
                lg.info(f"Found retained key '{k}'")
                new_dict[k] = v

    def _add_parse_map_keys(self, new_dict: dict, to_parse: dict, schema: dict) -> None:
        """Adds all parse mapped keys to the new dictionary that are still in the
        dictionary to parse and are part of the dictionary schema.

        Parameters
        ----------
        new_dict :class:`dict`:
            The dictionary to parse the data into

        to_parse :class:`dict`:
            The dictionary containing the data to be parsed

        schema :class:`dict`:
            The dictionary containing the schema for the new parsed data
        """
        lg.info("Checking for new keys in parse map...")
        for k, v in self.PARSE_MAPPING.items():
            if k in schema.keys() and v in to_parse.keys():
                lg.info(f"Found new version of deprecated key '{v}': '{k}'")
                new_dict[k] = to_parse[v]

    def _ensure_files_present(self) -> None:
        """Validates that all required files are present.

        Raises
        ------
        `FileNotFoundError`
            When an expected file could not be found
        """
        for f in self.SCHEMA_FILES:
            if not Path(f"src/schema/{f}.json").exists():
                raise FileNotFoundError(f"FATAL: Missing schema '{f}'")

        for f in self.V5_TO_PARSE_FILES:
            if not Path(f"input/{f}.json").exists():
                raise FileNotFoundError(f"FATAL: Missing file to parse '{f}'")

    def _load_files_to_parse(self) -> None:
        """Loads all files to be parsed"""
        with open("input/customrotation.json") as f:
            self.rotation_data: dict[str, dict] = json.load(f)

        with open("input/settings.json") as f:
            self.settings_data: dict[str, dict] = json.load(f)

        with open("input/acrc.json") as f:
            self.altcycler_data: dict[str, dict] = json.load(f)

    def _load_schema_files(self) -> None:
        """Loads all files to be parsed"""
        with open("src/schema/skills.json") as f:
            self.skills_schema: dict[str, dict] = json.load(f)

        with open("src/schema/settings.json") as f:
            self.settings_schema: dict[str, dict] = json.load(f)

        with open("src/schema/altcycler.json") as f:
            self.altcycler_schema: dict[str, dict] = json.load(f)

        with open("src/schema/keybinds.json") as f:
            self.keybinds_schema: dict[str, str] = json.load(f)

    def _create_parsed_data(self) -> None:
        self.parsed_rotation_data: dict[str, dict] = {}
        self.parsed_settings_data: dict[str, dict] = {}
        self.parsed_keybinds: dict[str, str] = {}
        self.parsed_altcycler_data: dict[str, dict] = {}


#    def _save_parsed_files(self) -> None:
#        """Saves all settings to configs"""
#        destinations = {
#            "settings": self.settings_data,
#            "keybinds": self.keybinds_data,
#            "altcycler": self.altcycler_data,
#            "skills": self.skill_data,
#        }
#        for file, var in destinations.items():
#            with open(f"settings/{file}.json", "w") as f:
#                json.dump(var, f, indent=4)
