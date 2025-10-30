# DnD Discord Bot

A Discord bot for Dungeons & Dragons players which aims to provide commands using modern Discord features.

Powered by [5e.tools](https://5e.tools/) for up-to-date 5e data.

## Features

- **Dice Roll Commands**: Easily roll dice with flexible expressions, such as `2d6`, `1d20+6`, or `1d8+4+2d6`.
- **D&D Data Lookup**: Look up D&D data and get detailed information about them directly in Discord, powered by [5e.tools](https://5e.tools/).
- **Customizable Color Embeds**: Customize the colors of your dice roll embeds for better visual appeal and easy identification, auto-generated if not specified.
- **Character Stat Rolling**: Automatically roll and generate D&D character stats.
- **Voice Chat Sound Effects**: The bot can join voice channels to play sound effects for your rolls, including special sounds for natural 1s and 20s, as well as effects for attacks, damage, and fire.
- **Token-Image Generation** - Generate a 5etools-style token from an image or image-url for your characters or custom creatures.
- **Initiative Tracking** - Track initiatives for combat easily, with easy-to-use buttons for players and dungeon masters.

## Installation

To get the bot running on your own Discord server, follow these steps:

### 1. Clone the Repository

Clone the repository using the following command:

```bash
git clone --recursive https://github.com/DaFrankort/lenny-dnd-bot.git
```

### 2. Install Dependencies

Once cloned, navigate to the repository directory and install the required dependencies:

```bash
cd lenny-dnd-bot

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt --force
```

### 3. Setup .env File

Copy `.env.example` and rename it to `.env`, make sure it's in the project root folder.
Add your discord-bot token and optionally add a guild ID:

```plaintext
DISCORD_BOT_TOKEN="your-token-here"
GUILD_ID=0
```

- If you don't have a bot token, you can create one by following [Discord's bot creation guide](https://discordpy.readthedocs.io/en/stable/discord.html).
- To get a guild ID, enable [developer mode](https://help.mee6.xyz/support/solutions/articles/101000482629-how-to-enable-developer-mode) on discord.
  Afterwards you can right click on your server of choice and select `Copy Server ID`

### 4. (Optional) Install FFMPEG

_If you don't wish for the bot to play immersive sound effects on dice rolls and initiative rolls, you can skip this step._

For voice chat capabilities [FFMPEG](https://ffmpeg.org/download.html) is required.
You can follow [this tutorial](https://www.hostinger.com/tutorials/how-to-install-ffmpeg#How_to_install_FFmpeg_on_Windows) for help with installing it.

### 5. Run the Bot

To start the bot, simply run the following command:

```bash
python ./src/main.py
```

You can add the following arguments if you wish:

- `--verbose, --no-verbose` - Run with or without debug-logging.
- `--voice, --no-voice` - Run with or without voice-chat functionalities.

The bot should now be online, don't forget to invite it to your servers!

## Usage

Once the bot is added to your server, the commands below are available. When setting up the bot, the config commands should be used first to set the game master roles.

### Config

Configure the current state of the server.

- `/config permissions` - Set the roles which are allowed to configure the bot further. Only the server admin is allowed to use this command.
- `/config sources` - Enable or disable which sources will be used during the `/search` commands. Only users with the permission roles can change the sources.

### Dice Rolls

Roll D&D dice using dice-expressions (e.g. `2d6` / `1d20+2`).

- `/roll <dice-expression> [reason]` – Roll a single dice expression, optionally specify a reason for the roll (e.g. Acrobatics)
- `/advantage <dice-expression> [reason]` – Rolls twice, highlights the highest result.
- `/disadvantage <dice-expression> [reason]` – Rolls twice, highlights the lowest result.
- `/d20` - Rolls a basic 1d20 without any modifiers.
- `/distribution <expression> [advantage] [min-to-beat]` - Creates a graph showing likeliness of your dice expression's roll results.

### D&D Data lookup

Look up various D&D data from [5e.tools](https://5e.tools/).

- `/search spell <spell-name>` – Look up information about a D&D spell (e.g. Fireball).
- `/search item <item-name>` - Look up information about a D&D item (e.g. Dagger).
- `/search condition <condition-name>` - Look up information about a D&D condition (e.g. Blinded).
- `/search creature <creature-name>` – Look up information about a D&D creature (e.g. Orc).
- `/search class <class-name>` – Look up information about a D&D Class (e.g. Wizard).
- `/search rule <rule-name>` – Look up information about a D&D rule (e.g. Saving Throw).
- `/search action <action-name>` – Look up information about a D&D action (e.g. Dash).
- `/search feat <feat-name>` – Look up information about a D&D feat (e.g. Savage Attacker).
- `/search language <language-name>` - Look up a D&D language (e.g. Common).
- `/search background <background-name>` - Look up a D&D Background (e.g. Soldier).
- `/search table <table-name>` - Look up a D&D Table (e.g. Wild Magic Surge).
- `/search species <species-name>` - Look up a D&D Species (e.g. Human).
- `/search all <query>` - Look for many related results regarding D&D data. Example: `/search fire` would return any data with 'fire' in the name.

### Character Tools

- `/stats roll` – Automatically roll stats for a new character's skills, using the 4d6 drop lowest method. Also generates a radar-graph to visualize the stats.
- `/stats visualize <str> <dex> <con> <int> <wis> <cha>` – Visualizes character stats in a radar-graph.
- `/namegen [race] [gender]` - Generate a random name, race and/or gender can be specified but will default to random.
- `/charactergen` - Generates a character with name, class, species, background and stats. Ensures that the build that is generated is somewhat optimal for your class; automatically selecting fitting backgrounds and assigning stats optimally.

### Token-Image Generation

Create 5e.tools-style token images quickly, [like this example](https://5e.tools/img/bestiary/tokens/MM/Goblin.webp).
Optionally adjust the frame's color with `hue-shift` (default: gold), control image alignment using `h_alignment` and `v_alignment` (default: center), and `variants` for generating up to 10 numbered variants of your tokens.

- `/tokengen file <image-attachment> [hue-shift] [h_alignment] [v_alignment] [variants]` - Generate a token from an image attachment.
- `/tokengen url <image-url> [hue-shift] [h_alignment] [v_alignment] [variants]` - Generate a token from an image URL.

### Discord utilities

- `/plansession <in_weeks> [poll_duration]` - Quickly generates a poll where players can vote for days they're available within a given week.
- `/playsound` - Allows users to play a sound effect from a file through the bot, allowing for more atmospheric role-play!
- `/timestamp relative [seconds] [minutes] [hours] [days] [weeks]` - Generates a timestamp relative from when you used this command.
- `/timestamp date <time> <timezone> [date]` - Generates all possible timestamps for a specific date & time. Date defaults to the current day.

#### User Colors
Commands that resemble user-actions are highlighted with colors that are unique per user. This makes it easy to discern different user's actions.
By default the user's color is automatically generated based on their display name. Users can adjust their colors using following commands:

- `/color set hex <hex_color>` - Set your color using a hexadecimal color value.
- `/color set rgb <r> <g> <b>` - Set your color using a RGB value.
- `/color clear` - Clears your set color and enforces use of an auto-generated color.
- `/color show` - Shows the color you've set to everyone.

### Track Initiative

Command to help track initiatives for combat. Names are enforced to be unique and will overwrite each other if specified twice.

- `/initiative` - Summons an embed with buttons to track initiative. Available buttons are as follows:
  - `Roll` - Rolls initiative for a user, can also roll for a creature if a name is specified.
  - `Set` - Set an initiative to a specific value, handy to rectify mistakes or if you want precise control over certain initiatives.
  - `Delete Roll` - Remove a single user or creature from the initiative tracker. Removes user's initiative by default.
  - `Bulk` - Adds creature initiatives in bulk, making it easy for a DM to add a group of creatures at once. These are numbered automatically for easy tracking.
  - `Lock` - Disables all the buttons, to avoid accidental adjustments.
  - `Clear Rolls` - Clears all stored initiatives in the server, used after a battle.
