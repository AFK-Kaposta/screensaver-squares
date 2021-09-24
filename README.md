# Screen saver - Squares
_By AFK_Kaposta_

### Description:
A screen saver that consists of a grid of squares. 
A random square starts with a different color,
and squares close by become this other color, making more
squares change color until the whole screen fills with this
new color. Then a new color appears, and the cycle continues. 

this screensaver supports any amount and arrangement of
monitors.

### Installation:
To install the screensaver, copy the `Squares.scr` file to this folder: `C:\Windows\System32`. After that, select 
'Squares' in the Windows control panel > Search: 'screen saver' > click on 'Change screen saver'.

### Software Used:
_(This software is not required in order to run `Squares.scr`.)_

Python version: 3.7

Python Arcade Library version: 2.5.6

Python Arcade Screensaver Framework: https://github.com/SirGnip/arcade_screensaver_framework

### Modifying the Screen Saver (Advanced):
In order to modify this screen saver you will need to have all the software above installed on your system. After 
installing the relevant software, edit `screensaver.pyw`. In the file you will find five parameters:
- `DARK_THEME` - If this parameter is set to `True`, the screen saver will only pick darker colors. If it is set to 
  `False`, the screen saver will pick any color.
- `COLOR_CHANGE_RATE` - This value determines how fast the color of each tile will change. The larger this number, 
  the slower each tile will change to the next color.
- `UPDATES_PER_SECOND` - This number determines the number of updates the screen saver goes through every second. 
- `TILE_SIZE` - This number determines the width and height of all the tiles. If the screen saver doesn't run 
  smoothly, increase this value.
  
After modifying the values to your content, run the following file: `convert to scr format.bat`, then press any. 
This will convert the Python script you just modified to a `.scr` file, which will be located in the folder `dist`.

**NOTE:** In order to delete or replace the screen saver file in the System32 folder you will first need to select 
a different screen saver, and either restart you PC or go to the Task Manager and end all the `screensaver.scr` or 
`Squares.scr` processes.
