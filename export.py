import datetime
import os

from PIL import Image, ImageDraw, ImageFont

# ========== paths ==========
font_file = 'src/RobotoMono.ttf'
template_file = 'src/template.png'
empty_template_file = 'src/template_empty.png'

# ========== fonts & positions ==========
# name field
name_pos = (840, 965)
name_font = ImageFont.truetype(font_file, 115)

# IBAN field
iban_pos = (1800, 1280)
iban_font = name_font

# month field
month_pos = (500, 1910)
month_font = name_font

# year field
year_pos = (1610, 1930)
year_font = ImageFont.truetype(font_file, 95)

# table
table_font = ImageFont.truetype(font_file, 118)
table_x_positions = [230, 945, 1805, 2510]
y_start = 2650
y_delta = 185.3

# total hour field
hours_pos = (1790, 6795)
hours_font = ImageFont.truetype(font_file, 160)

# ========== german localizations ==========
months_de = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
             'August', 'September', 'Oktober', 'November', 'Dezember']
weekdays_de = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']


def time_str(seconds):
    return f'{int(seconds // 3600):>2},{int((seconds % 3600) / 36):0<2}'


def export_to_pdf(payload):
    # Extracting data from payload
    name = payload["name"]
    month = payload["month"]
    year = payload["year"]
    iban = payload["iban"]
    use_template = payload["use_pdf_template"]
    entries = payload["entries"]

    table = []
    total_seconds = 0
    for date, start_time, end_time, work_time, location in entries:
        date = datetime.date(year=date.year(), month=date.month(), day=date.day())
        start_time = datetime.time(hour=start_time.hour(), minute=start_time.minute())
        end_time = datetime.time(hour=end_time.hour(), minute=end_time.minute())
        secs = int(work_time[:2])*3600 + int(work_time[3:]) * 60
        total_seconds += secs
        table.append((date.strftime('%d.%m. ') + weekdays_de[date.weekday()],
                      start_time.strftime('%H:%M-') + end_time.strftime('%H:%M'),
                      f"{time_str(secs)} hrs",
                      location))

    if use_template:
        img = Image.open(template_file)
    else:
        img = Image.open(empty_template_file)
    template = ImageDraw.Draw(img)

    # writing the collected data to the image
    template.text(name_pos, name, font=name_font, fill=(0, 0, 0))
    template.text(iban_pos, iban, font=iban_font, fill=(0, 0, 0))
    template.text(month_pos, months_de[month], font=month_font, fill=(0, 0, 0))
    template.text(year_pos, str(year)[2:], font=year_font, fill=(0, 0, 0))

    for i, row in enumerate(table):
        for column in range(4):
            template.text((table_x_positions[column], y_start + y_delta * i), row[column], font=table_font, fill=(0, 0, 0))

    template.text(hours_pos, f'{time_str(total_seconds)} h', font=hours_font, fill=(0, 0, 0))
    output_fname = f'job_log_{month+1:0>2}_{str(year)[2:]}'
    img.save(f'{output_fname}.png')
    os.system(f'magick convert -scale 1218x1848 -compress JPEG -quality 90 {output_fname}.png {output_fname}.pdf')
    os.system(f'rm {output_fname}.png')