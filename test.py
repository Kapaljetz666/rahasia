from PIL import Image, ImageDraw, ImageFont

# Ukuran gambar
width, height = 512, 768
template = Image.new("RGBA", (width, height), (255, 255, 255, 200))  # Background semi transparan

draw = ImageDraw.Draw(template)

# Ukuran kotak transparan di tengah
box_width, box_height = 256, 256
box_x1 = (width - box_width) // 2
box_y1 = (height - box_height) // 2
box_x2 = box_x1 + box_width
box_y2 = box_y1 + box_height

# Buat area tengah transparan
for y in range(box_y1, box_y2):
    for x in range(box_x1, box_x2):
        template.putpixel((x, y), (0, 0, 0, 0))  # Transparan penuh

# Tambahkan garis tepi kotak
draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline=(0, 0, 0, 255), width=3)

# Tambahkan teks di bawah kotak
text = "Tersenyumlah Hari Ini!"
font = ImageFont.load_default()
text_width, text_height = draw.textsize(text, font=font)
text_x = (width - text_width) // 2
text_y = box_y2 + 20
draw.text((text_x, text_y), text, fill=(0, 0, 0, 255), font=font)

# Simpan gambar
template.save("template_transparan.png")
print("Template berhasil disimpan sebagai template_transparan.png")
