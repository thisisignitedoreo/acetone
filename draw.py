
# font draw tool :)

import pygame as pg
import pyclip
import sys

class DrawTool:
    def __init__(self):
        pg.init()
        self.res = self.w, self.h = [500, 300]
        self.center = self.center_width, self.center_height = self.res[0] // 2, self.res[1] // 2
        self.fps = 60
        self.screen = pg.display.set_mode(self.res)
        self.clock = pg.time.Clock()
        self.title = "FontDrawTool; %s fps"

        self.res = []
        self.queue = None

    def draw(self):
        self.screen.fill(pg.color.Color("white"))

        a = self.h
        aw = a
        ah = a

        for y in range(11):
            pg.draw.line(self.screen, pg.color.Color("gray"), (0, y * (ah/10)), (aw, y * (ah/10)))
        for x in range(11):
            pg.draw.line(self.screen, pg.color.Color("gray"), (x * (aw/10), 0), (x * (aw/10), ah))
        
        for i in self.res:
            if i is None: continue
            x, y = i
            pg.draw.circle(self.screen, pg.color.Color("black"), (x*aw, y*ah), 10)

        for k, i in enumerate(self.res[:-1]):
            if self.res[k+1] is None: continue
            if i is None: continue
            x1, y1 = i
            x2, y2 = self.res[k+1]
            pg.draw.line(self.screen, pg.color.Color("black"), (x1*aw, y1*ah), (x2*aw, y2*ah), 10)

        if self.queue:
            first = True
            for x, y in self.queue[::-1]:
                pg.draw.circle(self.screen, pg.color.Color("red"), (x*aw, y*ah), 20 if first else 10)
                first = False
            for k, i in enumerate(self.queue[:-1]):
                x1, y1 = i
                x2, y2 = self.queue[k+1]
                pg.draw.line(self.screen, pg.color.Color("red"), (x1*aw, y1*ah), (x2*aw, y2*ah), 10)

        font = pg.font.Font(None, 16)

        text_repr = self.to_text()
        text_repr = text_repr.split("\n")
        y = 0
        for i in text_repr:
            text = font.render(i, 1, pg.color.Color("black"))
            self.screen.blit(text, (320, 0 + y))
            y += font.get_height()

    def to_text(self):
        text = ""
        for i in self.res:
            if i is None: text += "--\n"
            else: text += f"{i[0]} {i[1]}\n"
        
        return text

    def click_handler(self, ev):
        if ev.button != 1: return
        if ev.pos[0] <= 300:
            x, y = ev.pos
            x, y = round(x/30), round(y/30)
            x, y = x/10, y/10
            if self.queue is None:
                self.queue = [(x, y)]
            else:
                if self.queue == [] or self.queue[-1] != (x, y):
                    self.queue.append((x, y))
        else:
            text_repr = self.to_text()
            pyclip.copy(text_repr)

    def key_handler(self, ev):
        if ev.key == pg.K_RETURN:
            self.res += self.queue
            self.res.append(None)
            self.queue = None
        if ev.key == pg.K_BACKSPACE:
            if self.queue:
                self.queue.pop()
            elif self.res:
                self.res.pop()
        if ev.key == pg.K_RIGHTBRACKET:
            if self.res:
                self.res.pop()
        if ev.key == pg.K_LEFTBRACKET:
            if self.res:
                while self.res and self.res[-1] is not None:
                    self.res.pop()
        if ev.key == pg.K_SPACE:
            self.res = []
            self.queue = []
        if ev.key == pg.K_RIGHT:
            for k, i in enumerate(self.res):
                if i is None: continue
                self.res[k] = (round(i[0] + 0.1, 1) % 1.1, i[1])
        if ev.key == pg.K_LEFT:
            for k, i in enumerate(self.res):
                if i is None: continue
                self.res[k] = (round(i[0] - 0.1, 1) % 1.1, i[1])
        if ev.key == pg.K_UP:
            for k, i in enumerate(self.res):
                if i is None: continue
                self.res[k] = (i[0], round(i[1] - 0.1, 1) % 1.1)
        if ev.key == pg.K_DOWN:
            for k, i in enumerate(self.res):
                if i is None: continue
                self.res[k] = (i[0], round(i[1] + 0.1, 1) % 1.1)

    def handle_event(self, ev):
        if ev.type == pg.QUIT: sys.exit()
        if ev.type == pg.MOUSEBUTTONDOWN: self.click_handler(ev)
        if ev.type == pg.KEYDOWN: self.key_handler(ev)

    def run(self):
        while True:
            self.draw()
            [self.handle_event(ev) for ev in pg.event.get()]
            pg.display.set_caption(self.title % str(round(self.clock.get_fps(), 2)))
            pg.display.flip()
            self.clock.tick(self.fps)

if __name__ == "__main__":
    tool = DrawTool()
    tool.run()
