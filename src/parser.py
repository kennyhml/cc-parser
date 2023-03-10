import json
import os
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
    V5_TO_PARSE_FILES = ["settings", "customrotation", "acrc", "rgb"]
    PARSE_MAPPING: dict[str, str] = {
        "selected_character": "current_char",
        "main_character": "main_char_position",
        "allow_potions": "use_potions",
        "allow_speciality": "use_transform",
        "allow_awakening": "use_awakening",
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
        "id": "discord_id",
        "token": "discord_token",
        "error_mention": "at_on_events",
        "post_special_portal": "post_specials",
        "post_progress": "post_time",
        "post_statistics": "post_updates",
        "shutdown_pc": "acr_shutdown_pc",
        "aid_research": "include_guild",
        "priority": "skill_priorities",
    }

    def __init__(self) -> None:
        self._ensure_files_present()
        self._load_files_to_parse()
        self._load_schema_files()
        self._create_parsed_data()

    def __call__(self) -> None:
        self._wipe_output_folder()

        self._ensure_preset_completeness()
        self.parse_settings()
        self.parse_presets()
        self.parse_keybinds()
        self.parse_altcycler()
        self._save_parsed_files()

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
            f"Parsing 'keybinds' complete. "
            f"Total keys: {len(self.parsed_keybinds)}, schema keys: {len(schema.keys())}. "
            f"Keys not parsed: {set(schema.keys()).difference(self.parsed_keybinds.keys())}"
        )
        with open(f"output/keybinds.json", "w") as f:
            json.dump(self.parsed_keybinds, f, indent=4)

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

    def parse_presets(self) -> None:
        """Parses all presets in the v5 file into new presets in v6,
        keeping the same data but with different keys.

        This is achieved by first checking whether any pairs in the data to
        parse still use the same key as the new data uses, if so that pair
        will just be added right away.

        Otherwise the `PARSE_MAPPING` dictionary is used to check if we can
        find any new versions of deprecated keys in the data to parse and once
        again add the value to that key.
        """
        all_presets = set(self.settings_data.keys()).difference(
            ["global_keys", "chaos", "discord", "altcycler"]
        )

        for preset in all_presets:
            self._parse_preset_settings(preset)
            self._parse_preset_skills(preset)

    def parse_altcycler(self) -> None:
        """Parses all characters in the altcycler settings on v5 into
        the new altcycler settings of v6"""
        schema = self.altcycler_schema["c1"]

        for c, v in self.altcycler_data.items():
            parsed = self.parsed_altcycler_data[c] = {}
            self._add_retained_keys(parsed, v, schema)
            self._add_parse_map_keys(parsed, v, schema)

    def _parse_preset_settings(self, preset: str) -> None:
        """Parses all preset settings in settings.json into the new v6 preset
        from an existing v5 preset.

        Parameters
        ----------
        preset :class:`preset`:
            The preset to be parsed
        """
        schema = self.settings_schema["SL"]
        to_parse = self.settings_data[preset]
        parsed = self.parsed_settings_data[preset] = {}

        self._add_retained_keys(parsed, to_parse, schema)
        self._add_parse_map_keys(parsed, to_parse, schema)

        lg.info(
            f"Parsing '{preset}' complete. "
            f"Total keys: {len(parsed)}, schema keys: {len(schema.keys())}. "
            f"Keys not parsed: {set(schema.keys()).difference(parsed.keys())}"
        )

    def _parse_preset_skills(self, preset: str) -> None:
        """Parses all preset settings in customrotation.json into the new v6 preset
        from an existing v5 preset.

        Parameters
        ----------
        preset :class:`preset`:
            The preset to be parsed
        """
        schema = self.skills_schema["SL"]
        to_parse = self.rotation_data[preset]
        self.parsed_rotation_data[preset] = {}

        rgbs = self.rgb_data[preset]

        for idx, (k, v) in enumerate(self.skills_schema["SL"].items(), start=1):
            parsed = self.parsed_rotation_data[preset][k] = {}
            if isinstance(v, dict):
                self._add_retained_keys(parsed, to_parse, v)
                if idx < 9:
                    parsed["rgb"] = rgbs[f"skill_{idx}"]
            else:
                try:
                    self.parsed_rotation_data[preset][k] = self.rotation_data[preset][k]
                except KeyError:
                    self.parsed_rotation_data[preset][k] = self.rotation_data[preset][
                        self.PARSE_MAPPING[k]
                    ]

        awk = self.parsed_rotation_data[preset]["awakening"]
        self._add_retained_keys(awk, self.settings_data[preset], schema["awakening"])

        lg.info(
            f"Parsing '{preset}' complete. "
            f"Total keys: {len(self.parsed_rotation_data[preset])}, schema keys: {len(schema.keys())}. "
            f"Keys not parsed: {set(schema.keys()).difference(self.parsed_rotation_data[preset].keys())}"
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

    def _ensure_preset_completeness(self) -> None:
        """Makes sure that all presets in the settings.json are also present
        in the customrotation.json.

        Raises
        ------
        `LookupError`
            When one or more presets are only present in either file
        """
        all_presets = set(self.settings_data.keys()).difference(
            ["global_keys", "chaos", "discord", "altcycler"]
        )
        rotation_diff = all_presets.difference(self.rotation_data.keys())
        skill_diff = all_presets.difference(self.rgb_data.keys())
        if rotation_diff or rotation_diff:
            raise LookupError(
                f"FATAL! Preset(s) {skill_diff or rotation_diff} is only present in one file!"
            )

    def _ensure_files_present(self) -> None:
        """Validates that all required files are present.

        Raises
        ------
        `FileNotFoundError`
            When an expected file could not be found
        """
        for f in self.SCHEMA_FILES:
            if not Path(f"schema/{f}.json").exists():
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

        with open("input/rgb.json") as f:
            self.rgb_data: dict[str, dict] = json.load(f)

    def _load_schema_files(self) -> None:
        """Loads all files to be parsed"""
        with open("schema/skills.json") as f:
            self.skills_schema: dict[str, dict] = json.load(f)

        with open("schema/settings.json") as f:
            self.settings_schema: dict[str, dict] = json.load(f)

        with open("schema/altcycler.json") as f:
            self.altcycler_schema: dict[str, dict] = json.load(f)

        with open("schema/keybinds.json") as f:
            self.keybinds_schema: dict[str, str] = json.load(f)

    def _create_parsed_data(self) -> None:
        """Creates empty dictionaries to be populated with parsed data"""
        self.parsed_rotation_data: dict[str, dict] = {}
        self.parsed_settings_data: dict[str, dict] = {}
        self.parsed_keybinds: dict[str, str] = {}
        self.parsed_altcycler_data: dict[str, dict] = {}

    def _save_parsed_files(self) -> None:
        """Saves all settings to configs"""
        destinations = {
            "settings": self.parsed_settings_data,
            "keybinds": self.parsed_keybinds,
            "altcycler": self.parsed_altcycler_data,
            "skills": self.parsed_rotation_data,
        }
        for file, var in destinations.items():
            with open(f"output/{file}.json", "w") as f:
                json.dump(var, f, indent=4)

    def _wipe_output_folder(self) -> None:
        filelist = [f for f in os.listdir("output") if f.endswith(".json")]
        for f in filelist:
            os.remove(os.path.join("output", f))
