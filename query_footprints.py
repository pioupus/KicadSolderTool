#!/usr/bin/env python
import pcbnew
import sys


def test_of_module_exists_on_other_side(first_side, other_side):
    for modul_first in first_side:
        val = modul_first['val']
        for modul_other in other_side:
            if val == modul_other['val']:
                modul_first['other_side'] = True
                break;
    return first_side
            

def compare(a,b):
    #print(str(a)+str(b))
    if a['area'] == b['area']:
        if a['val'] == b['val']:
            if a['ref'] > b['ref']:
                #print (">")
                return 1
            else:
                #print ("<")
                return -1
        if a['val'] > b['val']:
            #print (">")
            return 1
        else:
            #print ("<")
            return -1

    elif a['area'] > b['area']:
        #print (">")
        return 1
    else:
        #print ("<")
        return -1

def query_and_sort(filename):
    pcb = pcbnew.LoadBoard(filename)

    modules = pcb.GetModules()
    module_items_top =[]
    module_items_bot =[]
    for mod in modules:
        smalles_area = sys.maxint;
        for pad in mod.Pads():
            area = pad.GetSize().x/1000.0 * pad.GetSize().y/1000.0
            if area < smalles_area:
                smalles_area = area
        #print("smallest pad size for part "+mod.GetReference()+": "+str(smalles_area) +" "+str(mod.IsFlipped()))
       # print(mod.GetValue())
        item = {'ref':mod.GetReference(),'area':smalles_area,'bot':mod.IsFlipped(),'x':mod.GetPosition()[0],'y':mod.GetPosition()[1], 'val':mod.GetValue(), 'other_side':False}
        if mod.IsFlipped():
            module_items_bot.append(item)
        else:
            module_items_top.append(item)
    module_items_bot = sorted(module_items_bot, cmp = lambda x,y:compare(x,y))
    module_items_top = sorted(module_items_top, cmp = lambda x,y:compare(x,y))


    if len(module_items_bot) > len(module_items_top):
        module_items_bot = test_of_module_exists_on_other_side(module_items_bot,module_items_top)
        
        module_items_bot.extend(module_items_top)
        return module_items_bot
    else:
        module_items_top = test_of_module_exists_on_other_side(module_items_top,module_items_bot)
        module_items_top.extend(module_items_bot)
        return module_items_top


if __name__ == '__main__':
    filename = "/home/arne/programming/projekte/windrad/kicad/revB/windrad.kicad_pcb"
    items = query_and_sort(filename)
    print(items)
 