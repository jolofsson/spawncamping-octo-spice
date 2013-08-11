import Tkinter
from math import *
import random
from random import shuffle
import time
import sys
#import _thread



# This is the class for the window displaying the tortoise and its world
class TortoiseFrame(Tkinter.Frame):

    tort_img_canvas=False
    
    def __init__(self,grid_size,simulation_speed,tortoise_brain):
        Tkinter.Frame.__init__(self,None)
        self.sim_speed = simulation_speed
        self.master.title('Tortoise World')
        self.canvas = Tkinter.Canvas(self,width=40*grid_size,height=40*grid_size+60,bg='white')
        self.canvas.pack(expand=1,anchor=Tkinter.CENTER)
        self.pack()
        self.tkraise()
        self.dog_canvas=None
        # Create the world
        self.tw = TortoiseWorld(grid_size,tortoise_brain)
        # Load images
        self.images = {}
        for img in ['wall','lettuce','pond','ground','stone','tortoise-n','tortoise-s','tortoise-w','tortoise-e','tortoise-dead','dog',]:
            self.images[img]=Tkinter.PhotoImage(file='./'+img+'.gif')
        # Draw environment
        for y in range(grid_size):
            for x in range(grid_size):
                self.canvas.create_image(x*40,y*40,image=self.images['ground'],anchor=Tkinter.NW)                
                if self.tw.worldmap[y][x] != 'ground':
                    self.canvas.create_image(x*40,y*40,image=self.images[self.tw.worldmap[y][x]],anchor=Tkinter.NW)
        # Set up a table for handling the tortoise images to use for each self.direction
        self.direction_img_table=['tortoise-n','tortoise-e','tortoise-s','tortoise-w']
        # Set up text item for drawing info
        self.text_item=self.canvas.create_text(40,(grid_size)*40,anchor=Tkinter.NW, text='')
        self.after(1,self.step)
        
    def step(self):
        # Update time
        self.tw.curr_time += 0.1
        # Move the tortoise 
        if self.tw.curr_time >= self.tw.next_time:
            self.tw.step_tortoise()
            # Update ground if necessary
            if self.tw.update_current_place:
                self.canvas.create_image(self.tw.xpos*40,self.tw.ypos*40,
                                         image=self.images[self.tw.worldmap[self.tw.ypos][self.tw.xpos]],anchor=Tkinter.NW)
            # Redraw tortoise
            tort_image=self.direction_img_table[self.tw.direction]
            if self.tw.health <= 0: tort_image='tortoise-dead'
            if self.tort_img_canvas != False:
                self.canvas.delete(self.tort_img_canvas)
            self.tort_img_canvas = self.canvas.create_image(self.tw.xpos*40,self.tw.ypos*40,image=self.images[tort_image],anchor=Tkinter.NW)
        # Move the dog
        if self.tw.curr_time >= self.tw.next_dog_time:
            self.tw.step_dog()
            if self.dog_canvas != None:
                self.canvas.delete(self.dog_canvas)
            self.dog_canvas = self.canvas.create_image(self.tw.dog_position[0]*40,self.tw.dog_position[1]*40,image=self.images['dog'],anchor=Tkinter.NW)
        # Display text information
        self.canvas.itemconfigure(self.text_item, text='Action: %-7s Eaten: %2d Time: %4d Score: %3d Drink Level %2d   Health %2d' %
                                      (self.tw.action, self.tw.eaten, int(self.tw.curr_time), self.tw.score, self.tw.drink_level, self.tw.health))
        if not self.tw.action == 'stop' and self.tw.curr_time <= self.tw.max_time:
            self.after(int(200/self.sim_speed),self.step)





class TortoiseWorld():    
    max_drink = 100
    max_health = 100
    max_time = 1000
    xpos,ypos=1,1
    drink_level=0
    eaten=0
    curr_time=0.0
    direction=0 #north=0, east=1, south=2, west=3
    worldmap=None
    action = 'None'
    next_time = 0
    next_dog_time = 0
    update_current_place=False
    score = 0
    health = max_health
    pain = False


    def __init__(self,grid_size,tortoise_brain):
        self.dog_position = [grid_size-2,grid_size-5]
        self.dog_dir = [0,0]
        self.direction_table=[(0,-1),(1,0),(0,1),(-1,0)]
        self.drink_level=self.max_drink
        self.create_world_map(grid_size)
        self.grid_size=grid_size
        self.tortoise_brain = tortoise_brain
        self.health=self.max_health
        self.pain = False

    def step_tortoise(self):
        self.curr_time = self.next_time
        time_change = 4-(3*float(self.drink_level)/self.max_drink)
        self.next_time = self.curr_time + time_change
        self.update_current_place=False
        dx,dy=self.direction_table[self.direction]
        # Sensing
        ahead = self.worldmap[self.ypos+dy][self.xpos+dx]
        here = self.worldmap[self.ypos][self.xpos] 
        free_ahead = (ahead not in ['stone','wall'])
        lettuce_ahead = (ahead == 'lettuce')
        lettuce_here = (here == 'lettuce')
        water_ahead = (ahead == 'pond')
        water_here = (here == 'pond')
        # See in which direction the dog is
        dgx, dgy = self.dog_position[0] - self.xpos, self.dog_position[1] - self.ypos
        rota,rotb = [(0,+1),(+1,0),(0,-1),(-1,0)],[(-1,0),(0,+1),(+1,0),(0,-1)]
        rel_x = rota[self.direction][0]*dgx + rotb[self.direction][0]*dgy
        rel_y = rota[self.direction][1]*dgx + rotb[self.direction][1]*dgy
        # Tortoise thinks!
        self.action = self.tortoise_brain.think(free_ahead,lettuce_ahead,lettuce_here,water_ahead,water_here,self.drink_level,rel_x,rel_y)
        self.pain = False
        # Perform action
        if self.action=='left':
            self.direction= (self.direction-1)%4
            self.drink_level = max(self.drink_level-2,0)
        elif self.action=='right':
            self.direction= (self.direction+1)%4
            self.drink_level = max(self.drink_level-2,0)
        elif self.action=='forward':
            if free_ahead:
                self.xpos += dx
                self.ypos += dy
            else:
                self.health -= 1
                self.pain = True
            self.drink_level = max(self.drink_level-2,0)
        elif self.action=='eat' and lettuce_here:
            self.drink_level = max(self.drink_level-1,0)
            self.eaten += 1
            self.worldmap[self.ypos][self.xpos] = 'ground'
            self.update_current_place=True
        elif self.action=='drink' and water_here:
            self.drink_level=self.max_drink
        elif self.action=='wait':
            self.drink_level = max(self.drink_level-1,0)
        # Update score
        if self.drink_level <= 0 or self.health <= 0:
            if self.drink_level <= 0: print("You died of thirst!")
            else: print("You died!")
            self.action="stop"
            self.health=0
            self.pain=True
        self.score = self.eaten*10-int(sqrt(self.curr_time/100))*10

    def step_dog(self):
        self.next_dog_time += 1.25
        # If the dog steps on the tortoise it hurts
        if self.dog_position[0] == self.xpos and self.dog_position[1] == self.ypos:
            self.health = self.health - 5
        # The dog keeps moving - if possible and unless it decides to turn
        nx = self.dog_position[0]+self.dog_dir[0]
        ny = self.dog_position[1]+self.dog_dir[1]
        if nx>=1 and ny >= 1 and nx < self.grid_size-1 and ny < self.grid_size-1 and self.worldmap[ny][nx] not in ['stone','wall'] and random.randint(0,3) != 0:
            self.dog_position[0]=nx
            self.dog_position[1]=ny
        else:
            # Steer dog randomly - or towards the turtle
            if random.randrange(0,3) == 0: self.dog_dir=[(1,0),(-1,0),(0,1),(0,-1)][random.randrange(0,4)]
            elif random.randrange(0,2) == 0:
                if self.xpos > self.dog_position[0]: self.dog_dir=(1,0)
                elif self.xpos < self.dog_position[0]: self.dog_dir=(-1,0)
                elif self.ypos > self.dog_position[1]: self.dog_dir=(0,1)
                elif self.ypos < self.dog_position[1]: self.dog_dir=(0,-1)
                else: self.dog_dir=(0,0)
            else:
                if self.ypos > self.dog_position[1]: self.dog_dir=(0,1)
                elif self.ypos < self.dog_position[1]: self.dog_dir=(0,-1)
                elif self.xpos > self.dog_position[0]: self.dog_dir=(1,0)
                elif self.xpos < self.dog_position[0]: self.dog_dir=(-1,0)
                else: self.dog_dir=(0,0)
        
    # Build a random world map 
    def create_world_map(self,grid_size):
        self.worldmap = [ [  ((y in [0,grid_size-1] or  x in [0,grid_size-1]) and 'wall') or 'ground'
                        for x in range(grid_size) ] for y in range(grid_size) ]
        # First put out the stones randomly
        for i in range(int((grid_size-2)**2/6)):
            ok=False
            while not ok: 
                (x,y) = random.randint(1,grid_size-1), random.randint(1,grid_size-1)
                if self.worldmap[y][x] == 'ground':
                    count_stones = 0
                    count_walls = 0
                    # Check that the stone will not be adjacent to two other stones,
                    # or one other stone and a wall.
                    # This is to prevent the appearance of inaccessible areas.
                    for dx in [-1,0,1]:
                        for dy in [-1,0,1]:
                           if self.worldmap[y+dy][x+dx] == 'stone':
                               count_stones += 1
                           if self.worldmap[y+dy][x+dx] == 'wall':
                               count_walls += 1
                    if count_stones == 0 or (count_stones <= 1 and count_walls == 0):        
                        self.worldmap[y][x] = 'stone'
                        ok=True
                    elif random.random() <= 0.1:
                        ok=True
        # Then put out the lettuces randomly
        for i in range(int((grid_size-2)**2/6)):
            ok=False
            while not ok: 
                (x,y) = random.randint(1,grid_size-1), random.randint(1,grid_size-1)
                if self.worldmap[y][x] == 'ground':
                    self.worldmap[y][x] = 'lettuce'
                    ok=True
        # Finally put out the water ponds randomly
        for i in range(int((grid_size-2)**2/15)):
            ok=False
            while not ok: 
                (x,y) = random.randint(1,grid_size-1), random.randint(1,grid_size-1)
                if self.worldmap[y][x] == 'ground':
                    self.worldmap[y][x] = 'pond'
                    ok=True



# The sensing input consists of the following parameters:
# - free_ahead (not blocked to rock or wall)
# - lettuce_ahead (in square in front of tortoise)
# - lettuce_here (can eat)
# - water_ahead (in square in front of tortoise)
# - water_here (can drink)
# - drink level (integer) 
# - dog_forward  (how many cells in front of us the dog is at)
# - dog_right  (how many cells to the right of us the dog is at)
# The available actions are:
#  - 'eat' (if on lettuce)
#  - 'drink' (if on water)
#  - 'left' (relative to current heading)
#  - 'right' (relative to current heading)
#  - 'forward' (relative to current heading)
#  - 'wait',
# -  'stop' (terminate simulation)

class TortoiseBrain:
    agent_map = [] #Karta som sk�ldpaddan skall g� igenom
    create_map = True #Kontroll s� inte kartan tas bort n�r programmet k�rs
    pond_list = [] #Lista d�r koordinater till alla 'ponds' sparas i
    unexplored_area = [] #Lista d�r koordinater till alla outforskade omr�den sparas i
    area_found = True #Kontroll n�r nya koordinater skall tas fram till sk�ldpaddan att g� till
    length = 15 #Variabel som h�ller koll p� avst�ndet till n�rmsta vattenk�lla (pond)
    map_size = 15 #Kartans storlek
    xpos = 1 #Sk�ldpaddans startposition
    ypos = 1
    direction=0 #norr=0, öst=1, syd=2, väst=3
    direction_table=[(0,-1),(1,0),(0,1),(-1,0)] #Addera alt subtrahera x, y-koordinater beroende p� �t vilket h�ll sk�ldpaddan pekar
    ws = [] #Lista p� koordinater till n�rmsta vattenk�llan (water source)
    goto = () #Tuple som har x,y-koordinater till ett omr�de som �r ok�nt (sk�ldpaddan skall allts� g� dit)
    check_goto = () #Kontrollerar goto-tupeln, att den f�r ett nytt v�rde, annars m�ste en ny position genereras fram
    found_water_src = 0 #Hur m�nga 'ponds' sk�ldpaddan har hittat
    


    def think(self,free_ahead,lettuce_ahead,lettuce_here,water_ahead,water_here,drink_level,dog_forward,dog_right):

        self.update_map() #Funktion som skapar agent_map
        dx, dy = self.direction_table[self.direction] #Lokala variabler f�r v�rden p� �t vilket h�ll sk�ldpaddans snok pekar �t
        
        if drink_level > 95: #Nollst�ller variabeln length till 15 efter att sk�ldpaddan har fyllt p� med vatten
            self.length = 15

        if drink_level < 50 and self.found_water_src > 0: #N�r sk�ldpaddans vattenniv� �r under 50 och en vattenk�lla �r funnen sedan tidigare
            self.area_found = True #S�tter denna till true s� programmet f�r leta reda p� ett nytt omr�de att g� mot fr�n vattenk�llan, detta f�r att f�rhindra ett f�r l�ngt avst�nd
            if self.goto not in self.unexplored_area: #L�gger tillbaka destinations-koordinaterna i 'unknown'-listan igen
                self.unexplored_area.append(self.goto)
            return self.water_source(drink_level,self.ypos,self.xpos) #Anropar funktionen water_source f�r att g� tillbaka till n�rmsta 'pond'
        
        if lettuce_here:
            self.agent_map[self.ypos][self.xpos] = 'lettuce' #Uppdaterar kartan
            if (self.ypos, self.xpos) in self.unexplored_area:
                self.unexplored_area.remove((self.ypos, self.xpos)) #Tar bort omr�det fr�n 'unknown'-listan
            return 'eat'
        elif water_here:
            self.found_water_src += 1 #Vattenk�lla funnen, �kar variabeln
            self.agent_map[self.ypos][self.xpos] = 'pond'
            if (self.ypos, self.xpos) in self.unexplored_area:
                self.unexplored_area.remove((self.ypos, self.xpos)) #Tar bort omr�det fr�n 'unknown'-listan
            if (self.ypos,self.xpos) not in self.pond_list:
                self.pond_list.append((self.ypos,self.xpos))
            if drink_level < 95:
                return 'drink'
        if water_ahead:
            self.found_water_src += 1
            self.agent_map[self.ypos+dy][self.xpos+dx] = 'pond'
            if (self.ypos+dy, self.xpos+dx) in self.unexplored_area:
                self.unexplored_area.remove((self.ypos+dy, self.xpos+dx)) #Tar bort omr�det fr�n 'unknown'-listan
            if (self.ypos+dy,self.xpos+dx) not in self.pond_list:
                self.pond_list.append((self.ypos+dy,self.xpos+dx)) #L�gger till 'ponden' i listan om den inte redan finns d�r
            if drink_level < 90:#En kontroll s� inte sk�ldpaddan fastnar i en loop om det finns tv� 'ponds' brevid varandra och sk�ldpaddan skall sv�nga mellan dessa
                self.ypos += dy
                self.xpos += dx
                return 'forward'
            else:
                return self.explore_map() #Annars anropas funktionen explore_map
        elif lettuce_ahead:
            self.agent_map[self.ypos+dy][self.xpos+dx] = 'lettuce'
            if (self.ypos+dy, self.xpos+dx) in self.unexplored_area:
                self.unexplored_area.remove((self.ypos+dy, self.xpos+dx)) #Tar bort omr�det fr�n 'unknown'-listan
            self.ypos += dy
            self.xpos += dx
            return 'forward'
        elif not free_ahead:
            self.agent_map[self.ypos+dy][self.xpos+dx] = 'stone'
            if (self.ypos+dy, self.xpos+dx) in self.unexplored_area:
                self.unexplored_area.remove((self.ypos+dy, self.xpos+dx)) #Tar bort omr�det fr�n 'unknown'-listan
            return self.explore_map() #Anropar explore_map

        else:
            self.agent_map[self.ypos+dy][self.xpos+dx] = 'ground'
            if (self.ypos+dy, self.xpos+dx) in self.unexplored_area:
                self.unexplored_area.remove((self.ypos+dy, self.xpos+dx)) #Tar bort omr�det fr�n 'unknown'-listan
            return self.explore_map() #Anropar explore_map


    #Funktion som utforskar alla ok�nda st�llen p� kartan (agent_map)
    def explore_map(self): 

        if len(self.unexplored_area) > 0: #Om listan �r st�rre �n 0
            if self.area_found is True:  #N�r denna �r true tas en ny position fram som sk�ldpaddan skall g� mot
                self.check_goto = self.goto #Kontroll att self.goto f�r ett nytt v�rde i for-loopen nedan
                for s in self.unexplored_area:
                    if abs(s[0]-self.ypos) <= 5 and abs(s[1]-self.xpos) <=5: #Begr�nsar vart sk�ldpaddan kan g�, utifr�n sin nuvarande position.
                        self.goto = s
                        self.unexplored_area.remove(s)
                        break
                if self.check_goto == self.goto: #Har ej f�tt n�gon ny position att g� till, detta kan leda till en position som �r l�ngt ifr�n nuvarande tillst�nd
                    for t in self.unexplored_area:
                        if self.agent_map[t[0]][t[1]] != 'stone':
                            self.goto = ((abs(t[0]+self.ypos)/2), (abs(t[1]+self.xpos)/2))
                            break 
                self.area_found = False
            if self.agent_map[self.goto[0]][self.goto[1]] != 'stone': #Om goto-tupeln inneh�ller x,y koordinater d�r en sten ligger, nollst�lls listan och en ny koordinat tas fram
                goto_way = self.find_path_bf(self.agent_map, self.ypos, self.xpos, self.goto[1], self.goto[0],False)
            else:
                goto_way = []
            if len(goto_way) > 1: #goto_way-listan �r st�rre �n 1
                del goto_way[0] #Tar bort f�rsta tupeln i listan (koordinater som sk�ldpaddan redan befinner sig p�)
                return self.movement(goto_way) #Skickar med listan till funktionen movement
                
                

            else: #N�tt m�let, generera fram en ny position att g� mot
                self.area_found = True
                return 'wait'

        else: #Om listan unexplored_area �r tom har sk�ldpaddan g�tt igenom hela kartan
            print("Listan �r nu tom!")
            return 'wait'
                
                

        

    #Funktion som leder sk�ldpaddan tillbaka till n�rmsta vattenk�lla
    def water_source(self,water_level,ypos,xpos):

        if water_level < 50:
            if len(self.pond_list) > 0: #Kontrollerar att det finns minst en position till vattenk�lla i listan
                for s in self.pond_list:
                    dia = self.rectangleDiagonal((ypos,xpos),s) #Tar fram f�gelavst�ndet till vattenk�llan
                    if dia < self.length: #Kontrollerar vilken av alla k�llor som �r den n�rmsta r�knat fr�n sk�ldpaddans position
                        self.length = dia
                        self.ws = s
                ws_way = self.find_path_bf(self.agent_map, ypos, xpos, self.ws[1], self.ws[0],True) #Anropar bf f�r b�sta v�g till vattenk�llan
                if len(ws_way) > 1: #Om sk�ldpaddan befinner sig brevid eller l�ngre ifr�n vattenp�len �r denna sann
                    del ws_way[0] #Tar bort den f�rsta tupeln i listan. (Den position som sk�ldpaddan redan befinner sig p�, x-, y-pos)                

                    return self.movement(ws_way) #Anropar movement-funktionen med listan till vattenk�llan som anrop

                else: #Annars befinner sig sk�ldpaddan p� vattenp�len
                    return 'drink'
                

    #Funktion som best�mmer hur sk�ldpaddan skall g�, utifr�n den lista som skickas med till funktionen
    def movement(self, goto_way):
        y_course = self.ypos - goto_way[0][0] #Kontrollerar �t vilket h�ll "m�let" finns fr�n sk�ldpaddans position
        x_course = self.xpos - goto_way[0][1]
        if y_course == -1: #M�let ligger �t s�der
                if self.direction == 2: #(syd)
                        self.ypos += 1
                        return 'forward'
                elif self.direction == 1: #�st
                        self.direction = (self.direction+1)%4
                        return 'right'
                else:           #Om direction �r norr eller v�st s� skall sk�ldpaddan vrida v�nster
                        self.direction = (self.direction-1)%4
                        return 'left'

        elif y_course == 1: #M�let ligger norr ut
                if self.direction == 0: #(norr)
                        self.ypos -= 1
                        return 'forward'
                elif self.direction == 1: #�st
                        self.direction = (self.direction-1)%4
                        return 'left'
                else:           #Om direction �r syd eller v�st s� skall sk�ldpaddan vrida h�ger
                        self.direction = (self.direction+1)%4
                        return 'right'

        elif x_course == -1: #M�let ligger �ster ut
                if self.direction == 1: #(�st)
                        self.xpos += 1
                        return 'forward'
                elif self.direction == 2: #syd
                        self.direction = (self.direction-1)%4
                        return 'left'
                else:           #Om direction �r norr eller v�st s� skall sk�ldpaddan vrida h�ger
                        self.direction = (self.direction+1)%4
                        return 'right'

        elif x_course == 1: #M�let ligger v�ster ut
                        
                if self.direction == 3: #(v�st)
                        self.xpos -= 1
                        return 'forward'
                elif self.direction == 2: #syd
                        self.direction = (self.direction+1)%4
                        return 'right'
                else:           #Om direction �r norr eller �st s� skall sk�ldpaddan vrida v�nster
                        self.direction = (self.direction-1)%4
                        return 'left'
                        
        
        
        
    def rectangleDiagonal(self,p1,p2):
         x = p2[0]-p1[0]
         y = p2[1]-p1[1]
         diagonal = sqrt(pow(x,2) + pow(y,2))
         return diagonal
        
 
            
    #Skapar kartan f�r agenten
    def update_map(self):


        if self.create_map is True: #Skapar en karta f�r agenten, alla omr�den �r ok�nda (unknown)
            self.agent_map = [ [  ((y in [0,self.map_size-1] or  x in [0,self.map_size-1]) and 'wall') or 'unknown' for x in range(self.map_size) ] for y in range(self.map_size) ]
            for i in range(1, len(self.agent_map)-1): #Skapar en lista f�r alla ok�nda omr�den
                for j in range(1, len(self.agent_map)-1):
                    if (i,j) not in self.unexplored_area:
                        self.unexplored_area.append((i,j)) 
            shuffle(self.unexplored_area) #Blandar om listan
            self.create_map = False #S�tter till false s� inte kartan skapas om



            
        
    #Skriver ut kartan n�r spelet avslutas
    def print_map(self, matrix):
        for i in range(0,len(matrix)):
            for j in range(0,len(matrix)):
                if matrix[i][j] == 'wall':                    
                    sys.stdout.write('##')
                elif matrix[i][j] == 'ground':
                    sys.stdout.write('  ')
                elif matrix[i][j] == 'stone':
                    sys.stdout.write('@ ')
                elif matrix[i][j] == 'pond':
                    sys.stdout.write('* ')
                elif matrix[i][j] == 'unknown':
                    sys.stdout.write('? ')
                elif matrix[i][j] == 'lettuce':
                    sys.stdout.write('& ')
            sys.stdout.write('\n')
        print("un- area: ", self.unexplored_area)

    def find_path_bf(self,labyrinth,startx,starty,endx,endy,water):
        stack = [ [(startx,starty)] ] #stack tilldelas startpunkterna.

        #Sålänge som stacken inte är tom, körs koden nedan.
        while stack:

            #Hämtar tillståndet som ligger överst på stacken.
            current_path = stack.pop()
            #x,y får de koordinater som finns i nuvarande tillstånd.
            x,y = current_path[-1]
            if (x,y) == (endy,endx): # Om position x,y = endx,endy har målet nåtts och vägen samt kostnaden returneras.
                return current_path
            else:

                #Kontrollerar vilka vägar som går att gå.
                if water is True: #Om sk�ldpaddan letar efter vattenk�lla anropas denna
                    next_steps = self.adjacent_passages(labyrinth,x,y)
                else: #Annars om den skall g� mot ett outforskat omr�de anropas denna
                    next_steps = self.adjacent_passages_to_explore(labyrinth,x,y)

                for s in next_steps:
                    if s not in current_path:
                    #Om s inte finns med i listan current_path, läggs den till först i stacken tillsammans med current_path.
                        stack.insert(0,current_path+[s])
                        
        return []


    def adjacent_passages(self,matrix,x,y):
            
        lista = []
        if x > len(matrix) - 1:
            return lista
            
        else:
            
            if matrix[x-1][y] != 'stone' and matrix[x-1][y] != 'wall' and matrix[x-1][y] != 'unknown':
                lista.append((x-1,y))
            if y+1 < len(matrix):
                if matrix[x+1][y] != 'stone' and matrix[x+1][y] != 'wall' and matrix[x+1][y] != 'unknown':
                    lista.append((x+1, y))
        if y > len(matrix) - 1:
            return lista

        else:
             if matrix[x][y-1] != 'stone' and matrix[x][y-1] != 'wall' and matrix[x][y-1] != 'unknown':
                 lista.append((x, y-1))
             if x+1 < len(matrix):
                 if matrix[x][y+1] != 'stone' and matrix[x][y+1] != 'wall' and matrix[x][y+1] != 'unknown':
                     lista.append((x,y+1))

        return lista

    def adjacent_passages_to_explore(self,matrix,x,y):
            
        lista = []
        if x > len(matrix) - 1:
            return lista
            
        else:
            
            if matrix[x-1][y] != 'stone' and matrix[x-1][y] != 'wall':
                lista.append((x-1,y))
            if y+1 < len(matrix):
                if matrix[x+1][y] != 'stone' and matrix[x+1][y] != 'wall':
                    lista.append((x+1, y))
        if y > len(matrix) - 1:
            return lista

        else:
             if matrix[x][y-1] != 'stone' and matrix[x][y-1] != 'wall':
                 lista.append((x, y-1))
             if x+1 < len(matrix):
                 if matrix[x][y+1] != 'stone' and matrix[x][y+1] != 'wall':
                     lista.append((x,y+1))

        return lista


        


tb = TortoiseBrain()
tf = TortoiseFrame(15,40,tb)
tf.mainloop()
tb.print_map(tb.agent_map)
print("Score:", tf.tw.score)


