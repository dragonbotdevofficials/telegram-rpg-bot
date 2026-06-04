import json
import random
import requests
import asyncio
import time
import os

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command

# =========================
# BOT TOKEN
# =========================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

# =========================
# OLLAMA
# =========================
OLLAMA_URL = "http://localhost:11434/api/generate"

# =========================
# BOT SETUP
# =========================
bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# SAVE FILE
# =========================
SAVE_FILE = "player.json"
PLAYERS_FILE = "players.json"
# =========================
# PLAYER DATA
# =========================
player = {
    "health": 100,
    "xp": 0,
    "level": 1,
    "coins": 100,
    "potions": 3,
    "inventory": [],
    "equipped_weapon": "",
    "attack_bonus": 0,
    "last_daily": 0,
}


# =========================
# LOAD PLAYER
# =========================
def load_player():
    global player

    try:
        with open(SAVE_FILE, "r") as file:
            loaded_data = json.load(file)

            # SAFE UPDATE
            player.update(loaded_data)

    except:
        save_player()


# =========================
# SAVE PLAYER
# =========================
def save_player():
    print("SAVING PLAYER DATA...")
    print(player)
    with open(SAVE_FILE, "w") as file:
        json.dump(player, file, indent=4)


# =========================
# MULTI USER SYSTEM
# =========================


def load_players():
    try:
        with open(PLAYERS_FILE, "r") as file:
            return json.load(file)
    except:
        return {}


def save_players(players):
    with open(PLAYERS_FILE, "w") as file:
        json.dump(players, file, indent=4)


def get_player(user_id):
    players = load_players()

    user_id = str(user_id)

    if user_id not in players:
        players[user_id] = {
            "health": 100,
            "xp": 0,
            "level": 1,
            "coins": 100,
            "potions": 3,
            "inventory": [],
            "equipped_weapon": "",
            "attack_bonus": 0,
            "last_daily": 0,
        }

        save_players(players)

    return players[user_id]


# =========================
# LEVEL SYSTEM
# =========================
def check_level_up():
    required_xp = player["level"] * 100

    if player["xp"] >= required_xp:
        player["level"] += 1

        player["health"] = 100


# LOAD PLAYER
load_player()

with open("backup_player_data.json", "w") as f:
    json.dump(player, f, indent=4)

print("BACKUP CREATED")
# =========================
# MONSTERS
# =========================
monsters = ["Goblin", "Skeleton", "Zombie", "Dark Wolf", "Orc"]

enemy_health = {}
boss_health = {}


# =========================
# START
# =========================
@dp.message(Command("start"))
async def start(message: Message):
    text = (
        "🎮 WELCOME TO RPG BOT\n\n"
        "/battle - Fight monsters\n"
        "/boss - Fight boss\n"
        "/quest - AI quest\n"
        "/stats - Player stats\n"
        "/inventory - Inventory\n"
        "/equip - Equip weapon\n"
        "/shop - RPG shop\n"
        "/heal - Use potion\n"
        "/daily - Daily reward\n"
        "/leaderboard - Top players"
    )

    await message.answer(text)


# =========================
# STATS
# =========================
@dp.message(Command("stats"))
async def stats(message: Message):
    if message.from_user.id != 8981858811:
        await message.answer("❌ Access denied.")
        return
    player = get_player(message.from_user.id)
    text = (
        f"🛠️ ADMIN STATS\n\n"
        f"🏆 Level: {player['level']}\n"
        f"❤️ Health: {player['health']}\n"
        f"⭐ XP: {player['xp']}\n"
        f"🪙 Coins: {player['coins']}\n"
        f"🧪 Potions: {player['potions']}\n"
        f"⚔️ Weapon: {player['equipped_weapon']}\n"
        f"💥 Attack Bonus: {player['attack_bonus']}"
    )

    await message.answer(text)


# =========================
# QUEST
# =========================
@dp.message(Command("quest"))
async def quest(message: Message):
    player = get_player(message.from_user.id)

    prompt = "Generate a short fantasy RPG quest with rewards."

    try:
        response = requests.post(
            OLLAMA_URL, json={"model": "qwen3:1.7b", "prompt": prompt, "stream": False}
        )

        result = response.json()

        quest_text = result["response"]

    except:
        quest_text = "🗡️ A dark knight searches for the lost crown."

    xp_reward = random.randint(10, 30)
    coin_reward = random.randint(20, 60)

    player["xp"] += xp_reward
    player["coins"] += coin_reward

    players = load_players()
    players[str(message.from_user.id)] = player
    save_players(players)

    text = (
        f"📜 QUEST GENERATED\n\n"
        f"{quest_text}\n\n"
        f"🎁 Rewards:\n"
        f"⭐ XP: +{xp_reward}\n"
        f"🪙 Coins: +{coin_reward}"
    )

    await message.answer(text)


# =========================
# DAILY REWARD
# =========================
@dp.message(Command("daily"))
async def daily(message: Message):
    player = get_player(message.from_user.id)

    current_time = time.time()

    cooldown = 86400

    last_claim = player["last_daily"]

    if current_time - last_claim < cooldown:
        remaining = int(cooldown - (current_time - last_claim))

        hours = remaining // 3600

        await message.answer(
            f"⏳ Daily already claimed!\n\n🕒 Try again in {hours} hours."
        )

        return

    coin_reward = random.randint(100, 250)

    player["coins"] += coin_reward

    player["potions"] += 1

    player["last_daily"] = current_time

    players = load_players()
    players[str(message.from_user.id)] = player
    save_players(players)

    text = f"🎁 DAILY REWARD CLAIMED!\n\n🪙 Coins: +{coin_reward}\n🧪 Potions: +1"

    await message.answer(text)


# =========================
# HEAL
# =========================
@dp.message(Command("heal"))
async def heal(message: Message):
    player = get_player(message.from_user.id)

    if player["potions"] <= 0:
        await message.answer("❌ No potions left!")
        return

    heal_amount = random.randint(20, 40)

    player["health"] += heal_amount

    if player["health"] > 100:
        player["health"] = 100

    player["potions"] -= 1

    players = load_players()
    players[str(message.from_user.id)] = player
    save_players(players)

    text = (
        f"🧪 Potion Used!\n\n"
        f"❤️ Healed: +{heal_amount}\n"
        f"❤️ Current Health: {player['health']}\n\n"
        f"🧪 Potions Left: {player['potions']}"
    )

    await message.answer(text)


# =========================
# INVENTORY
# =========================
@dp.message(Command("inventory"))
async def inventory(message: Message):
    player = get_player(message.from_user.id)

    items = "\n".join(player["inventory"])

    if items == "":
        items = "Empty"

    text = f"🎒 INVENTORY\n\n{items}\n\n⚔️ Equipped Weapon: {player['equipped_weapon']}"

    await message.answer(text)


# =========================
# EQUIP
# =========================
@dp.message(Command("equip"))
async def equip(message: Message):
    player = get_player(message.from_user.id)

    weapon_found = None
    weapon_bonus = 0

    for item in player["inventory"]:
        if "Sword" in item:
            weapon_found = item

            if "Dragon Slayer" in item:
                weapon_bonus = 15

            elif "Iron" in item:
                weapon_bonus = 5

            break

    if weapon_found is None:
        await message.answer("❌ No sword found!")
        return

    player["equipped_weapon"] = weapon_found
    player["attack_bonus"] = weapon_bonus

    players = load_players()
    players[str(message.from_user.id)] = player
    save_players(players)

    text = (
        f"⚔️ Weapon Equipped!\n\n🔥 {weapon_found}\n\n💥 Attack Bonus: +{weapon_bonus}"
    )

    await message.answer(text)


# =========================
# SHOP
# =========================
@dp.message(Command("shop"))
async def shop(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧪 Buy Potion (50 Coins)", callback_data="buy_potion"
                )
            ]
        ]
    )

    text = "🏪 RPG SHOP\n\n🧪 Potion = 50 Coins"

    await message.answer(text, reply_markup=keyboard)


# =========================
# BUY POTION
# =========================


@dp.callback_query(lambda c: c.data == "buy_potion")
async def buy_potion(callback: CallbackQuery):
    player = get_player(callback.from_user.id)

    if player["coins"] < 50:
        await callback.message.edit_text("❌ Not enough coins!")

        return

    player["coins"] -= 50

    player["potions"] += 1

    players = load_players()
    players[str(callback.from_user.id)] = player
    save_players(players)

    text = (
        f"🧪 Potion Purchased!\n\n"
        f"🪙 Coins Left: {player['coins']}\n"
        f"🧪 Potions: {player['potions']}"
    )

    await callback.message.edit_text(text)


# =========================
# BATTLE
# =========================
@dp.message(Command("battle"))
async def battle(message: Message):
    user_id = str(message.from_user.id)

    monster = random.choice(monsters)

    enemy_health[user_id] = {"name": monster, "hp": random.randint(50, 100)}

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ Attack", callback_data="attack")],
            [InlineKeyboardButton(text="🛡️ Defend", callback_data="defend")],
            [InlineKeyboardButton(text="🏃 Run", callback_data="run")],
        ]
    )

    text = f"👹 {monster} appeared!\n\n❤️ Enemy HP: {enemy_health[user_id]['hp']}"

    await message.answer(text, reply_markup=keyboard)


# =========================
# ATTACK
# =========================
@dp.callback_query(lambda c: c.data == "attack")
async def attack(callback: CallbackQuery):
    user_id = str(callback.from_user.id)

    player = get_player(callback.from_user.id)

    if user_id not in enemy_health:
        await callback.answer("No active battle!")
        return

    monster = enemy_health[user_id]["name"]

    player_damage = random.randint(10, 25) + player["attack_bonus"]

    critical_text = ""
    bonus_xp = 0

    if random.randint(1, 100) > 80:
        player_damage *= 2

        bonus_xp = random.randint(5, 15)

        player["xp"] += bonus_xp

        critical_text = f"\n💥 ULTRA CRITICAL HIT!\n⭐ Bonus XP: +{bonus_xp}"

    enemy_health[user_id]["hp"] -= player_damage

    if enemy_health[user_id]["hp"] <= 0:
        xp_reward = random.randint(20, 50)
        coin_reward = random.randint(10, 40)

        player["xp"] += xp_reward
        player["coins"] += coin_reward

        loot = ""

        loot_items = ["🗡️ Iron Sword", "🛡️ Wooden Shield", "💎 Magic Stone"]

        if random.randint(1, 100) > 70:
            found_item = random.choice(loot_items)

            player["inventory"].append(found_item)

            loot = f"\n🎁 Loot Found: {found_item}"

        players = load_players()
        players[user_id] = player
        save_players(players)

        del enemy_health[user_id]

        text = (
            f"⚔️ You defeated the {monster}!\n\n"
            f"⭐ XP Earned: +{xp_reward}\n"
            f"🪙 Coins Earned: +{coin_reward}"
            f"{critical_text}"
            f"{loot}"
        )

        await callback.message.edit_text(text)

    else:
        enemy_attack = random.randint(5, 15)

        player["health"] -= enemy_attack

        players = load_players()
        players[user_id] = player
        save_players(players)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚔️ Attack", callback_data="attack")],
                [InlineKeyboardButton(text="🛡️ Defend", callback_data="defend")],
                [InlineKeyboardButton(text="🏃 Run", callback_data="run")],
            ]
        )

        text = (
            f"⚔️ You attacked the {monster}!\n\n"
            f"💥 Damage Dealt: {player_damage}"
            f"{critical_text}\n\n"
            f"👹 Enemy HP Left: "
            f"{enemy_health[user_id]['hp']}\n\n"
            f"❤️ Enemy Attack: -{enemy_attack}\n"
            f"❤️ Your Health: {player['health']}"
        )

        await callback.message.edit_text(text, reply_markup=keyboard)


# =========================
# DEFEND
# =========================
@dp.callback_query(lambda c: c.data == "defend")
async def defend(callback: CallbackQuery):
    user_id = str(callback.from_user.id)

    player = get_player(callback.from_user.id)

    if user_id not in enemy_health:
        await callback.answer("No active battle!")
        return

    monster = enemy_health[user_id]["name"]

    reduced_damage = random.randint(1, 5)

    counter_text = ""

    player["health"] -= reduced_damage

    if random.randint(1, 100) > 75:
        counter_damage = random.randint(5, 15)

        enemy_health[user_id]["hp"] -= counter_damage

        counter_text = f"\n⚔️ Counter Attack: {counter_damage} Damage!"

    players = load_players()
    players[user_id] = player
    save_players(players)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ Attack", callback_data="attack")],
            [InlineKeyboardButton(text="🛡️ Defend", callback_data="defend")],
            [InlineKeyboardButton(text="🏃 Run", callback_data="run")],
        ]
    )

    text = (
        f"🛡️ DEFENSE SUCCESSFUL!\n\n"
        f"❤️ Reduced Damage: -{reduced_damage}\n"
        f"👹 Enemy HP: "
        f"{enemy_health[user_id]['hp']}\n"
        f"❤️ Your Health: "
        f"{player['health']}"
        f"{counter_text}"
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# =========================
# BOSS
# =========================
@dp.message(Command("boss"))
async def boss(message: Message):
    boss_name = "🐉 Dragon King"

    boss_health[boss_name] = 300

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ Attack Boss", callback_data=f"bossattack_{boss_name}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛡️ Defend", callback_data=f"bossdefend_{boss_name}"
                )
            ],
            [InlineKeyboardButton(text="🏃 Escape", callback_data="run")],
        ]
    )

    text = f"{boss_name} appeared!\n\n❤️ Boss HP: {boss_health[boss_name]}"

    await message.answer(text, reply_markup=keyboard)


# =========================
# BOSS ATTACK
# =========================
@dp.callback_query(lambda c: c.data.startswith("bossattack"))
async def boss_attack(callback: CallbackQuery):
    boss_name = callback.data.split("_", 1)[1]

    player_damage = random.randint(15, 35) + player["attack_bonus"]

    critical_text = ""

    if random.randint(1, 100) > 85:
        player_damage *= 2

        critical_text = "\n💥 CRITICAL HIT!"

    boss_health[boss_name] -= player_damage

    if boss_health[boss_name] <= 0:
        xp_reward = random.randint(100, 200)

        coin_reward = random.randint(100, 300)

        player["xp"] += xp_reward

        player["coins"] += coin_reward

        rare_loot = ["🔥 Dragon Slayer Sword", "👑 King Armor", "💎 Legendary Crystal"]

        loot = random.choice(rare_loot)

        player["inventory"].append(loot)

        check_level_up()

        save_player()

        text = (
            f"🏆 BOSS DEFEATED!\n\n"
            f"🐉 {boss_name} destroyed!\n\n"
            f"⭐ XP Earned: +{xp_reward}\n"
            f"🪙 Coins Earned: +{coin_reward}\n"
            f"🎁 Rare Loot: {loot}"
            f"{critical_text}"
        )

        await callback.message.edit_text(text)

    else:
        boss_damage = random.randint(10, 25)

        player["health"] -= boss_damage

        save_player()

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⚔️ Attack Boss", callback_data=f"bossattack_{boss_name}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛡️ Defend", callback_data=f"bossdefend_{boss_name}"
                    )
                ],
                [InlineKeyboardButton(text="🏃 Escape", callback_data="run")],
            ]
        )

        text = (
            f"⚔️ You attacked {boss_name}!\n\n"
            f"💥 Damage Dealt: {player_damage}"
            f"{critical_text}\n\n"
            f"❤️ Boss HP Left: "
            f"{boss_health[boss_name]}\n\n"
            f"🔥 Boss Attack: -{boss_damage}\n"
            f"❤️ Your Health: {player['health']}"
        )

        await callback.message.edit_text(text, reply_markup=keyboard)


# =========================
# BOSS DEFEND
# =========================
@dp.callback_query(lambda c: c.data.startswith("bossdefend"))
async def boss_defend(callback: CallbackQuery):
    boss_name = callback.data.split("_", 1)[1]

    reduced_damage = random.randint(3, 8)

    player["health"] -= reduced_damage

    save_player()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ Attack Boss", callback_data=f"bossattack_{boss_name}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛡️ Defend", callback_data=f"bossdefend_{boss_name}"
                )
            ],
            [InlineKeyboardButton(text="🏃 Escape", callback_data="run")],
        ]
    )

    text = (
        f"🛡️ You defended against "
        f"{boss_name}!\n\n"
        f"❤️ Reduced Damage: "
        f"-{reduced_damage}\n"
        f"❤️ Boss HP: "
        f"{boss_health[boss_name]}\n"
        f"❤️ Your Health: "
        f"{player['health']}"
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# =========================
# LEADERBOARD
# =========================
@dp.message(Command("leaderboard"))
async def leaderboard(message: Message):
    fake_players = [
        {"name": "Shadow Knight", "level": 10, "xp": 900},
        {"name": "DragonSlayer", "level": 8, "xp": 700},
        {"name": "Night Hunter", "level": 6, "xp": 500},
    ]

    text = (
        f"🏆 RPG LEADERBOARD\n\n"
        f"🥇 You — Level {player['level']} "
        f"— {player['xp']} XP\n\n"
    )

    medals = ["🥈", "🥉", "🏅"]

    for i, fake_player in enumerate(fake_players):
        text += (
            f"{medals[i]} "
            f"{fake_player['name']} "
            f"— Level {fake_player['level']} "
            f"— {fake_player['xp']} XP\n"
        )

    await message.answer(text)


# =========================
# MAIN
# =========================
async def main():
    print("TEST MESSAGE 12345")
    print("🎮 RPG GAME RUNNING...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
