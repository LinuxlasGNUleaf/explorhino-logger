import os
import pickle
import platform
import regex

from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

default_name = ''
if platform.system() == 'Linux':
    import pwd
    default_name = pwd.getpwuid(os.getuid()).pw_gecos.split(',')[0]

#========== paths ==========
font_file = 'src/RobotoMono.ttf'
template_file = 'src/template.png'
quickuse_file = 'quickuse.arr'

#========== fonts & positions ==========
# name field
name_pos = (840,965)
name_font = ImageFont.truetype(font_file, 115)

# IBAN field
iban_pos = (1800,1280)
iban_font = name_font

# month field
month_pos = (500, 1910)
month_font = name_font

# year field
year_pos = (1610, 1930)
year_font = ImageFont.truetype(font_file, 95)

# table
table_font = ImageFont.truetype(font_file, 118)
table_xpos = [230,945,1805,2510]
y_start = 2650
y_delta = 185.3

# total hour field
hours_pos = (1790, 6795)
hours_font = ImageFont.truetype(font_file, 160)

#========== german localizations ==========
months_de = ['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember']
weekdays_de = ['Mo','Di','Mi','Do','Fr','Sa','So']

#========== div. configs ==========
iban_re = regex.compile(r'\b[A-Z]{2}[0-9]{2}(?:[ ]?[0-9]{4}){4}(?!(?:[ ]?[0-9]){3})(?:[ ]?[0-9]{1,2})?\b')
MAX_INFO = 30
TERMINAL_WIDTH = 60
MAX_TABLE_ENTRIES = 22

#========== objects ==========
table = []

time_repr = lambda seconds: f'{int(seconds//3600):0>2},{int((seconds%3600)/36):0<2}'

if os.path.isfile(quickuse_file):
    with open(quickuse_file,'rb') as qfile:
        default_iban, quickuse = pickle.load(qfile)
else:
    default_iban, quickuse = '',{}

img = Image.open(template_file)
template = ImageDraw.Draw(img)

def terminal_print(print_str, start_line=False, end_line=False):
    if start_line:
        print(f'//{print_str.center(len(print_str)+2).center(TERMINAL_WIDTH,"=")}\\\\')
        return
    elif end_line:
        print(f'\\\\{TERMINAL_WIDTH*"="}//\n')
        return
    else:
        for splitstr in print_str.split('\n'):
            print(f'|| {splitstr}')

def terminal_input(input_str):
    return input(f'|| {input_str}')

terminal_print('GENERAL INFO',start_line=True)

while True:
    if default_name:
        name = terminal_input(f'Enter your name (press enter to default to {default_name}): ') or default_name
    else:
        name = terminal_input('Enter your name : ')
    if name:
        terminal_print(f'Name set to: {name}\n')
        break
    else:
        terminal_print('Name must not be empty.')

while True:
    if default_iban:
        iban = terminal_input(f'Enter your IBAN (press enter to default to {default_iban}): ') or default_iban
    else:
        iban = terminal_input('Enter your IBAN : ')
    if iban:
        if regex.search(iban_re,iban.strip()):
            terminal_print(f'IBAN set to: {iban}\n')
            break
        else:
            terminal_print('That does not look like a valid IBAN ._. Check again.')
    else:
        terminal_print('IBAN must not be empty.')

while True:
    try:
        last_year = datetime.now().year if datetime.now().month > 1 else datetime.now().year - 1 
        year = int(terminal_input(f'Enter the year (press enter to default to {last_year}): ') or last_year)
        terminal_print(f'Year set to: {year}\n')
        break
    except ValueError:
        terminal_print('Invalid input, must be integer.')


while True:
    try:
        if datetime.now().month == 1: # if it's January
            if last_year != year: # if the user changed the year, make current month the default
                last_month = 1
            else:
                last_month = 12 # else make it December of last year
        else:
            last_month = (datetime.now().month-1) # otherwise choose last month
        month = int(terminal_input(f'Enter the month (1-12) (press Enter to default to {last_month} ({months_de[last_month-1]})): ') or last_month)
        terminal_print(f'Month set to: {months_de[month-1]}')
        break
    except ValueError:
        terminal_print('Invalid input, must be integer.')

terminal_print('',end_line=True)

total_seconds = 0.0
start_date = datetime(year,month,1)

while len(table) <= MAX_TABLE_ENTRIES:
    terminal_print(f'ENTRY {len(table)+1}/22',start_line=True)
    # Day Input
    while True:
        try:
            start_date = datetime(year,month,int(terminal_input('Enter the day (1-31): ')))
            terminal_print(f'Day set to {weekdays_de[start_date.weekday()]} {start_date.strftime("%d.%m.")}\n')
            break
        except ValueError:
            terminal_print(f'Invalid input, must be a valid day in {datetime.strftime(start_date, "%B")}')

    # Start Time Input
    while True:
        try:
            time = terminal_input('Enter the start time (00:00-23:59, mins are optional): ').split(':')
            if len(time) == 1:
                time.append(0)
            start_date = start_date.replace(hour=int(time[0]),minute=int(time[1]))
            break
        except (ValueError, IndexError):
            terminal_print('Invalid input, must be valid time.')

    # End Time Input
    while True:
        try:
            time = terminal_input('Enter the end time (00:00-23:59, mins are optional): ').split(':')
            if len(time) == 1:
                time.append(0)
            end_date = start_date.replace(hour=int(time[0]),minute=int(time[1]))
            delta = (end_date-start_date)
            if delta.days != 0 or delta.seconds == 0:
                terminal_print('End time has to be AFTER the start time at the same day.')
                continue
            terminal_print(f'Time delta: {time_repr(delta.seconds)} hrs\n')
            break
        except (ValueError, IndexError):
            terminal_print('Invalid input, must be valid time.')

    # Job Info Input
    while True:
        quicklist = sorted(quickuse, key=lambda x: quickuse[x],reverse=True)
        for i, entry in enumerate(quicklist):
            terminal_print(f'{i+1} "{entry}"')

        if quicklist:
            info = terminal_input('Enter the job info or use a number for a shortcut: ').strip()
        else:
            info = terminal_input('Enter the job info: ').strip()

        if not info:
            terminal_print('Job Info can not be empty.')
            continue
        if len(info) > MAX_INFO:
            terminal_print(f'Job Info is too long, has to be shorter than {MAX_INFO+1} characters.')
            continue

        if info.isdigit():
            if int(info) in range(1,len(quicklist)+1):
                info = quicklist[int(info)-1]
            else:
                terminal_print('Index not in quicklist!')
                continue
        else:
            if info in quickuse.keys():
                quickuse[info] += 1
            else:
                quickuse[info] = 1
        break

    # Saving the data for this entry
    table.append((start_date.strftime('%d.%m. ')+weekdays_de[start_date.weekday()],
                            start_date.strftime('%H:%M-')+end_date.strftime('%H:%M'),
                            f'{time_repr(delta.seconds)} hrs',
                            info))

    # Inquiry for new line
    total_seconds += delta.seconds
    terminal_print("",end_line=True)
    cancel = False
    while True:
        new_entry = input('New entry? (y/n)').strip().lower()
        if new_entry == 'n':
            cancel = True
            break
        elif new_entry == 'y':
            break
        else:
            print('Invalid answer.')

    if cancel:
        break

# writing the collected data to the image
template.text(name_pos, name, font=name_font, fill=(0,0,0))
template.text(iban_pos, iban, font=iban_font, fill=(0,0,0))
template.text(month_pos, months_de[month-1], font=month_font, fill =(0, 0, 0))
template.text(year_pos, str(year)[2:], font=year_font, fill =(0, 0, 0))

for i, row in enumerate(table):
    for column in range(4):
        template.text((table_xpos[column], y_start + y_delta * i), row[column], font=table_font, fill =(0, 0, 0))

template.text(hours_pos, f'{time_repr(total_seconds)} h', font=hours_font, fill =(0, 0, 0))
img.save(f'job_log_{start_date.month:0>2}_{str(start_date.year)[2:]}.png')

with open(quickuse_file,'wb') as qfile:
    pickle.dump((iban,quickuse), qfile)
