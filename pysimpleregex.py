#!/usr/bin/env python3
#region import 
import re, pathlib
import PySimpleGUI as sg    #import PySimpleGUIWeb as sg
import jsonpickle as json
from datetime import datetime
# from time import monotonic as now 
json.set_encoder_options('json', sort_keys=True, indent=4)
#endregion
#region costanti 
PRESET_DIM = None #((800, 0), (1104, 825), (5, 28))
TFONT = "Monospace"
DFONT = 20
BFONT = (TFONT, DFONT)                  #big font
SFONT = (TFONT, int(DFONT/3*2))         #font checkbox
CH_FLEN = 30                            #full len in char of box
CH_1_10 = int(CH_FLEN / 10)
CH_9_10 = int(CH_FLEN / 15 * 13)
# CH_SLEN = int(CH_FLEN/3*2)            #len in char of combobox 2/3
CH_SLEN = 17
CH_FWID = 18                            #tot width char, hardcoded magicnumber
STD_REGEX = {"data" : ["fun", "regex", "flag", "testo", 0, "replace"]}
GENRE = ("findall", "fullmatch", "match", "search", "split", "sub", "subn")
GENIN = GENRE[0]
FLAGS_CMB = "ILMSUXA"
DELAY = 1; DETAIL = DELAY/2         #elapsedtime/subdivision between checks
#endregion

def preset_dim(sg):
    """
    return, position, size and offset caused by decorator
    
    Parameters
    ----------
    sg : PySimpeGUI module
        imported module of pysimplegui
    
    Returns
    -------
    ((int,int),(int,int),(int,int))
        start position of the screen, dimension and decorator shift
    """
    if isinstance(PRESET_DIM, tuple): return PRESET_DIM
    win = sg.Window('mlw', [[]], alpha_channel=0)
    win.read(timeout=0)
    lc1 = win.current_location()
    win.close(); del win
    win = sg.Window('mlw', [[]], location=lc1, alpha_channel=0)
    win.read(timeout=0)
    lc2 = win.current_location()
    geometry = neogeo = win.TKroot.winfo_geometry()
    win.maximize()
    xd, yd = lc2[0]-lc1[0], lc2[1]-lc1[1]
    decorator = xd, yd
    while geometry == neogeo:
        win.refresh()
        neogeo = win.TKroot.winfo_geometry()
    geometry = neogeo
    win.close(); del win
    x,y,xp,yp = geometry.translate("".maketrans("x+", "  ")).split()
    position = int(xp), int(yp)
    fullsize = int(x), int(y)
    return position, fullsize, decorator

class Appendsave:
    """
    Questa classe salva i cambiamenti in fondo al file in una
    struttura dati delimitata da due marcatori
    """
    SCALAR = {str, bytes, bool, int, float, complex, slice, type(None)}
    ITERAB = {str, bytes, list, tuple, dict, set, frozenset, range, bytearray}
    CONTEN = tuple(ITERAB-SCALAR)
    SCALAR = tuple(SCALAR)
    ITERAB = tuple(ITERAB)

    def __init__(self, standard=None, mka='### SAVE ###', mkb='### FINE ###', dateform="%Y%m%d%H%M%S%f"):
        """
        init
        
        Parameters
        ----------
        standard : list, optional
            struttura dati standard, by default []
        mka : str, optional
            marcatore iniziale (deve iniziare con #), by default '### SAVE ###'
        mkb : str, optional
            marcatore finale (deve iniziare con #), by default '### FINE ###'
        dateform : str, optional
            formato data, by default "%Y%m%d%H%M%S%f"
        """
        
        old_script = pathlib.Path(__file__).resolve()
        tmp_script = old_script.parent / (old_script.name + "_tmp")
        bkp_script = old_script.parent / (old_script.name + "_bkp")

        if standard is None: standard = []
        self.standard = standard
        list(self.discendi(standard))   #produco lo schema di default con cui
        self.schema = self._schema_last  #andrò a validare gli inserimenti
        self.mka = mka
        self.mkb = mkb
        self.dateform = dateform
        self.old_script = old_script
        self.tmp_script = tmp_script
        self.bkp_script = bkp_script

    @property
    def righe(self):
        """
        le righe di questo script, preferisco calcolarle ogni volta così
        è possibile editare lo script durante l'esecuzione dell'interfaccia
        (sconsigliabile ma possibile).
        Assicuro un newline all'ultima riga.

        Returns
        -------
        lista di stringhe
            una stringa per ogni riga con un newline alla fine
        """
        testo_ben_terminato = self.old_script.read_text().rstrip() + "\n"
        lista_stringhe = testo_ben_terminato.splitlines(keepends=True)
        return lista_stringhe
    @righe.setter
    def righe(self, *args):
        """
        negato il set automatico (inutile ma per formalismo)
        """
        pass
    
    def indici_json(self, dati=None):
        """
        restituisce gli indici delle posizioni dei marcatori se ci sono
        altrimenti le posizioni degli indici con la struttura dati
        standard (non scrive niente, viene considerato il file attuale!)

        Returns
        -------
        (int, int)
            indice marcatore iniziale, indice marcatore finale
        """
        righe = self.righe #le liste sono mutabili ma self.righe viene generato alla richiesta
        inr = righe[::-1]
        lnr = len(righe) #questo mi porta ad avere gli indici +1 che mi influisce nello slice
        try:    #trovo gli indici dell'inizio e della fine del json
            # usare .index delle liste non va bene perché devo confrontare strippato
            j_iniz = lnr - next(n for n,s in enumerate(inr) if self.mka == s.strip())
            j_fine = lnr - next(n for n,s in enumerate(inr) if self.mkb == s.strip())
        except (ValueError, StopIteration) as e: #se non esiste devo creare un salvataggio standard
            dati = self.standard if dati is None else dati
            righe.append(self.mka + "\n")
            j_iniz = len(righe)
            jsonst = f'{json.dumps(dati)}\n'
            righe += ["#"+s for s in jsonst.splitlines(keepends=True)]
            righe.append(self.mkb)
            j_fine = len(righe)
        return j_iniz, j_fine
    def add_own_exec(self, file):
        """
        aggiunge i permessi di esecuzione al file per l'utente
        
        Parameters
        ----------
        file : path
            stringa o Path del file
        """
        file = pathlib.Path(file)
        p_oc = oct(file.stat().st_mode)
        pref, perm = p_oc[:-3], p_oc[-3:]
        perm = str(int(perm[0]) | 1) + perm[1:]
        file.chmod(int(pref+perm,8))    
    def scrivi_dati(self, testo, proteggi_script=True, diff_dati=True):
        """
        scrive i dati, ma solo se ci sono cambiamenti
        
        Parameters
        ----------
        testo : string
            testo che verrà salvato
        proteggi_script : bool
            se vero, la scrittura dei dati viene effettuata solo se il codice 
            non viene cambiato ma il controllo è effettuato l'ultima versione del
            file e il .bkp, così è possibile effettuare cambiamenti al codice ma non
            due volte di fila (e quindi non si rischia di perdere parti di codice
            senza accorgersi che non si può salvare). Ovviamente se non c'è il file
            .bkp allora questo controllo non viene effettuato, by default True
        diff_dati : bool
            se vero la scrittura dei dati viene effettuata solo se ci
            sono state modifiche, il controllo avviene solo se esiste
            un file .bkp, non c'è nessun rischio di perdere ipotetici
            cambiamenti altrimenti perché non si potrebbero comunque
            ritrovare nel bkp, by default True
        """
        otxt = self.old_script.read_text()
        p_bkp = self.bkp_script.is_file()
        p_scr = True
        if proteggi_script and p_bkp: 
            #se lo script fra file e bkp (se esiste è diverso non permetto la scrittura
            mka = "\n" + self.mka + "\n"
            btxt = self.bkp_script.read_text()
            if otxt.rsplit(mka, 1)[0].strip() != btxt.rsplit(mka, 1)[0].strip():
                #ho avuto qualche problemino qua, per adesso tengo così
                p_scr = False
        p_dif = testo != otxt if diff_dati and p_bkp else True #no camb? niente scrittura
        if p_scr and p_dif:
            self.tmp_script.write_text(testo)
            self.old_script.rename(self.bkp_script)
            self.tmp_script.rename(self.old_script)
            self.add_own_exec(self.old_script)
        else:
            er = f"Scrittura non effettuata: "\
                 f"{'nessun cambiamento' if not p_dif else ''}"\
                 f"{' & ' if not p_dif and not p_scr else ''}"\
                 f"{'codice cambiato' if not p_scr else ''}"
            raise ValueError(er)
            # raise ValueError(f"Scrittura non effettuata, {'dati uguali' if permesso else 'permesso negato'}.")
    def importa_dati(self):
        """
        preleva i dati dal fondo del file restituendoli nella struttura appropriata

        Returns
        -------
        [stesso formato di partenza]
            struttura dati contenente quanto salvato
        """
        j_iniz, j_fine = self.indici_json()
        if len(self.righe) < j_fine:    #se non ci sono ancora dati
            # self.esporta_dati(self.standard) #no, preferisco non farlo
            dati = self.standard #ritorno valori generici
        else:                           #ci sono i dati da importare
            righe_str = self.righe[j_iniz:j_fine-1]
            righe_str = [r.lstrip('#') for r in righe_str]
            strin_str = ''.join(righe_str)
            dati = json.loads(strin_str)
        return dati
    def esporta_dati(self, dati=None):
        """salva in coda i dati json, questo metodo è fatto per salvare
        una intera struttura dati aggiornata (non solo le differenze)

        Parameters
        ----------
        dati : struttura personalizzata, optional
            i dati da salvare, se non specificata vengono risalvati
            gli stessi dati già presenti(inutile?), by default None
        Returns
        -------
        struttura dati personalizzata
            gli stessi dati che sono stati salvati
        """
        if dati is None:
            dati = self.importa_dati()
        
        #creo la stringa del json e gli prependo i # dei commenti
        jstringa = json.dumps(dati) + "\n"
        com_list = ["#"+s for s in jstringa.splitlines(keepends=True)]

        #procuro gli indici (mi serve solo l'iniziale)
        j_iniz, j_fine = self.indici_json(dati)

        #separo le righe dello script e le unisco al nuovo json
        righe_script = self.righe[:j_iniz-1] + [self.mka + "\n"] + com_list + [self.mkb]
        testo_script = ''.join(righe_script)

        self.scrivi_dati(testo_script)
        return dati
    def elimina_dati(self):
        """
        cancella tutti i dati
        """
        j_iniz, j_fine = self.indici_json()
        script = ''.join(self.righe[:j_iniz-1])
        self.scrivi_dati(script, False)

    def salva(self, elemento, lambda_sort=None):
        """
        aggiunge l'elemento ai dati salvati, verifica che la struttura sia ideantica a 
        quello dello standard, si interessa solo della struttura contenitore più esterna
        e supporta solo liste e dizionari, se mai servirà altro lo implementerò dopo.
        
        Parameters
        ----------
        elemento : gli stessi tipi della struttura standard
            questo è il record che si andrà a salvare
        lambda_sort : funzione callback, optional
            funzione anche lambda che viene usata per ordinare
            la struttura dati, dato un elemento della struttura dati
            deve restituire il sottoelemento di questo che verrà usato
            per ordinare gli elementi. Se non la si specifica la struttura
            dati non viene ordinata prima di essere salvata. Se si vuole ordinare
            senza specificare nessuna chiave di ordinamento, si può usare
            lambda x:x,  by default None
        """
        validaz = self.valida(elemento) 
        dati = self.importa_dati()
        if dati == self.standard: #evito di incollare eventualmente + standard
            dati = elemento
        else:    
            if all(isinstance(op, list) for op in (elemento, dati)):
                dati += elemento
                if lambda_sort is not None:
                    dati = type(dati).__call__(sorted(dati, key=lambda_sort))
            elif all(isinstance(op, dict) for op in (elemento, dati)):
                dati.update(elemento)
                if lambda_sort is not None:
                    dati = dict(sorted(dati.items(), key=lambda_sort))
        self.esporta_dati(dati)
    def leggi(self, chiave):
        dati = self.importa_dati()
        return dati[chiave]
    def aggiorna(self, chiave, elemento):
        validaz = self.valida(elemento) #mi assicuro che ci sia lo stesso struttura
        dati = self.importa_dati()
        if all(isinstance(op, list) for op in (elemento, dati)):
            if isinstance(chiave, int) and chiave<len(dati):
                dati[chiave] = [elemento][0]
            else: raise TypeError(f"chiave {chiave} non idonea alla lista")
        elif all(isinstance(op, dict) for op in (elemento, dati)):
            if chiave in dati:
                chiave_el = next(iter(elemento))
                dati[chiave] =  elemento[chiave_el]
                # self.cancella(chiave)
                # dati.update(elemento)
            else: raise TypeError(f"chiave {chiave} non presente nel dizionario")
        else: raise TypeError("sono supportati solo contenitori esterni tipo lista o dict")
        self.esporta_dati(dati)
    def cancella(self, chiave):
        dati = self.importa_dati()
        dati.pop(chiave)
        self.esporta_dati(dati)
    def cerca(self, elemento):
        dati = self.importa_dati()
        isdict = isinstance(dati, dict) #memorizzo perché poi dati potrebbe cambiare
        conv = type(dati)
        concordanze = list()
        try: #se l'elemento passato è già completo oppure è contenuto così com'è
            if elemento == dati:
                concordanze.append(elemento)
            elif elemento in dati:
                if isdict: concordanze.append(conv([elemento]))
                else: concordanze.append(conv(elemento)) #forse conv non serve ma ok
        except TypeError: pass
        if not concordanze and isinstance(dati, self.CONTEN):
            if isdict:
                dati = dati.items()     #per attraversare con il for
            for record in dati: #per ogni figlio del contenitore principale
                for foglia in self.discendi(record, lev=1): #cerco concordanze
                    try:
                        if ((record not in concordanze) and
                            (elemento==foglia or elemento in foglia)):
                            if isdict: concordanze.append(conv([record]))
                            else: concordanze.append(record)
                            break
                    except TypeError: pass
        return concordanze
    def elenca(self):
        """
        restituisce in una lista ogni singolo elemento dei nostri dati
        
        Returns
        -------
        list
            ogni elemento ha la stesso standard della struttura dati scelta
        """
        dati = self.importa_dati()
        conv = type(dati)
        lista = []
        if isinstance(dati, dict):
            lista = [conv([d]) for d in dati.items()]
        else:
            lista = [conv(d) for d in dati]
        return lista

    def discendi(self, val=None, stampa=False, unkn_iter=False, lev=0, schema=None, valida=True):
        """
        percorre i tipi di dati contenitori e restitusice quelli scalari (le
        stringhe sono trattate come scalari).
        non è penato per essere omnicomprensivo ma supportare i tipi
        
        Parameters
        ----------
        val : qualsiasi tipo standard, optional
            stringhe, boleani, liste, dizionari... e è specificato None
            importa i dati memorizzati, by default None
        stampa : bool, optional
            durante la discensione stampa elemento e profondita
        unkn_iter: bool, optional
            se è vera prova ad iterare nei tipi di dato contenitori sconosciuti
            altrimenti li restituisce come fossero scalari
        lev : int, optional
            variabili interna di lavoro che rappresenta i livello
            di profondità raggiunto, by default 0
        i: int, optional
            contantore che rappresenta l'idice dell'elemento nello schema,
            by default 0
        schema : dict, optional
            dizionario contenente nello stesso ordine i tipi dei dati nella
            struttura da traversare. Lasciando il valore di default None viene
            creato un dizionario dei tipi durante la discesa e restituito in
            output, invece passando lo schema la struttura dati viene validata
            durante la discesa e raisato un TypeError su mancata corrispondenza
            by default None
        valida : bool, optional
            flag che serve a decidere se validare o meno, il suo funzionamento è
            autoregolato, si attiva solo quando si passa uno schema altrimenti
            si disattiva (quando lo schema è None, quindi al max al primo avvio).
            Si potrebbe ancora volerlo usare a mano nel caso si passi uno schema
            ma non si voglia validarlo (e non mi vengono motivi in mente per 
            fare una cosa del genere), by default True 
        
        Yields
        -------
        tipi scalari
            restituisce tipi non più scomponibili
        """
        if schema is None:
            # se si passa None come schema, non avviene validazione e viene collezionato
            # lo schema per futuri utilizzi. (schema può essere none solo all'inizio)
            # se invece si passa uno schema vuol dire che mi aspetto la validazione
            # quindi la validazione rimane True.
            schema = list()             #self.schema_last diventa una nuova lista,
            self._schema_last = schema  #self.schema rimane invariato
            valida = False
        # if val is None and lev==0:
        if lev == 0:        #solo al primo giro e se non si parte da un livello > 0
            if valida:      #se la validazione è attiva avvio un iteratore sullo schema
                class Validiter:
                    #iteratore che mantiene in memoria i dati precedenti, lo faccio
                    #così evito di usare variabili della classe principale
                    def __init__(self, schema):
                        self.prev = None
                        self._next = (-1,0, schema[0][1])
                        self.schema_iter = iter((i,l,t) for i,(l,t) in enumerate(schema))
                    def __next__(self): #classe iteratore
                        self.prev = self._next  #prima di uno stopiterator questa viene
                        self._next = next(self.schema_iter) #eseguita
                        return self._next
                self._schema_last = schema  #salvo l'ultimo schema passato
                self._record_last_len = 0   #lung ultimo record per validazione
                schema = Validiter(schema)

            if val is None: #importa i dati e attiva la sstanza se si passa None a val
                stampa = True
                val = self.importa_dati()

        if valida:  #valida schema
            try:
                it_ind, it_lev, it_tip = next(schema)
                self._record_last_len += 1
                if not isinstance(val, it_tip) or it_lev != lev:
                    raise TypeError('corrispondenza invalida')
            except (TypeError, StopIteration):
                it_ind, it_lev, it_tip = schema.prev
                it_ind += 1
                it_val = self._schema_last[it_ind:it_ind+1]
                it_lev, it_tip = it_val[0] if it_val else ("outofrange",)*2
                er = f"Validazione Fallita, schema non corrispondente:\n"\
                     f"schema tipo:{it_tip} pos:{it_ind} lev:{it_lev}\n"\
                     f"record tipo:{type(val)} val:{val}" 
                raise TypeError(er) 
        else:   #crea scema (in assenza di validazione)
            schema.append((lev,type(val)))

        if isinstance(val, self.SCALAR):
            if stampa: print("."*lev, val, sep='')
            yield val
        elif isinstance(val, dict):
            for k,v in val.items():
                if stampa: print("."*(lev+1), k, sep='')
                yield k
                yield from self.discendi(v, stampa, unkn_iter, lev+1, schema, valida)
        elif isinstance(val, self.CONTEN):
            for v in val:
                yield from self.discendi(v, stampa, unkn_iter, lev+1, schema, valida)
        else: #tipo di dato sconosciuto
            try:
                if unkn_iter:
                    for v in val:
                        yield from self.discendi(v, stampa, unkn_iter, lev+1, schema, valida)
                else: raise TypeError('unkn_iter è falso')
            except TypeError:
                if stampa: print("."*lev, val, sep='')
                yield val
    def valida(self, val):
        result = list(self.discendi(val, schema=self.schema))
        lenv = self._record_last_len
        lens = len(self.schema)
        if lenv != lens:
            er =  f"Validazione Fallita, schema non corrispondente:\n"\
                  f"{lenv} elementi su un totale di {lens}"
            raise TypeError(er)
        return list(self.discendi(val, schema=self.schema))

    def timestamp(self):
        """
        restituisce una stringa della data rispettando il formato specificato
        durante l'istanziamento della classe
        
        Returns
        -------
        string
            data attuale formato stringa
        """
        #ho aggiunto i millisecondi al formato standard altrimenti salvataggi
        #in successione in <1 si sovrascrivono (nei dizionari), alternativa
        #era aggiungere un numero progressivo solo alla bisogna, ma non sapevo
        #in che punto del programma mettere una cosa così # int("0" + "1234"[2:])
        return datetime.now().strftime(self.dateform)
    def timestamp_to_date(self, timestamp):
        """
        riconverte una stringa nel formato specificato all'istanziamento in un tipo
        di dato del tempo
        
        Parameters
        ----------
        timestamp : string
            data nel formato tempo predefinito durante l'istanziamento della classe
        
        Returns
        -------
        time.struct_time
            formato di tempo manipolabile
        """
        return datetime.strptime(timestamp, self.dateform)

class Record:
    """
    classe di supporto per poter avere oggetti e non stringhe combo box
    di pysimplegui. Viene ritornato __str__ 
    """
    prefun = GENIN
    presub = ''

    @property
    def record(self):
        return {self.key : [self.fun, self.regex, self.flags, self.text, self.count, self.replace]}
    @record.setter
    def record(self, dati):
        key = next(iter(dati.keys()))
        dati = dati[key]
        self.key     = key
        self.fun     = dati[0]
        self.regex   = dati[1]
        self.flags   = dati[2]
        self.text    = dati[3]
        self.count   = dati[4]
        self.replace = dati[5]

    def __init__(self, *record):
        """
        Parameters
        ----------
        record : args
            dizionario standard per la memorizzazione dei dati se monovalore
            regex, flags e testo nel caso di tre valori (chiave generata)
        """
        if len(record) == 1:
            record = record[0]
            self.record = record
        else:
            att = ['key', 'fun', 'regex', 'flags', 'text', 'count', 'replace']
            rec = [store.timestamp()] + list(record) + [""]*(len(att)-1-len(record))
            for a,v in zip(att, rec):
                if a == 'fun' and not v: v = "findall"  #valori di default per
                elif a == 'count' and not v: v = 0    #evitare i campi vuoti
                self.__setattr__(a,v)
    def __str__(self):
        return self.record[self.key][1]
    def __eq__(self, other):
        """
        vero se gli elementi sono uguali (le chiavi non sono importanti)

        Parameters
        ----------
        other : Record
            un altro record con cui fare il confronto
        
        Returns
        -------
        bool
            se il contenuto dei record è lo stesso, senza la data
        """
        return all(a==b for a,b in zip(self.record.values(), other.record.values()))
    def is_empty(self):
        """return True if the record is void"""
        return not any((self.regex, self.flags, self.text, self.count, self.replace))
    def is_saved(self):
        """return True if record is already saved"""
        return any(self == Record(s) for s in store.elenca())
    @classmethod
    def capture(cls, values):
        """
        return a Record object from the current data showed in the gui
        
        Parameters
        ----------
        values : values from Window.read()
            data returned from Window of pysimplegui
        
        Returns
        -------
        Record
            current data object
        """
        fun = values['regfun']
        regex = values['regbox'][:-1]
        flags = ''.join([f for f in FLAGS_CMB  if values[f]])
        text = values['text'][:-1]
        count = values['cntbox']
        count = int(count) if count.isdecimal() else 0
        rep = values['subbox']
        replace = values['subbox'][:-1] if values['subbox'] != "None\n" else '' #X BUG MULTILINE
        return cls(fun, regex, flags, text, count, replace)
    @classmethod
    def gui_adapt(cls, window, record):
        if record.fun != cls.prefun:                #se cambia funzione
            # print(f"{cls.prefun} > {record.fun}")
            if record.fun in ("sub", "subn"):       #in una sub
                if cls.prefun in ("sub", "subn"):   #ed era una sub
                    cls.presub = record.replace     #registro il valore per precedente
                else: 
                    if cls.prefun != "split":
                        window['cntbox'].update(disabled=False)
                        window['cntbox'].update(text_color="black")
                    window['subbox'].update(disabled=False)
                    window['subbox'].update(text_color="black")
                    window['subbox'].update(cls.presub)  #X BUG MULTILINE
            elif record.fun == "split":
                if cls.prefun in ("sub", "subn"):
                    cls.presub = ""
                    window['subbox'].update("")
                    window['subbox'].update(text_color="#d9d9d9")
                    window['subbox'].update(disabled=True)
                window['cntbox'].update(disabled=False)
                window['cntbox'].update(text_color="black")
            else:
                if cls.prefun in ("split", "sub", "subn"):
                    window['cntbox'].update("0")
                    window['cntbox'].update(text_color="#d9d9d9")
                    window['cntbox'].update(disabled=True)
                    if cls.prefun != "split":
                        cls.presub = ""
                        window['subbox'].update("")
                        window['subbox'].update(text_color="#d9d9d9")
                        window['subbox'].update(disabled=True)
            cls.prefun = record.fun
    @classmethod
    def capturegex(cls, values, window):
        """
        capture current data from gui and execute a debounced regex
        
        Parameters
        ----------
        values : values of pysimplegui Window.read()
            data captured from the gui
        
        Returns
        -------
        list or None
            list of regex occurrencies
        """
        r = cls.capture(values)
        cls.gui_adapt(window, r)
        flags = [f for f in FLAGS_CMB  if values[f]]
        flags = sum([eval("re."+f) for f in flags])
        return regexer(r.fun, r.text, r.regex, flags, r.count, r.replace)
    @classmethod
    def show(cls, window, *record):
        """
        show specified record ok the interface
    
        Parameters
        ----------
        window : Window
            istance of pysimplegui
        record : Record or data
            it is ok to pass a Record object or a record data
        """
        if len(record) == 1 and isinstance(record[0], Record):
            record = record[0]
        else: record = Record(*record)
        cls.gui_adapt(window, record)
        window['regfun'].update(record.fun)
        window['regbox'].update(record.regex)
        for f in FLAGS_CMB :
            window[f].update(f in record.flags)
        window['text'].update(record.text)
        window['cntbox'].update(record.count)
        window['subbox'].update(record.replace)
    @classmethod
    def updatelist(cls, window, record=None):
        """
        update the list of record on the interface,
        if record is a saved record, preselect it in the list
        
        Parameters
        ----------
        window : sg.Window
            the instnced windows of pysimplegui
        record : Record, optional
            one save, by default None
        
        Returns
        -------
        [Record, Record...]
            updated list of saved record
        """
        if record is None or not record.is_saved(): record = Record()
        saved = [Record(r) for r in store.elenca()]
        window['savedlist'].update(record, saved)
        return saved

def throttle_debounce(tic, wait):
    """
    decoratore che posticipa l'esecuzine della funzione decorata, si
    sottointende l'uso lanciando la funzione ad intervalli regolari.
    la funzione decorata viene avviata solo quando non ci sono più
    cambiamenti da un numero di volte di tic in wait.
    
    Parameters
    ----------
    tic : int
        la duranta di un intervallo di scansione
    wait : int
        il delay di attesa, è da considerarsi più come numero tic
        che di sencondi che devono passare (a meno che un tic==1sec)
    
    Returns
    -------
    function
        decorated function
    """
    def decorate(delayedfun):
        _start = 0
        _value = None
        _lst_e = None
        def wrap(*args, **kwargs):
            nonlocal _start, _value, _lst_e
            val = (args, kwargs)
            if val != _lst_e:       #ho fatto una modifica
                _start = 0
                _lst_e = val
            elif _lst_e != _value:  #ho smesso di fare modifiche
                _start += tic
                if _start >= wait:  #ho smesso per n volte
                   _value = val
                   _start = 0
                   result = delayedfun(*args, **kwargs)
                   return result
        return wrap
    return decorate
@throttle_debounce(DETAIL, DELAY)
def regexer(fun, text, regex, flags=0, count=0, replace=""):
    #non compilo la regex perché i metodi usano una già incorporata
    if fun in ('fullmatch', 'match', 'search'):
        result = getattr(re, fun)(regex, text, flags)
        if result is not None:
            result = result.regs
            if result == ((0, 0),): result = ('',)
        else: result = ()
    elif fun == 'findall':
        result = re.findall(regex, text, flags)
    elif fun == "split":
        result = re.split(regex, text, count, flags)
    elif fun in ('sub', 'subn'):
        result = [getattr(re, fun)(regex, replace, text, count, flags)]
    else:
        result = [""]
    return result
    
sg.theme('BrightColors')
store = Appendsave(STD_REGEX)
saved = [Record(r) for r in store.elenca()]
layout = [
    [
        sg.Combo(GENRE, GENIN, (9,1), key='regfun', font=SFONT, readonly=True),
        # sg.Text("", size=(0,0)),
        sg.Checkbox("I", key="I", font=SFONT, tooltip="IGNORECASE"),
        sg.Checkbox("L", key="L", font=SFONT, tooltip="LOCALE (only with byte pattern)", disabled=True),
        sg.Checkbox("M", key="M", font=SFONT, tooltip="MULTILINE"),
        sg.Checkbox("S", key="S", font=SFONT, tooltip="DOTALL"),
        sg.Checkbox("U", key="U", font=SFONT, tooltip="UNICODE (default if not ascii)", disabled=True),
        sg.Checkbox("X", key="X", font=SFONT, tooltip="VERBOSE"),
        sg.Checkbox("A", key="A", font=SFONT, tooltip="ASCII"),
        sg.VerticalSeparator(),
        sg.Button('?', key='help', font=SFONT, tooltip="help"),
    ],    
    [   
        sg.InputText("0", (CH_1_10,1), True, key="cntbox", justification='right',
                     visible=True, background_color="#d9d9d9", text_color="#d9d9d9"), 
        sg.VerticalSeparator(pad=(0,1)),
        sg.Multiline(size=(CH_9_10,1), disabled=False, key="subbox", autoscroll=True,
                     visible=True, background_color="#d9d9d9", text_color="#d9d9d9"),
    ],
    [sg.Multiline(key="regbox", size=(CH_FLEN,3), autoscroll=True, focus=True)],
    [sg.Multiline(key="text", size=(CH_FLEN,6), autoscroll=True)],
    [sg.Multiline(key="result", size=(CH_FLEN, 6), autoscroll=True, disabled=True)],
    [   
        sg.Button('N', key='new', tooltip="new"),
        sg.Button('S', key='save', tooltip="save"),
        sg.Button('L', key='load', tooltip="load"),
        sg.Button('D', key='dele', tooltip="delete"),
        sg.Combo(saved, size=(CH_SLEN,1), key='savedlist', readonly=True),
    ],
]
#enter_submits non funziona, almeno non in accoppiata con do_not_clear
#multiline ha sempre un \n alla fine anche se è vuoto
#Output cattura anche stder e stdout!

#region calcolo posizione finestra quando la creo 
if sg.port == "PySimpleGUI":
    SLOC, SSIZ, SDEC = preset_dim(sg) 
    offset = map(sum, zip(SLOC, map(lambda n: n//4, SSIZ)))
    window = sg.Window("rg", layout, location=offset,
                        font=("Default", 20))#, element_justification="right")
elif sg.port == "PySimpleGUIWeb":
    window = sg.Window("rg", layout, font=BFONT)
#endregion
#window['savedlist'].expand(True) #non funge, come espandere combo?
window.finalize(); window['subbox'].update(disabled=True) #X BUG MULTILINE


def popup(mex, y_n=False, scr=False, font=BFONT, pos=window, siz=(CH_FLEN+1,CH_FWID), title=''):
    """
    shorcut to preconfigured popup format
    
    Parameters
    ----------
    mex : string
        message to show
    y_n : bool, optional
        if popup have yes-no buttons, by default False
    scr : bool, optional
        if popup is scrollable (disable y_n), by default False
    font : tuple, optional
        font format of pysimplegui, by default BFONT
    pos : (int,int), optional
        upper-left position of the popup, can be windows object and
        reflect topleft of window, or PySimpleGUI module and reflect
        topleft of desktop, by default window
    size : (int,int), optional
        dimension of popup in character, valid only for scrollable popup,
        by default hardcoded to window dimension 
    Returns
    -------
    bool
        True of False
    """
    if not isinstance(pos, tuple):
        pos = tuple(a-b for a,b in zip(pos.current_location(), SDEC)) 
    if scr:
        res = sg.popup_scrolled(mex, title=title, font=font, location=pos, size=siz, non_blocking=True, keep_on_top=True)
    else:
        poop = sg.popup_yes_no if y_n else sg.popup
        res = poop(mex, font=font, location=pos, keep_on_top=True)
    return True if res == "Yes" else False


while True:
    #ogni secondo rilascio uno stato
    event, values = window.read(timeout=DETAIL*1000)  #un controllo al sec
    #dovrebbe togliere il focus quando si switcha con tab, ma...
    # if sg.name == "PySimpleGUI":
        # window['result'].Widget.config(takefocus=0)
    if event is None:   break       #quit dal programma
    elif event == "__TIMEOUT__":    #ad ogni cadenza
        try: result = Record.capturegex(values, window) #meglio accettare record da regexer?
        except re.error: result = ""
        if result is not None:
            if result and any(result):
                lr = len(str(len(result)))
                result = [f"{n:0{lr}}) {s}" for n, s in enumerate(result,1)]
                result = "\n".join(result)
                window['result'].update(result)
            else:
                window['result'].update('')
    elif event == "help":
        mex =   r"Special Character (_ for cont)" + "\n" \
                r".   all except newline(dotall)" + "\n" \
                r"^   start of the string" + "\n" \
                r"$   end of the string" + "\n" \
                r"*   0 or more greedy (*? notg)" + "\n" \
                r"+   1 or more greedy (+? notg)" + "\n" \
                r"?   0 or 1    greedy (?? notg)" + "\n" \
                r"{,} opt from,to ({,}? notgree)" + "\n" \
                r"\   escape special seq or char" + "\n" \
                r"[_]  set of char ([^] complem)" + "\n" \
                r"|   alternative" + "\n" \
                r"(_)  grouping match \id access" + "\n" \
                r"(?_)inline flag, _ for iLmsuxa" + "\n" \
                r"(?:_)nogroup match, no accessb  " + "\n" \
                r"(?P<name>_)groupmtch \name acc" + "\n" \
                r"(?P=name_)match previous again" + "\n" \
                r"(?#_) ignored comment (flag x)" + "\n" \
                r"(?=_)if next is _ noconsum str" + "\n" \
                r"(?!_)if next is not _" + "\n" \
                r"(?<=_)if preceded by _ fix len" + "\n" \
                r"(?<!_)if not prec by _ fix len" + "\n" \
                r"(?(id/name)yes|no)alternative?" + "\n" \
                r"" + "\n" \
                r"Special Sequence (escp with \)" + "\n" \
                r"\n  number, matches grou again" + "\n" \
                r"\A  match only at start of str" + "\n" \
                r"\Z  match only at end of strin" + "\n" \
                r"\b  m. empty strn outside word" + "\n" \
                r"\B  m. empty strng inside word" + "\n" \
                r"\d  all digits, in ascii [0-9]" + "\n" \
                r"\D  all non digits equiv [^\d]" + "\n" \
                r"\s  allspace,asci[ \t\n\r\f\v]" + "\n" \
                r"\S  all non wspace equiv [^\S]" + "\n" \
                r"\w  all alphanum,a[a-zA-Z0-9_]" + "\n" \
                r"\W  \w complement, equiv [^\w]" + "\n" \
                r"\\  literal backslash" + "\n" \
                r"" + "\n" \
                r"Py escape sequence (- no work)" + "\n" \
                r"\\   \ backslash, like regex" + "\n" \
                r"\'   ' singlequote" + "\n" \
                r'\"   " doublequote' + "\n" \
                r"\a -   ascii bell" + "\n" \
                r"\b -   backspace sub regex \b" + "\n" \
                r"\f -   line feed" + "\n" \
                r"\n     newline" + "\n" \
                r"\r -   return carriage" + "\n" \
                r"\t     tabulation horizzontal" + "\n" \
                r"\v -   tabulation vertical" + "\n" \
                r"\ooo   octal seq \101 == A" + "\n" \
                r"\xhh   hexad seq  8b \x41 == A" + "\n" \
                r"\uxxxx hexad 16b \u0041 == A" + "\n" \
                r"\uxxxxxxxx h32b\u00000041 == A" + "\n" \
                r"\N{name} - unicode name {tab}" + "\n" \
                r"\newline - literally newline" + "\n" \
                r"" + "\n" \
                r"Flag Description (- disabled)" + "\n" \
                r"I   ignore case sensitive" + "\n" \
                r"L - \w\W\b\B locale dependent" + "\n" \
                r"M   ^ $ matched every newline" + "\n" \
                r"S   . match any char also \n" + "\n" \
                r"U - unicode, default no ascii " + "\n" \
                r"X   ignore wspace and comment" + "\n" \
                r"A   \w\W\b\B\d\D ascii setted" + "\n" \
                r"    " + "\n" \
                r"Methods Description" + "\n" \
                r"findall find all occurrencies" + "\n" \
                r"fullmatch match complete strin" + "\n" \
                r"match match string from start" + "\n" \
                r"search search pattern in text" + "\n" \
                r"split split strin with pattern" + "\n" \
                r"sub sub pattern with replacmnt" + "\n" \
                r"subn like sub but with total"
        popup(mex, scr=True, title="help")
    elif event == "new":
        recnew = Record.capture(values)
        oksv = True
        if not recnew.is_empty():
            if not recnew.is_saved():
                oksv = popup("The current work is not saved, procede anyway?", True)
        if oksv:
            Record.show(window)
            Record.updatelist(window)
    elif event == "save":
        recnew = Record.capture(values)
        if not recnew.is_empty():
            oksv = True
            if recnew.is_saved():
                oksv = popup("identical save already present, proced anyway?", True)      
            if oksv:
                recsav = values['savedlist']
                if isinstance(recsav, Record) and popup("overwrite selected save?", True):
                    store.aggiorna(recsav.key, recnew.record)
                else:
                    store.salva(recnew.record)
                Record.updatelist(window, recnew)
        else:
            popup("the record is empty!")
    elif event == "load":
        recsav = values['savedlist']
        if isinstance(recsav, Record):
            recnew = Record.capture(values)
            if recnew != recsav:
                oksv = True
                if not recnew.is_empty() and not recnew.is_saved():
                    oksv = popup("The current work is not saved, procede anyway?", True)
                if oksv:
                    Record.show(window, recsav)
            else:
                popup("you load save with same content")
        else:
            popup("you haven't select any save")
    elif event == "dele":
        recsav = values['savedlist']
        if isinstance(recsav, Record):
            if popup(f"delete?: {recsav}", True):
                store.cancella(recsav.key)
                Record.updatelist(window)
        else:
            popup("No save selected")

window.close()

### SAVE ###
#{}
### FINE ###