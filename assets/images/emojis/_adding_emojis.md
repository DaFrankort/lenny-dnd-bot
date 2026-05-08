# Adding new Emojis to Lenny

Whenever you wish to add a new emoji to Lenny, you can follow these steps:
1. **Add the emoji to this folder**: 
    Place the new emoji in the `assets/images/emojis` directory. Name the file appropriately, as you will need to reference it later.
    A discord application emoji has the following limits (at the time of writing, 08/05/2026):
    - Maximum file size: 256KB
    - Supported formats: JPEG, PNG, GIF, WEBP, AVIF
    - Recommended dimensions: 128 x 128 pixels (but can be larger, up to 1024 x 1024 pixels)
    - Naming: Emoji names must be at least 2 characters long and can only contain alphanumeric characters and underscores

    **Naming conventions**
    Avoid using spaces in the filename; instead, use underscores. Lenny will automatically convert spaces to underscores when uploading and referencing the emoji. Additionally, all emoji-names are converted to lowercase when uploaded. For clarity, try to use only lowercase letters in the filename as well.
    (E.g. `Loot Goblin.webp` will be uploaded as `loot_goblin`).

    You can use sub-folders to organize emojis by category, in the code the folder name will be used as a prefix followed by an underscore (E.g. ``./class/artificer.webp`` -> ``class_artificer``)

2. **Add the emoji-name to the `AppEmoji` Enum in `./lenny/logic/app_emojis.py`**:
    Make sure to follow the naming convention of using lowercase letters and underscores instead of spaces.
    ```py

    class AppEmoji(Enum):
        ...
        # ./creature/Loot Goblin.webp
        LOOT_GOBLIN = "creature_loot_goblin"
    ```

    Afterwards, add a fallback emoji for your newly added emoji in the ``_fallback`` property of the AppEmoji class. This is important to ensure that if the custom emoji fails to load, a default emoji will be used instead.
    ```py
    @property
    def _fallback(self) -> str:
        fallback_map = {
            ...
            self.LOOT_GOBLIN: "👹",
        }
    ```

3. **Use the new emoji in the code**:
    You can now reference the new emoji in your code using the `AppEmoji` enum. For example:
    ```py
    from lenny.logic.app_emojis import AppEmoji

    # This will print the custom emoji or the fallback if it fails to load.
    print(AppEmoji.LOOT_GOBLIN.emoji)
    ```

4. **Syncing emojis**
    After adding the new emoji, you need to sync the emojis. This is done automatically whenever the bot launches.
    When working on a feature that implements new emojis, keep an eye out for any warnings in the console regarding unused emojis.
    The discord API does not allow for automatic application emoji deletion, so this needs to be do manually in the [Discord Developer Portal](https://discord.com/developers/applications).

    Each bot has ~2000 emoji slots, so generally speaking this should never back up. But preemptively cleaning up unused emojis is a good practice to avoid hitting the limit. (It is also really tedious having to remove a lot of emojis from the Developer Portal)