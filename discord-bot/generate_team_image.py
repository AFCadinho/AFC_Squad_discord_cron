import requests
from PIL import Image, ImageDraw, ImageFont
import re
import io
import os
from functools import lru_cache

# Load a nicer font (replace path with your local font)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SMALL = ImageFont.truetype(FONT_PATH, 30)
FONT_MEDIUM = ImageFont.truetype(FONT_PATH, 36)
FONT_LARGE = ImageFont.truetype(FONT_PATH, 44)


def get_required_team_width(team):
    max_width = 0
    for pokemon in team:
        pill_width = get_max_pill_width(pokemon, FONT_MEDIUM)
        sprite_width = int(0.22 * 1600)
        pill_to_stat_spacing = 100  # spacing between pills and stat columns
        stat_columns_width = 60 + 70 + 160  # IVs + labels + EVs + buffer before moves
        padding_margin = 60  # final right-side buffer

        max_move_width = 0
        for move in pokemon["moves"]:
            text_w = FONT_MEDIUM.getbbox(move)[2]
            max_move_width = max(max_move_width, text_w + 28 + 28)  # account for pill padding

        
        total = sprite_width + pill_width + pill_to_stat_spacing + stat_columns_width + max_move_width + padding_margin

        max_width = max(max_width, total)
    return max(max_width, 1600)  # ensure it's at least 1600



def normalize_item_name(item_name):
    normalized = item_name.lower()
    normalized = normalized.replace("é", "e")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized


@lru_cache(maxsize=None)
def fetch_item_icon(item_name):
    if not item_name:
        return None

    normalized = normalize_item_name(item_name)

    # Try PokéAPI first
    url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/{normalized}.png"
    try:
        response = requests.get(url)
        if response.ok:
            return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"Error fetching from PokeAPI: {e}")

    # If online fetch fails, try local fallback
    local_path = os.path.join("battle_items", f"{normalized}.png")
    if os.path.isfile(local_path):
        try:
            return Image.open(local_path).convert("RGBA")
        except Exception as e:
            print(f"Error loading local item icon for {item_name}: {e}")

    print(f"Item icon not found: {item_name}")
    return None



def get_team_max_pill_width(team):
    max_width = 0
    for pokemon in team:
        for label, value in [("Item", pokemon["item"]), ("Ability", pokemon["ability"]), ("Nature", pokemon["nature"])]:
            if value:
                bbox = FONT_MEDIUM.getbbox(f"{label}: {value}")
                text_width = bbox[2] - bbox[0]
                pill_width = text_width + 2 * 8 + 6
                max_width = max(max_width, pill_width)
    return max_width


def get_max_pill_width(pokemon, font):
    max_width = 0
    for label, value in [("Item", pokemon["item"]), ("Ability", pokemon["ability"]), ("Nature", pokemon["nature"])]:
        if value:
            bbox = font.getbbox(f"{label}: {value}")
            text_width = bbox[2] - bbox[0]
            max_width = max(max_width, text_width + 2 * 8 + 6)
    return max_width


def draw_pill(draw, xy, text, font, fill=(255, 255, 255), bg=(50, 50, 50, 200), border=None):
    padding_x, padding_y = 14, 8
    x, y = xy
    bbox = font.getbbox(text)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w, h = text_w + padding_x * 2, text_h + padding_y * 2
    radius = h // 2

    shape = [x, y, x + w, y + h]
    text_y = y + (h - text_h) // 2 - 2
    draw.rounded_rectangle(shape, radius, fill=bg, outline=border)
    draw.text((x + padding_x, text_y), text, font=font, fill=fill)
    return w + 6, h  # return both width and height


def fetch_pokemon_sprite(pokemon_name):
    normalized = re.sub(r"\s*\(.*\)$", "",
                        pokemon_name.lower()).replace(" ", "-")
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{normalized}")
    if response.ok:
        poke_id = response.json()["id"]
        sprite_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke_id}.png"
        sprite_response = requests.get(sprite_url)
        if sprite_response.ok:
            return Image.open(io.BytesIO(sprite_response.content)).convert("RGBA")
    return None


def parse_pokepaste(text):
    blocks = re.split(r'\n\s*\n', text.strip())
    team = []
    for block in blocks:
        lines = block.split('\n')
        name_item = lines.pop(0).split(' @ ')
        poke = {"name": name_item[0], "item": name_item[1] if len(name_item) > 1 else None,
                "ability": None, "nature": None, "evs": {}, "ivs": {}, "moves": []}
        for line in lines:
            if line.startswith("Ability: "):
                poke["ability"] = line[9:].strip()
            elif "Nature" in line:
                match = re.search(r"(\w+) Nature", line)
                if match:
                    poke["nature"] = match.group(1)
            elif line.startswith("EVs: "):
                for ev in line[5:].split("/"):
                    poke["evs"][ev.strip().split(" ")[1]] = int(
                        ev.strip().split(" ")[0])
            elif line.startswith("IVs: "):
                for iv in line[5:].split("/"):
                    poke["ivs"][iv.strip().split(" ")[1]] = int(
                        iv.strip().split(" ")[0])
            elif line.startswith("- "):
                poke["moves"].append(line[2:].strip())
        team.append(poke)
    return team


def draw_team_block(pokemon, pill_max_width, width=1600, height=360):
    block = Image.new("RGBA", (width, height), (20, 20, 30, 255))
    draw = ImageDraw.Draw(block)

    sprite = fetch_pokemon_sprite(pokemon["name"])
    if sprite:
        max_sprite_width = int(width * 0.22)
        max_sprite_height = int(height * 0.75)
        sprite.thumbnail((max_sprite_width, max_sprite_height), Image.Resampling.LANCZOS)
        sprite_y = (height - sprite.height) // 2
        block.paste(sprite, (int(width * 0.02), sprite_y), sprite)



    name_x = int(width * 0.22)
    name_y = int(height * 0.18)
    name_text = pokemon["name"]
    name_bbox = FONT_LARGE.getbbox(name_text)
    name_w = name_bbox[2] - name_bbox[0]

    # Draw Pokémon name
    draw.text((name_x, name_y), name_text, font=FONT_LARGE, fill="white")

    # Draw item icon next to Pokémon name
    icon = fetch_item_icon(pokemon["item"])
    if icon:
        icon_size = int(FONT_LARGE.size * 1.3)  # e.g. 30% bigger than text height
        icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        icon_x = name_x + name_w + FONT_LARGE.size // 3
        icon_y = name_y + (FONT_LARGE.size // 2) - (icon_size // 2)
        block.paste(icon, (int(icon_x), int(icon_y)), icon)

    pill_start_x = name_x
    pill_y = int(height * 0.34)

    for label, value, color in [("Item", pokemon["item"], (200, 180, 255)),
                                ("Ability", pokemon["ability"], (180, 255, 200)),
                                ("Nature", pokemon["nature"], (255, 230, 150))]:
        if value:
            clean_value = re.sub(r'[\r\n\t]+', '', value).strip()
            pill_text = f"{label}: {clean_value}"
            _, pill_height = draw_pill(draw, (pill_start_x, pill_y), pill_text,
                                    FONT_MEDIUM, bg=color + (200,))
            pill_y += pill_height + 10  # dynamic spacing like moves



    iv_x = pill_start_x + pill_max_width + 100
    stat_x = iv_x + 60
    ev_x = stat_x + 70
    move_x = ev_x + 160

    stat_y_start = int(height * 0.25)
    draw.text((iv_x, stat_y_start - 30), "IVs", font=FONT_SMALL, fill="white")
    draw.text((ev_x, stat_y_start - 30), "EVs", font=FONT_SMALL, fill="white")

    stats_labels = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
    for i, stat in enumerate(stats_labels):
        y = stat_y_start + i * int(height * 0.10)
        iv_val = pokemon['ivs'].get(stat, 31)
        ev_val = pokemon['evs'].get(stat, 0)
        draw.text((iv_x, y), f"{iv_val:<2}", font=FONT_SMALL, fill="#fff")
        draw.text((stat_x, y), stat, font=FONT_SMALL, fill="#ddd")
        draw.text((ev_x, y), f"{ev_val:<3}", font=FONT_SMALL,
                  fill="#0f0" if ev_val else "#555")

    move_y = int(height * 0.21)
    for move in pokemon["moves"]:
        _, pill_height = draw_pill(draw, (move_x, move_y), move, FONT_MEDIUM,
                                fill="#fff", bg=(255, 100, 0, 180))
        move_y += pill_height + 10  # consistent spacing between pills


    draw.line([(0, height - 1), (width, height - 1)], fill=(255, 255, 255, 30), width=1)

    return block


def fetch_team(url):
    raw_url = url if url.endswith("/raw") else f"{url.rstrip('/')}/raw"
    return parse_pokepaste(requests.get(raw_url).text)


def generate_team_image(url, filename="team.png"):
    team = fetch_team(url)
    pill_max_width = get_team_max_pill_width(team)
    dynamic_width = get_required_team_width(team)
    blocks = [draw_team_block(p, pill_max_width, width=int(dynamic_width), height=360) for p in team]

    padding = 30
    block_width = blocks[0].width
    block_height = blocks[0].height
    img_height = len(blocks) * (block_height + padding) + padding

    img = Image.new("RGBA", (block_width, img_height), (10, 10, 15, 255))
    y_offset = padding
    for block in blocks:
        img.paste(block, (0, y_offset))
        y_offset += block.height + padding

    img.save(filename)
    print(f"Saved team image to {filename}")


if __name__ == "__main__":
    pokepaste_url = "https://pokepast.es/065fe49b30f18999"
    generate_team_image(pokepaste_url)
