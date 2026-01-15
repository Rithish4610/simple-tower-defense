import pygame, sys, math, random
pygame.init()

# ---------------- SCREEN ----------------
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defense – Level Based Limits")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("arial", 18)
BIG = pygame.font.SysFont("arial", 42)

# ---------------- COLORS ----------------
BLACK=(30,30,30); GREEN=(60,180,60); RED=(220,60,60)
BLUE=(60,60,220); YELLOW=(240,220,0); PURPLE=(150,80,200)
GRAY=(200,200,200); BROWN=(140,100,70)

# ---------------- GRID ----------------
GRID=50
def snap(x,y): return (x//GRID)*GRID,(y//GRID)*GRID

# ---------------- PATH ----------------
PATH=[(0,300),(300,300),(300,150),(650,150),(650,400),(1000,400)]
BASE_HP=100

# ---------------- LEVEL CONFIG ----------------
LEVELS={
1:{"enemies":["normal"],"count":8,"spawn":80,"tower_limit":4},
2:{"enemies":["normal","flying"],"count":10,"spawn":75,"tower_limit":5},
3:{"enemies":["normal","armored"],"count":12,"spawn":70,"tower_limit":6},
4:{"enemies":["normal","flying","armored"],"count":15,"spawn":65,"tower_limit":7},
5:{"enemies":["armored","flying"],"count":18,"spawn":60,"tower_limit":8},
}

# ---------------- ENEMY ----------------
class Enemy:
    def __init__(self,etype):
        self.path=PATH; self.i=0
        self.x,self.y=PATH[0]
        self.dead=False; self.alpha=255
        self.type=etype

        if etype=="flying":
            self.speed=3; self.health=60; self.armor=0; self.color=(180,180,255)
        elif etype=="armored":
            self.speed=1.2; self.health=180; self.armor=2; self.color=(120,120,120)
        else:
            self.speed=2; self.health=90; self.armor=0; self.color=RED

        self.max_health=self.health; self.size=28

    def move(self):
        if self.dead:
            self.alpha-=5
            return self.alpha<=0

        if self.i+1<len(self.path):
            tx,ty=self.path[self.i+1]
            dx,dy=tx-self.x,ty-self.y
            dist=math.hypot(dx,dy)
            if dist<self.speed: self.i+=1
            else:
                self.x+=self.speed*dx/dist
                self.y+=self.speed*dy/dist
        else: return True
        return False

    def draw(self):
        surf=pygame.Surface((self.size,self.size),pygame.SRCALPHA)
        pygame.draw.rect(surf,self.color,(0,0,self.size,self.size),border_radius=6)
        surf.set_alpha(self.alpha)
        screen.blit(surf,(self.x,self.y))
        pygame.draw.rect(screen,RED,(self.x,self.y-6,self.size,4))
        pygame.draw.rect(screen,GREEN,(self.x,self.y-6,self.size*(self.health/self.max_health),4))

# ---------------- BULLET ----------------
class Bullet:
    def __init__(self,x,y,target,dmg,splash=0):
        self.x,self.y=x,y; self.target=target
        self.dmg=dmg; self.splash=splash; self.speed=7

    def move(self,enemies):
        if not self.target or self.target.health<=0: return True
        dx,dy=self.target.x-self.x,self.target.y-self.y
        dist=math.hypot(dx,dy)
        if dist<self.speed:
            damage=max(1,self.dmg-self.target.armor)
            self.target.health-=damage
            if self.splash:
                for e in enemies:
                    if math.hypot(e.x-self.target.x,e.y-self.target.y)<self.splash:
                        e.health-=damage//2
            return True
        self.x+=self.speed*dx/dist; self.y+=self.speed*dy/dist
        return False

    def draw(self):
        pygame.draw.circle(screen,YELLOW,(int(self.x),int(self.y)),4)

# ---------------- TOWER ----------------
class Tower:
    def __init__(self,x,y,ttype):
        self.x,self.y=x,y; self.type=ttype
        self.level=1; self.angle=0; self.cool=0

        if ttype=="sniper":
            self.range,self.dmg,self.rate=260,8,50; self.color=PURPLE
        elif ttype=="splash":
            self.range,self.dmg,self.rate=140,3,25; self.color=YELLOW
        else:
            self.range,self.dmg,self.rate=160,2,20; self.color=BLUE

    def upgrade(self):
        self.level+=1; self.dmg+=1; self.range+=10

    def clicked(self,mx,my):
        return self.x<mx<self.x+GRID and self.y<my<self.y+GRID

    def attack(self,enemies,bullets):
        self.cool-=1
        for e in enemies:
            if e.dead: continue
            d=math.hypot(self.x-e.x,self.y-e.y)
            if d<self.range and self.cool<=0:
                self.angle=math.degrees(math.atan2(e.y-self.y,e.x-self.x))
                splash=60 if self.type=="splash" else 0
                bullets.append(Bullet(self.x+25,self.y+25,e,self.dmg,splash))
                self.cool=self.rate
                break

    def draw(self):
        base=pygame.Surface((GRID,GRID),pygame.SRCALPHA)
        pygame.draw.circle(base,self.color,(25,25),20)
        screen.blit(pygame.transform.rotate(base,-self.angle),(self.x,self.y))
        pygame.draw.circle(screen,self.color,(self.x+25,self.y+25),self.range,1)

# ---------------- GAME ----------------
def main():
    level=1; money=300; base_hp=BASE_HP
    towers=[]; bullets=[]; enemies=[]
    spawn=0; spawned=0; selected=None

    while True:
        screen.fill(GREEN)

        # grid & path
        for x in range(0,WIDTH,GRID): pygame.draw.line(screen,(220,220,220),(x,0),(x,HEIGHT))
        for y in range(0,HEIGHT,GRID): pygame.draw.line(screen,(220,220,220),(0,y),(WIDTH,y))
        pygame.draw.lines(screen,BROWN,False,PATH,40)

        for event in pygame.event.get():
            if event.type==pygame.QUIT: pygame.quit();sys.exit()

            if event.type==pygame.MOUSEBUTTONDOWN:
                mx,my=event.pos
                for t in towers:
                    if t.clicked(mx,my):
                        selected=t; break
                else:
                    if money>=120 and len(towers)<LEVELS[level]["tower_limit"]:
                        gx,gy=snap(mx,my)
                        if all(t.x!=gx or t.y!=gy for t in towers):
                            towers.append(Tower(gx,gy,random.choice(["normal","sniper","splash"])))
                            money-=120

            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_u and selected and money>=100:
                    selected.upgrade(); money-=100

        cfg=LEVELS[level]
        spawn+=1
        if spawn>cfg["spawn"] and spawned<cfg["count"]:
            enemies.append(Enemy(random.choice(cfg["enemies"])))
            spawn=0; spawned+=1

        for e in enemies[:]:
            end=e.move()
            if end and not e.dead:
                base_hp-=10; enemies.remove(e)
            elif e.health<=0:
                e.dead=True; money+=40
            elif e.alpha<=0:
                enemies.remove(e)
            e.draw()

        for t in towers:
            t.attack(enemies,bullets); t.draw()

        for b in bullets[:]:
            if b.move(enemies): bullets.remove(b)
            else: b.draw()

        # level complete
        if spawned==cfg["count"] and not enemies:
            if level<5:
                level+=1; spawned=0; money+=200
            else:
                screen.blit(BIG.render("YOU WIN!",True,BLUE),(420,260))

        # UI
        pygame.draw.rect(screen,GRAY,(0,0,WIDTH,40))
        screen.blit(FONT.render(f"Level: {level}/5",True,BLACK),(20,10))
        screen.blit(FONT.render(f"Towers: {len(towers)}/{cfg['tower_limit']}",True,BLACK),(120,10))
        screen.blit(FONT.render(f"Money: {money}",True,BLACK),(300,10))
        screen.blit(FONT.render("Click tower → U to upgrade",True,BLACK),(480,10))

        if base_hp<=0:
            screen.blit(BIG.render("GAME OVER",True,RED),(380,260))

        pygame.display.update()
        clock.tick(60)

main()
