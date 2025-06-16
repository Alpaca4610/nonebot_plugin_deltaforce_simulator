import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from nonebot import get_plugin_config
from .config import Config
import textwrap
import json
import random
import httpx
# import nonebot
from io import BytesIO


# driver = get_driver()
# config = nonebot.get_driver().config
plugin_config = get_plugin_config(Config)


try:
    # 从环境变量获取配置路径
    custom_config_path = plugin_config.deltaforce_sim_config
    if custom_config_path and os.path.isfile(custom_config_path):
        # 尝试从自定义路径加载
        with open(custom_config_path, 'r', encoding='utf-8') as f:
            CONTAINER_CONFIGS = json.load(f)
    else:
        # 使用默认路径
        default_path = Path(__file__).parent / 'container_configs.json'
        with open(default_path, 'r', encoding='utf-8') as f:
            CONTAINER_CONFIGS = json.load(f)
except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
    default_path = Path(__file__).parent / 'container_configs.json'
    with open(default_path, 'r', encoding='utf-8') as f:
        CONTAINER_CONFIGS = json.load(f)


def load_font(font_size=24):
    """统一加载字体文件，支持错误回退机制"""
    try:
        font_path = Path(__file__).parent / "resource" / "Yahei.ttf"
        return ImageFont.truetype(str(font_path), font_size)
    except IOError as e:
        print(f"自定义字体加载失败: {e}, 使用回退字体")
        try:
            # 尝试加载系统默认支持中文的字体
            return ImageFont.truetype("simhei.ttf", font_size)  # 黑体
        except:
            # 最终回退到PIL默认字体
            print("系统字体加载失败，使用PIL默认字体")
            return ImageFont.load_default()


def load_all_items():
    """加载所有物品数据文件"""
    item_files = [
        'armor.json',    # 护甲
        'bag.json',      # 背包
        'chest.json',    # 胸挂
        'collection.json',  # 收集品
        'helmet.json'    # 头盔
    ]
    
    all_items = []
    for file_name in item_files:
        try:
            with open(Path(__file__).parent / "resource" / file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 为每个物品添加类型标识
                for item in data:
                    # 从文件名提取类型（去掉.json后缀）
                    item_type = file_name.replace('.json', '')
                    item['item_type'] = item_type
                all_items.extend(data)
                # print(f"成功加载文件: {file_name}, 物品数量: {len(data)}")
        except Exception as e:
            print(f"加载文件 {file_name} 出错: {str(e)}")
    
    #print(f"总共加载物品数量: {len(all_items)}")
    return all_items

# 根据 grade 获取背景颜色
def get_background_color(grade):
    color_map = {
        1: (206, 213, 213, 255),
        2: (56, 139, 35, 255),  
        3: (110, 137, 203, 255), 
        4: (151, 99, 197, 255), 
        5: (224, 170, 88, 255), 
        6: (191, 83, 78, 255)
    }
    return color_map.get(grade, "#FFFFFF")


async def process_image(url, grade, object_name):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
    img = Image.open(BytesIO(response.content)).convert("RGBA")
    
    # 创建一个带有指定背景颜色的新图像
    background_color = get_background_color(grade)
    background = Image.new('RGBA', (img.width, img.height), background_color)
    
    # 将原始图像与背景图像合并
    background.paste(img, (0, 0), img)
    
    # 在图片左上角加入 objectName
    draw = ImageDraw.Draw(background)
    font = load_font(20)  # 使用20号字体
    draw.text((10, 10), object_name, font=font, fill=(0, 0, 0))
    
    return background

# 按照物品尺寸正确排列物品的方法
async def place_items_in_grid(items, grid_size=3):
    cell_size = 150
    grid_image = Image.new('RGBA', (grid_size * cell_size, grid_size * cell_size), (28, 33, 34, 80))
    draw_grid = ImageDraw.Draw(grid_image)  # 初始化网格绘制对象
    
    # 初始化网格占用状态（根据grid_size动态生成）
    grid_occupied = [[False for _ in range(grid_size)] for _ in range(grid_size)]
    
    # 检查物品是否能放入网格
    total_cells = sum(item['length'] * item['width'] for item in items)
    max_cells = grid_size * grid_size
    if total_cells > max_cells:
        raise ValueError(f"物品总占用格子数({total_cells})超过网格容量({max_cells})")
    
    for item in items:
        # 下载并处理原始图片（异步请求）
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(item['pic'])
        original_img = Image.open(BytesIO(response.content)).convert("RGBA")
        
        # 根据物品尺寸计算缩放比例
        item_width = item['width'] * cell_size
        item_height = item['length'] * cell_size
        
        # 保持原始比例缩放图片
        aspect_ratio = original_img.width / original_img.height
        if aspect_ratio > 1:  # 宽大于高
            new_width = item_width
            new_height = int(item_width / aspect_ratio)
        else:  # 高大于宽
            new_height = item_height
            new_width = int(item_height * aspect_ratio)
            
        resized_img = original_img.resize((new_width, new_height), Image.LANCZOS)
        
        # 创建带背景和文字的完整图片
        background_color = get_background_color(item['grade'])
        final_img = Image.new('RGBA', (item_width, item_height), background_color)
        
        # 居中放置缩放后的图片
        x_offset = (item_width - new_width) // 2
        y_offset = (item_height - new_height) // 2
        final_img.paste(resized_img, (x_offset, y_offset), resized_img)
        
        # 添加物品名称（带半透明背景和自动换行）
        draw = ImageDraw.Draw(final_img)
        font = load_font(24)  # 使用24号字体
        text = item['objectName']
        
        # 自动换行处理
        max_width = final_img.width - 20  # 留出边距
        avg_char_width = font.getlength("汉")  # 计算汉字宽度
        chars_per_line = max(1, int(max_width / avg_char_width))
        lines = textwrap.wrap(text, width=chars_per_line)
        
        # 计算文本块总高度
        line_height = font.size + 4  # 行间距
        total_height = len(lines) * line_height
        
        # 绘制半透明背景（包含所有行）
        padding = 8
        bg_rect = [0, 0, final_img.width, total_height + padding*2]
        # draw.rectangle(bg_rect, fill=(128, 128, 128, 0))  # 保持半透明
        
        # 逐行绘制文本
        for i, line in enumerate(lines):
            text_position = (padding, padding + i * line_height)
            draw.text(text_position, line, font=font, fill=(0, 0, 0))
        
        placed = False
        # 遍历所有可能的放置位置 - 使用动态grid_size
        for y in range(grid_size - item['length'] + 1):
            for x in range(grid_size - item['width'] + 1):
                # 检查目标区域是否空闲
                can_place = True
                for i in range(item['length']):
                    for j in range(item['width']):
                        if grid_occupied[y + i][x + j]:
                            can_place = False
                            break
                    if not can_place:
                        break
                
                if can_place:
                    # 计算粘贴位置
                    paste_x = x * cell_size
                    paste_y = y * cell_size
                    grid_image.paste(final_img, (paste_x, paste_y), final_img)
                    
                    # 标记占用网格
                    for i in range(item['length']):
                        for j in range(item['width']):
                            grid_occupied[y + i][x + j] = True
                    
                    placed = True
                    break
            if placed:
                break
        
        # if not placed:
        #     print(f"警告: 物品 '{item['objectName']}' 无法放置到网格中")
    
    border_color = (211, 211, 211, 179)
    
    # 绘制分割线
    for y in range(grid_size):
        for x in range(grid_size):
            if not grid_occupied[y][x]:
                x0 = x * cell_size
                y0 = y * cell_size
                x1 = x0 + cell_size
                y1 = y0 + cell_size
                draw_grid.rectangle([x0, y0, x1, y1], outline=border_color, width=1)

    return grid_image

# 随机选择物品 - 增加容器配置参数
def select_random_items(all_items, container_type="small_safe"):
    # 获取容器配置
    config = CONTAINER_CONFIGS.get(container_type, {})
    
    allowed_types = config.get("allow_types", [])
    allowed_items = [item for item in all_items 
                    if item.get("secondClass") in allowed_types]
    
    # 按品质权重选择
    weighted_items = []
    for item in allowed_items:
        grade = item.get("grade", 1)
        weight = config.get("grade_weights", {}).get(grade, 1)
        weighted_items.extend([item] * weight)
    
    # 随机选择物品数量
    num_items = random.randint(config.get("min_items", 1), config.get("max_items", 2))
    selected_items = random.sample(weighted_items, min(num_items, len(weighted_items)))
    
    return selected_items

def add_title_area(grid_image, container_name="", user_name="", plugin_name="三角洲抽卡插件", icon_path=None):
    """在网格图片上方添加标题区域"""
    title_height = 80
    
    # 创建新图片，高度为原图高度+标题高度
    total_height = grid_image.height + title_height
    total_width = grid_image.width
    new_image = Image.new('RGBA', (total_width, total_height), (255, 255, 255, 255))
    
    # 绘制标题背景（半透明灰色）
    draw = ImageDraw.Draw(new_image)
    title_bg_color = (128, 128, 128, 180)  # 半透明灰色
    draw.rectangle([0, 0, total_width, title_height], fill=title_bg_color)
    
    font = load_font(24)  # 使用24号字体

    
    # 获取当前时间
    # current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    title_text = f"{user_name} 摸到了 {container_name}"

    max_width = total_width - 40  # 左右各20像素边距
    avg_char_width = font.getlength("汉")  # 计算汉字宽度
    chars_per_line = max(1, int(max_width / avg_char_width))
    lines = textwrap.wrap(title_text, width=chars_per_line)
    
    # 计算文本块总高度（含行间距）
    line_height = font.size + 4  # 行间距4px
    total_text_height = len(lines) * line_height
    
    # 计算文本的垂直起始位置（居中）
    text_y = (title_height - total_text_height) // 2
    
    # 加载并处理容器图标（新增）
    icon_x = 20  # 图标左边距
    if icon_path:
        try:
            # 加载图标并调整大小
            icon_img = Image.open(Path(__file__).parent / icon_path).convert("RGBA")
            # 缩放图标（高度为标题区域的70%）
            icon_height = int(title_height * 0.7)
            icon_aspect = icon_img.width / icon_img.height
            icon_width = int(icon_height * icon_aspect)
            icon_img = icon_img.resize((icon_width, icon_height), Image.LANCZOS)
            
            # 计算图标垂直位置（居中）
            icon_y = (title_height - icon_height) // 2
            
            # 粘贴图标到标题区域
            new_image.paste(icon_img, (icon_x, icon_y), icon_img)
        except Exception as e:
            print(f"加载图标失败: {str(e)}")
    
    # 计算文本块总宽度（用于居中）
    max_line_width = max(font.getlength(line) for line in lines)
    
    # 计算文本水平起始位置（居中）
    text_x = (total_width - max_line_width) // 2
    
    # 逐行绘制文本（居中显示）
    for i, line in enumerate(lines):
        draw.text((text_x, text_y + i * line_height), line, font=font, fill=(255, 255, 255))
    
    # 将原网格图片粘贴到标题下方
    new_image.paste(grid_image, (0, title_height), grid_image)
    return new_image


async def process(container_type="small_safe", user_name="玩家1"):
    all_items = load_all_items()
    retry_count = 0
    max_retries = 10
    
    # 获取容器配置
    container_config = CONTAINER_CONFIGS.get(container_type, {})
    container_name = container_config.get("name", "未知容器")
    
    # 获取图标路径（新增）
    icon_path = container_config.get("icon", None)
    
    async with httpx.AsyncClient(timeout=30) as client:
        while retry_count < max_retries:
            selected_items = select_random_items(all_items, container_type)
            try:
                grid_size = container_config.get("grid_size", 3)
                result_image = await place_items_in_grid(selected_items, grid_size)
                
                result_image = add_title_area(
                    result_image, 
                    container_name, 
                    user_name=user_name,
                    icon_path=icon_path  # 新增图标路径参数
                )
                
                img_byte_arr = BytesIO()
                result_image.save(img_byte_arr, format='PNG')
                
                img_byte_arr.seek(0)
                return img_byte_arr
            except ValueError as e:
                #print(f"错误：{e}，重新选择物品... (尝试 {retry_count+1}/{max_retries})")
                retry_count += 1
    
    # 达到最大重试次数后仍强制显示结果
    #print("达到最大重试次数，使用最后一次尝试")
    selected_items = select_random_items(all_items)
    result_image = place_items_in_grid(selected_items)
    
    # 添加标题区域
    result_image = add_title_area(result_image, user_name="玩家1")
    
    # 修改：创建BytesIO对象并返回图片
    img_byte_arr = BytesIO()
    result_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

async def generate_result(container_type="small_safe", user_name="玩家1"):
    """统一抽卡入口函数"""
    if container_type == "random":
        # 从配置中按权重随机选择一个容器类型
        container_keys = list(CONTAINER_CONFIGS.keys())
        # 根据容器稀有度动态计算权重：高爆率->10, 中等爆率->20, 低爆率->30
        weights = []
        for key in container_keys:
            rarity = CONTAINER_CONFIGS[key].get("rarity", 1)
            if rarity >= 4:  # 高爆率容器
                weight = 10
            elif rarity >= 2:  # 中等爆率容器
                weight = 20
            else:  # 低爆率容器
                weight = 30
            weights.append(weight)
        container_type = random.choices(container_keys, weights=weights, k=1)[0]
        #print(f"随机选择容器类型: {container_type} (权重: {weights})")
    
    return await process(container_type, user_name)

# if __name__ == "__main__":
#     # 默认使用小保险箱
#     img_bytes = asyncio.run(generate_result("random", user_name="Alpaca"))
#     # 修改：使用返回的BytesIO对象显示图片
#     result_image = Image.open(img_bytes)
#     result_image.show()
