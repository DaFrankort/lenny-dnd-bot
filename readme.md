# DnD Discord Bot

A Discord bot for Dungeons & Dragons players which aims to provide commands using modern Discord features.

Powered by [5e.tools](https://5e.tools/) for up-to-date 5e data.

## Features

- **Dice Roll Commands**: Roll dice with custom parameters (e.g., `/roll 2d6`, `/advantage 1d20+1` or `/disadvantage 3d20+4`).
- **D&D Spell Lookup**: Look up spells and get detailed information about them directly in Discord using `/spell`.
- **Customizable Color Embeds**: Customize the colors of your dice roll embeds for better visual appeal and easy identification, auto-generated if not specified.
- **Character Stat Rolling**: Automatically roll and generate character stats for D&D characters.
- **Initiative tracking**: Let players roll initiative and roll initiative for creatures and track it easily.

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

pip install -r requirements.txt
```

### 3. Set Up the Bot

Create a new file named `.env` in the project root and add your bot token:

```plaintext
DISCORD_TOKEN=your-bot-token-here
```

If you don't have a bot token, you can create one by following [Discord's bot creation guide](https://discordpy.readthedocs.io/en/stable/discord.html).

### 4. Run the Bot

To start the bot, simply run the following command:

```bash
py -3 ./src/main.py
```

Or alternatively run the provided `run.bat` file.
The bot should now be running on your Discord server.

## Usage

Once the bot is added to your server, you can use the following commands:

### Dice Rolls

- `/roll <dice>` – Roll a custom dice, e.g., `/roll 2d6` or `/roll 1d20+2`.
- `/advantage <dice>` – Rolls twice, highlights the highest result, e.g., `/advantage  2d6` or `/advantage 1d20+2`.
- `/disadvantage <dice>` – Rolls twice, highlights the lowest result, e.g., `/disadvantage 2d6` or `/disadvantage 1d20+2`.
- `/d20` - Rolls a basic 1d20 without any modifiers.

### D&D Data lookup

- `/spell <spell-name>` – Look up information about a D&D spell (e.g. Fireball).
- `/item <item-name>` - Look up information about a D&D item (e.g. Dagger).
- `/condition <condition-name>` - Look up information about a D&D condition (e.g. Blinded).
- `/search <query>` - Look for many related results regarding spells, items or conditions, example: `/search fire` would return any data with 'fire' in the name.

### Character Stat Roll

- `/stats` – Automatically roll stats for a new character's skills, using the 4d6 drop lowest method.

### Customize embed colors for users

- `/color <hex-value>` - Provide a hex value for a color and anytime you roll dice it will label your rolls with that color.
- `/color` - Using the command without a hex-value will clear the user's set color.
- If the user has no color set, a random one will be generated based on the user's display-name.

### Track Initiative

- `/initiative <modifier> <target>` - Roll for initiative, all rolls are stored per server. You can provide a 'target' to roll for NPC's / Creatures, rolls for user by default.
- `/bulkinitiative <modifier> <name> <amount> <shared>` - Adds creature initiatives in bulk, making it easy for a DM to add a group of creatures at once. These are numbered automatically for easy tracking.
- `/setinitiative <value> <name>` - Set an initiative to a specific value, handy to rectify mistakes or if you want precise control over certain initiatives.
- `/swapinitiative <target a> <target b>` - Swap initiative between two users or creatures, handy for users with the Alert feat.
- `/removeinitiative <target>` - Remove a single user or creature from the initiative tracker, removes user's initiative by default.
- `/showinitiative` - Shows an embed with all the initiatives, used to track the order & who's turn it is.
- `/clearinitiative` - Clears all stored initiatives in the server, used after a battle.

