# explorhino-logger
A automated script to fill reports for Explorhino

# Usage
Execute the script `python3 main.py`

First you will be prompted for:
- Name (on Linux, you will be able to choose your full user name as a shortcut)
- IBAN (will be cached / presented as a shortcut if already cached)
- Year (current year as default)
- Month (last month by default)

Then, for each entry you will be prompted for:
- Day of the Month (format: `D` or `DD`, range 1 - 31 depending on month)
- Start Time (format: `HH` or `HH:MM`)
- End Time (format: `HH` or `HH:MM`)
- Job Info (you will be presented with a list of your most used job infos to chose from, or enter a new one)

After each entry you will be asked if you want to add a new line/entry, the max is 22 lines.

In the end, the report will be compiled, the total time calculated and a new file created that contains the report.
In case you want to delete the cached Job Infos and IBAN, delete `quickuse.arr`
