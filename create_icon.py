"""生成应用图标"""
from PIL import Image, ImageDraw, ImageFont


def create_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    images = []
    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 113, 227, 255))
        draw = ImageDraw.Draw(img)
        # 画一个简化的文档图标
        margin = size // 6
        # 文档主体
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=size // 10,
            fill=(255, 255, 255, 230),
        )
        # 文档折角
        corner = size // 3
        draw.polygon(
            [size - margin - corner, margin,
             size - margin, margin + corner,
             size - margin, margin],
            fill=(200, 220, 255, 255),
        )
        # "AI" 文字
        try:
            font_size = size // 3
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        text = "AI"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (size - tw) // 2
        ty = (size - th) // 2
        draw.text((tx, ty), text, fill=(0, 113, 227, 255), font=font)

        images.append(img)

    # 保存为 .ico（多尺寸）
    ico_path = "icon.ico"
    images[0].save(ico_path, format="ICO",
                   sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    print(f"图标已生成: {ico_path}")


if __name__ == "__main__":
    create_icon()
