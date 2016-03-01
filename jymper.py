#!/usr/bin/env python
import pygame

class Renderer:
    def __init__(self, resolution, world):
        self.display = pygame.display.set_mode(resolution)
        self.resolution = resolution
        self.sprite_size = 8
        self.sprite_scale = 4
        #self.sprites = pygame.image.load("textures.png")
        self.sprites = pygame.transform.scale(pygame.image.load("textures.png"),
                                              (64*self.sprite_scale, 64*self.sprite_scale))
        self.sprites.set_colorkey((0, 0, 0, 255))
        self.world = world

    def draw_entity(self, entity):
        sprite_size = self.sprite_size * self.sprite_scale
        src_rect = (entity.current_sprite[0] * sprite_size,
                    entity.current_sprite[1] * sprite_size,
                    sprite_size,
                    sprite_size
        )

        # calculate placement position (FIXME: Find a better one...)
        ppos = ((entity.pos[0] + entity.mod_pos[0]) * sprite_size,
                (entity.pos[1] + entity.mod_pos[1]) * sprite_size)

        # place
        self.display.blit(self.sprites, ppos, src_rect)

    def render(self):
        """Draws the gaming area to the screen surface"""
        sprite_size = self.sprite_size * self.sprite_scale
        for row in self.world.world:
            for block in row:
                src_rect = (block.current_sprite[0] * sprite_size,
                            block.current_sprite[1] * sprite_size,
                            sprite_size,
                            sprite_size
                )

                # calculate placement position (FIXME: Find a better one...)
                ppos = (block.pos[0] * sprite_size,
                        block.pos[1] * sprite_size)

                # place
                self.display.blit(self.sprites, ppos, src_rect)

        for entity in self.world.entities:
            self.draw_entity(entity)

class StupidRenderer:
    def __init__(self, resolution, world):
        self.world = world
        self.display = pygame.display.set_mode(resolution)

    def render(self):
        self.display.fill((0, 0, 0))
        self.world.active_blocks.update()
        self.world.active_entities.update()

        self.world.active_blocks.draw(self.display)
        self.world.active_entities.draw(self.display)

        pygame.display.update()


class Sprites:
    def __init__(self):
        self.size = 8
        self.scale = 4
        #self.sprites = pygame.image.load("textures.png")
        self.textures = pygame.transform.scale(pygame.image.load("textures.png"),
                                               (64*self.scale, 64*self.scale))
        self.textures.set_colorkey((0, 0, 0, 255))

        # slice it :D
        self.sprites = list()
        for x in range(8):
            for y in range(8):
                self.sprites.append(list())
                sprite_size = self.size * self.scale
                src_rect = (x * sprite_size,
                            y * sprite_size,
                            sprite_size,
                            sprite_size
                )
                self.sprites[-1].append(self.textures.subsurface(src_rect))

    def get(self, (x, y)):
        #sprite_size = self.sprite_size * self.sprite_scale
        #src_rect = (x * sprite_size,
        #            y * sprite_size,
        #            sprite_size,
        #            sprite_size
        #)
        # TODO: move this into a precutter..
        #return self.sprites.subsurface(src_rect)
        return self.sprites[y][x]

class World:
    def __init__(self, level_string):
        self.active_blocks = pygame.sprite.Group() # Blocks are blocking blocks... gah
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
        self.kind = "block"
        self.blocking = True
        self.hurting = False
        #self.current_sprite = (0, 1)
        self.image = sprites.get(self.sprite)
        self.rect = self.image.get_rect()
        self.rect.x = x * (sprites.size * sprites.scale)
        self.rect.y = y * (sprites.size * sprites.scale)

    def update(self):
        pass

class Player(Block):
    # Later make new base called entity and handle them diffrently
    # for example these should "float", between grid points
    # def __init__(self, x, y)
    sprite = (0, 0)
    def __init__(self, x, y):
        Block.__init__(self, x, y)
        kind = "player"
        self.blocking = False
        self.change_x = 0
        self.change_y = 0

    def jump(self):
        # move down a bit and see if there is a platform below us.
        # Move down 2 pixels because it doesn't work well if we only move down
        # 1 when working with a platform moving down.
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, world.active_blocks, False)
        self.rect.y -= 2
 
        # If it is ok to jump, set our speed upwards
        if len(platform_hit_list) > 0: # or self.rect.bottom >= SCREEN_HEIGHT:
            self.change_y = -10

    def move(self, direction):
        if direction == 'left':
            self.change_x -= 1
        elif direction == 'right':
            self.change_x += 1

    def stop(self):
        self.change_x = 0

    def update(self):
        """ Move the player. """
        # Gravity
        self.calc_grav()

        # Move left/right
        self.rect.x += self.change_x

        # Are we colliding yet?!
        block_hit_list = pygame.sprite.spritecollide(self, world.active_blocks, False)
        for block in block_hit_list:
            if self.change_x > 0:
                self.rect.right = block.rect.left
            elif self.change_x < 0:
                self.rect.left = block.rect.right

        # Move up/down
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

    def calc_grav(self):
        """ Calculate effect of gravity. """
        if self.change_y == 0:
            self.change_y = 1
        else:
            self.change_y += .35

        # See if we are on the ground.
        #if self.rect.y >= SCREEN_HEIGHT - self.rect.height and self.change_y >= 0:
        #    self.change_y = 0
        #    self.rect.y = SCREEN_HEIGHT - self.rect.height


def shitty_main_loop(world, renderer):
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
                    print( "FPS: %f" % fps_clock.get_fps() )

                if event.key == pygame.K_UP:
                    world.entities[0].jump()
                elif event.key == pygame.K_LEFT:
                    world.entities[0].move("left")
                elif event.key == pygame.K_RIGHT:
                    world.entities[0].move("right")

        # Do world events
        world.tick()

        # Limit FPS
        fps_clock.tick(24)

# test load
sprites = Sprites()
level = """


###           ###

     ## ##
##
      ##
 ##         ####
 ##
 P   ###  #
######## ###  #####"""

world = World(level)

pygame.init()
pygame.display.set_caption("jymper")
#renderer = Renderer((640,480), world)
renderer = StupidRenderer((640, 480), world)
shitty_main_loop(world, renderer)
