#!/usr/bin/env python3
# ~ import PySimpleGUIWeb as sg
#aggiornamento per git
import PySimpleGUI as sg
import re 
from time import monotonic as now 
 
def get_curr_screen_geometry(tk):
    """
    Workaround to get the size of the current screen in a multi-screen setup.

    Returns:
        position, fullsize (int): Two tuple of int,int dimension
    """
    root = tk.Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    geometry = root.winfo_geometry()
    root.destroy()
    x,y,xp,yp = geometry.translate("".maketrans("x+", "  ")).split()
    position = int(xp), int(yp)
    fullsize = int(x), int(y)
    
    return position, fullsize
 

sg.theme('BrightColors')  


layout = [
    [
        sg.Checkbox("I", key="I", tooltip="IGNORECASE"),
        sg.Checkbox("L", key="L", tooltip="LOCALE (only with byte pattern)", disabled=True),
        sg.Checkbox("M", key="M", tooltip="MULTILINE"),
        sg.Checkbox("S", key="S", tooltip="DOTALL"),
        sg.Checkbox("U", key="U", tooltip="UNICODE (default if not ascii)", disabled=True),
        sg.Checkbox("X", key="X", tooltip="VERBOSE"),
        sg.Checkbox("A", key="A", tooltip="ASCII"),
    ],
    [sg.Multiline(key="regbox", size=(30,3), autoscroll=True,
                  focus=True, # ~ enable_events=True, 
                  enter_submits=True, do_not_clear=True,
    )],
    [sg.Multiline(key="text", size=(30,6), autoscroll=True,
                  enter_submits=True, do_not_clear=True,
    )],
    [sg.Multiline(key="result", size=(30, 6), autoscroll=True, disabled=True)]
]
#enter_submits non funziona, almeno non in accoppiata con do_not_clear
#multiline ha sempre un \n alla fine anche se è vuoto
#Output cattura anche stder e stdout!

#calcolo pos finestra la creo 
if sg.name == "PySimpleGUI":
    sloc, ssiz = get_curr_screen_geometry(sg.tkinter) 
    offset = map(sum, zip(sloc, map(lambda n: n//4, ssiz)))
    window = sg.Window("rg", layout, location=offset,
                        font=("Default", 20))
elif sg.name == "PySimpleGUIWeb":
    window = sg.Window("rg", layout, font=("Default", 20))



parse = False
parse_delay = 1
start_cron = now()
regex = regtext = text = flags_old = ""
flags_cmb = "ILMSUXA"
while True:
    #ogni secondo rilascio uno stato
    event, values = window.read(timeout=1000)  #un controllo al sec
    #dovrebbe togliere il focus quando si switcha con tab, ma...
    if sg.name == "PySimpleGUI":
        window['result'].Widget.config(takefocus=0)
    
    if event is None:   #se premo su esc, escio
        break 

    #se la regex è cambiata l'aggiorno, [:-1] tolgo l'\n alla fine
    flags_new = [f for f in flags_cmb if values[f]]
    if (flags_old != flags_new) or (regtext != values['regbox'][:-1]):
        flags_old = flags_new
        flags_sum = sum([eval("re."+f) for f in flags_old])
        regtext = values['regbox'][:-1]
        try:                regex = re.compile(regtext, flags_sum)
        except re.error:    regex = ''
        parse = True
        start_cron = now()
    if text != values['text'][:-1]:     #se il testo è cambiato l'aggiorno
        text = values['text'][:-1]
        parse = True
        start_cron = now()
    if parse:
        if now()-start_cron >= parse_delay: 
            parse = False
            result = re.findall(regex, text)
            if not regtext: #con "" findall restituisce risultati vuoti
                result = [s for s in result if s] #non consento
            lr = len(str(len(result)))
            result = [f"{n:0{lr}}) {s}" for n, s in enumerate(result,1)]
            result = "\n".join(result)
            window['result'].update(result)
            start_cron = now()
window.close()
        
        
        
        
        
    #DELAY EVENTI
    # ~ if event is None:
        # ~ break
    # ~ elif event == "reg":
        # ~ now = ns()
        # ~ dif = int((now-back)/1E9)
        # ~ if dif >= 5:
            # ~ print('e', dif)
            # ~ back = now
            # ~ n = 1            
        # ~ elif dif >= n:
            # ~ print(n, dif)
            # ~ n += 1
