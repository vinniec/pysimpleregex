#!/usr/bin/env python3
# ~ import PySimpleGUIWeb as sg
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
    # ~ [sg.InputText(size=(20,10))] #una linea sola
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
regex = regtext = text = ""
while True:
    #ogni secondo rilascio uno stato
    event, values = window.read(timeout=1000)  #un controllo al sec
    #dovrebbe togliere il focus quando si switcha con tab, ma...
    if sg.name == "PySimpleGUI":
        window['result'].Widget.config(takefocus=0)
    
    if event is None:   #se premo su esc, escio
        break 
    if regtext != values['regbox'][:-1]: #se la regex è cambiata l'aggiorno
        regtext = values['regbox'][:-1]  #[:-1] tolgo l'\n alla fine
        try:                regex = re.compile(rf"""{regtext}""")
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
            # result = [s for s in result if s]
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
