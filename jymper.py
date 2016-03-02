#!/usr/bin/env python
import random
import pygame

class Renderer:
    def __init__(self, resolution, world):
        self.world = world
        self.display = pygame.display.set_mode(resolution)

    def render(self):
        #self.display.fill((0, 0, 0))
        self.display.blit(sprites.backdrop, (0, 0, 640, 480))

        self.world.active_blocks.draw(self.display)
        self.world.hurtful_things.draw(self.display)
        self.world.active_entities.draw(self.display)

        pygame.display.update()


class Sprites:
    def __init__(self):
        self.size = 8
        self.scale = 4
        self.textures = pygame.transform.scale(pygame.image.load("textures.png"),
                                               (64*self.scale, 64*self.scale))
        self.textures.set_colorkey((0, 0, 0, 255))
        self.backdrop = pygame.transform.scale(pygame.image.load("backdrop.png"),
                                               (160*self.scale, 120*self.scale))

        # slice it :D
        self.sprites = list()
        for y in range(8):
            self.sprites.append(list())
            for x in range(8):
                sprite_size = self.size * self.scale
                src_rect = (x * sprite_size,
                            y * sprite_size,
                            sprite_size,
                            sprite_size
                )
                self.sprites[-1].append(self.textures.subsurface(src_rect))

    def get(self, (x, y)):
        try:
            return self.sprites[y][x]
        except IndexError, e:
            raise ValueError("Couldn't find sprite {}, {} in {}".format(x, y, self.sprites))


class World:
    def __init__(self, level_string):
        self.active_blocks = pygame.sprite.Group() # Blocks are blocking blocks... gah
        self.hurtful_things = pygame.sprite.Group()
        self.active_entities = pygame.sprite.Group() # players later entites :D
        self.world = list() # list of lists
        self.entities = list()
        self.width = 0
        y = -1
        for row in level_string.split('\n'):
            y += 1
            x = -1
            for char in row:
                self.world.append(list())
                x += 1
                if char == 'P':
                    self.entities.append(Player(x, y))
                    self.active_entities.add(self.entities[-1])
                elif char == '#':
                    self.world[-1].append(Block(x, y))
                    self.active_blocks.add(self.world[-1][-1])
                elif char == 'F':
                    self.world[-1].append(Fire(x, y))
                    self.hurtful_things.add(self.world[-1][-1])
            if x > self.width:
                print("new x {}".format(x))
                self.width = x

        self.height = y
        print(self.width, self.height)

    def block_at(self, x, y):
        if len(self.world) -1 < y:
            return None

        if len(self.world[y]) -1 < x:
            return None

        return self.world[y][x]

    def tick(self):
        for row in self.world:
            for block in row:
                block.update()

        for entity in self.entities:
            entity.update()


class Block(pygame.sprite.Sprite):
    # Basic block
    sprite = (0, 1)
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.blocking = True
        self.hurting = False
        self.image = sprites.get(self.sprite)
        self.rect = self.image.get_rect()
        self.rect.x = x * (sprites.size * sprites.scale)
        self.rect.y = y * (sprites.size * sprites.scale)

    def update(self):
        pass

class Fire(Block):
    def __init__(self, x, y):
        self.sprites = [(0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6)]
        self.sprite = random.choice(self.sprites)
        Block.__init__(self, x, y)
        self.hurting = True
        self.blocking = False
        self.sprite_pos = self.sprites.index(self.sprite)

    def update(self):
        t = pygame.time.get_ticks()

        if t % 4 == 0:
            #self.image = sprites.get(random.choice(self.sprites))
            self.sprite_pos += 1
            if self.sprite_pos >= len(self.sprites):
                self.sprite_pos = 0
            self.sprite = self.sprites[self.sprite_pos]
            self.image = sprites.get(self.sprite)
        # Spawn framgent 5% chance

class Player(Block):
    # Later make new base called entity and handle them diffrently
    # for example these should "float", between grid points
    # def __init__(self, x, y)
    sprite = (0, 0)
    def __init__(self, x, y):
        Block.__init__(self, x, y)
        self.blocking = False
        self.change_x = 0
        self.change_y = 0
        self.max_speed = 6
        self.max_jump = 8
        self.jump_amount = 0
        self.moving = "no" # no, left, right
        self.last_direction = "right"
        self.jumping = False
        self.walk_sprites = [(0, 0), (1, 0)]
        self.jump_sprites = [(2, 0), (3, 0)]

    def jump(self):
        # move down a bit and see if there is a platform below us.
        # Move down 2 pixels because it doesn't work well if we only move down
        # 1 when working with a platform moving down.
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, world.active_blocks, False)
        self.rect.y -= 2

        # If it is ok to jump, set our speed upwards
        if len(platform_hit_list) > 0: # or self.rect.bottom >= SCREEN_HEIGHT:
            #self.change_y = -8 # 8 is a good standard
            #self.jump_amount = 4
            self.jumping = True

    def move(self, direction):
        if self.moving != direction and not self.jumping:
            self.change_x *= 0.25
        self.moving = direction # 'left', right
        self.last_direction = direction

    def halt(self, kind):
        """Stop adding speed to kind (move, jump)"""
        if kind == 'move' and not self.jumping:
            self.moving = 'no'
            self.image = sprites.get(self.walk_sprites[0])
        else:
            self.jumping = False
            self.jump_amount = 0

    def update(self):
        """ Move the player. """
        # Gravity
        self.calc_grav()

        # Move left/right
        if self.moving != 'no':
            if self.moving == 'left':
                self.change_x -= 0.5
                if self.change_x < -self.max_speed:
                    self.change_x = -self.max_speed
            else:
                self.change_x += 0.5
                if self.change_x > self.max_speed:
                    self.change_x = self.max_speed

            self.rect.x += self.change_x

        # Are we colliding yet?!
        block_hit_list = pygame.sprite.spritecollide(self, world.active_blocks, False)
        for block in block_hit_list:
            if self.change_x > 0:
                self.rect.right = block.rect.left
            elif self.change_x < 0:
                self.rect.left = block.rect.right

        # Move up/down
        if self.jumping and self.jump_amount <= self.max_jump:
            self.jump_amount += 2
            self.change_y -= 2
        self.rect.y += self.change_y

        # Are we colliding yet?!
        block_hit_list = pygame.sprite.spritecollide(self, world.active_blocks, False)
        for block in block_hit_list:
            # Reset our position based on the top/bottom of the object.
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
            elif self.change_y < 0:
                self.rect.top = block.rect.bottom

            # Stop our vertical movement
            self.change_y = 0

        # update our graphics
        if self.moving == 'no':
            self.image = sprites.get(self.walk_sprites[0])
        elif self.moving in ('left', 'right') and self.change_y == 0:
            t = pygame.time.get_ticks() % 750 #1000
            if t < 250:
                self.image = sprites.get(self.walk_sprites[0])
            elif t < 500:
                self.image = sprites.get(self.walk_sprites[1])
            elif t < 750:
                self.image = sprites.get(self.jump_sprites[0])
            #else:
            #    self.image = sprites.get(self.jump_sprites[1])
        else:
            if self.change_y > 0:
                self.image = sprites.get(self.jump_sprites[1])
            else:
                self.image = sprites.get(self.jump_sprites[0])

        if self.last_direction == 'left':
            self.image = pygame.transform.flip(self.image, True, False)


    def calc_grav(self):
        """ Calculate effect of gravity. """
        if self.change_y == 0:
            self.change_y = 1
        else:
            self.change_y += .35

def main_loop(world, renderer):
    run = True
    fps_clock = pygame.time.Clock()

    while run:
        renderer.render()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Clean up and close down.
                run = False
                pygame.quit()
                break

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    print("FPS: %f" % fps_clock.get_fps())
                elif event.key == pygame.K_F5:
                    print("Reseting player position")
                    world.entities[0].rect.x = 64
                    world.entities[0].rect.y = 384
                    world.entities[0].change_x = 0
                    world.entities[0].change_y = 0

                elif event.key == pygame.K_UP:
                    world.entities[0].jump()
                elif event.key == pygame.K_LEFT:
                    world.entities[0].move("left")
                elif event.key == pygame.K_RIGHT:
                    world.entities[0].move("right")

            elif event.type == pygame.KEYUP:
                # stop move actions
                if event.key == pygame.K_UP:
                    world.entities[0].halt('jump')
                elif event.key == pygame.K_LEFT:
                    world.entities[0].halt('move')
                elif event.key == pygame.K_RIGHT:
                    world.entities[0].halt('move')

        # Do world events
        world.tick()

        # Limit FPS
        fps_clock.tick(30)

# test load
sprites = Sprites()
level = """
####            ####
##                ##
#      ####        #
#       ##         #
####           ### #
#                  #
##    ## ##        #
###                #
#      ##          #
# ##         ####  #
# ##               #
#  P  ###       # ##
###########FFF######
####################"""
world = World(level)

pygame.init()
pygame.display.set_caption("jymper")
renderer = Renderer((640, 480), world)
main_loop(world, renderer)
